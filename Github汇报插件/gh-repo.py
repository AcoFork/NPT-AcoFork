import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger
from datetime import datetime, timezone, timedelta

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/TeamFlos/phira",
    "https://api.github.com/repos/AcoFork/NPT-AcoFork",
]
GROUP_IDS = [12345678]  # 你的QQ群号列表
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler
latest_trees = {}
latest_branches = {}

async def check_github_repo(url):
    global latest_trees, latest_branches
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            repo_name = url.split("/")[-2] + "/" + url.split("/")[-1]
            
            # 检查分支变动
            branches_url = f"{url}/branches"
            response = await client.get(branches_url, headers=headers)
            response.raise_for_status()
            current_branches = {branch['name']: branch['commit']['sha'] for branch in response.json()}
            
            if repo_name not in latest_branches:
                latest_branches[repo_name] = current_branches
                latest_trees[repo_name] = {}
                return  # 首次检查，不发送消息
            
            changes = []
            for branch, commit_sha in current_branches.items():
                if branch not in latest_branches[repo_name]:
                    changes.append(("新建分支", branch))
                elif commit_sha != latest_branches[repo_name][branch]:
                    changes.append(("更新", branch))
                    await check_branch_update(client, repo_name, branch, latest_branches[repo_name][branch], commit_sha, changes)
            
            for branch in set(latest_branches[repo_name].keys()) - set(current_branches.keys()):
                changes.append(("删除分支", branch))
            
            if changes:
                await report_changes(client, repo_name, changes)
            
            latest_branches[repo_name] = current_branches
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误：{e}")
        except Exception as e:
            logger.error(f"发生错误：{e}")

async def check_branch_update(client, repo_name, branch, old_commit, new_commit, changes):
    compare_url = f"https://api.github.com/repos/{repo_name}/compare/{old_commit}...{new_commit}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = await client.get(compare_url, headers=headers)
    response.raise_for_status()
    compare_data = response.json()
    
    if compare_data['merge_base_commit']['sha'] == old_commit:
        changes.append(("推送", branch))
    else:
        changes.append(("合并", branch))
    
    # 检查文件变动
    modified_files = [file['filename'] for file in compare_data['files']]
    if modified_files:
        changes.append(("文件变动", branch, modified_files))

async def report_changes(client, repo_name, changes):
    commit_info = await get_latest_commit_info(client, repo_name, changes[0][1])
    
    modified_files = []
    actions = set()
    branches = set()
    for change in changes:
        if change[0] == "文件变动":
            modified_files.extend(change[2])
        actions.add(change[0])
        branches.add(change[1])
    
    action = "/".join(actions)
    branch = ", ".join(branches)
    
    msg = f"仓库 {repo_name} 文件发生变动：\n"
    msg += "\n".join(modified_files[:10])
    if len(modified_files) > 10:
        msg += f"\n...等共 {len(modified_files)} 个文件"
    
    msg += f"\n\n行为：{action}"
    msg += f"\n执行者：{commit_info['executor']}"
    msg += f"\n执行时间：{commit_info['time']}"
    msg += f"\n分支：{branch}"
    msg += f"\n提交摘要：{commit_info['summary']}"
    msg += f"\n仓库链接：https://github.com/{repo_name}"
    
    await send_group_message(msg)

async def get_latest_commit_info(client, repo_name, branch):
    commits_url = f"https://api.github.com/repos/{repo_name}/commits?sha={branch}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = await client.get(commits_url, headers=headers)
        response.raise_for_status()
        commits_data = response.json()
        if commits_data:
            latest_commit = commits_data[0]
            commit_message = latest_commit["commit"]["message"]
            executor = latest_commit["commit"]["author"]["name"]
            commit_time = datetime.strptime(latest_commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            commit_time = commit_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
            formatted_time = commit_time.strftime("%Y-%m-%d %H:%M:%S")
            return {
                "summary": commit_message,
                "executor": executor,
                "time": formatted_time
            }
        return {
            "summary": "无法获取提交信息",
            "executor": "未知执行者",
            "time": "未知时间"
        }
    except Exception as e:
        logger.error(f"获取提交信息时出错：{e}")
        return {
            "summary": "获取提交信息时出错",
            "executor": "未知执行者",
            "time": "未知时间"
        }

async def send_group_message(msg):
    bot = get_bot()
    for group_id in GROUP_IDS:
        await bot.send_group_msg(group_id=group_id, message=Message(msg))

@scheduler.scheduled_job("interval", seconds=CHECK_INTERVAL)
async def scheduled_check():
    for url in GITHUB_API_URLS:
        await check_github_repo(url)

def get_bot() -> Bot:
    import nonebot
    for b in nonebot.get_bots().values():
        return b
    raise RuntimeError("未找到Bot实例")