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
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler
latest_branches = {}

async def check_github_repo(url):
    global latest_branches
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
                return  # 首次检查，不发送消息
            
            main_action = None
            affected_branch = None
            modified_files = []
            executor = None
            
            for branch in set(latest_branches[repo_name].keys()) - set(current_branches.keys()):
                if main_action is None:
                    main_action = "删除分支"
                    affected_branch = branch
                    executor = await get_branch_deletion_info(client, repo_name, branch)
            
            if main_action != "删除分支":
                for branch, commit_sha in current_branches.items():
                    if branch not in latest_branches[repo_name]:
                        main_action = "新建分支"
                        affected_branch = branch
                    elif commit_sha != latest_branches[repo_name][branch]:
                        action, files, commit_executor = await check_branch_update(client, repo_name, branch, latest_branches[repo_name][branch], commit_sha)
                        if action == "合并" and main_action != "新建分支":
                            main_action = "合并"
                            affected_branch = branch
                            executor = commit_executor
                        elif action in ["提交", "回滚提交"] and main_action not in ["新建分支", "合并"]:
                            main_action = action
                            affected_branch = branch
                            executor = commit_executor
                        modified_files.extend(files)
            
            if main_action:
                await report_changes(client, repo_name, main_action, affected_branch, modified_files, executor)
            
            latest_branches[repo_name] = current_branches
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误：{e}")
        except Exception as e:
            logger.error(f"发生错误：{e}")

async def check_branch_update(client, repo_name, branch, old_commit, new_commit):
    compare_url = f"https://api.github.com/repos/{repo_name}/compare/{old_commit}...{new_commit}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = await client.get(compare_url, headers=headers)
    response.raise_for_status()
    compare_data = response.json()
    
    if compare_data['merge_base_commit']['sha'] == old_commit:
        action = "提交"
        commit_message = compare_data['commits'][-1]['commit']['message']
        if commit_message.lower().startswith("revert"):
            action = "回滚提交"
    else:
        action = "合并"
    
    modified_files = [file['filename'] for file in compare_data['files']]
    executor = compare_data['commits'][-1]['commit']['author']['name']
    return action, modified_files, executor

async def get_branch_deletion_info(client, repo_name, branch):
    events_url = f"https://api.github.com/repos/{repo_name}/events"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = await client.get(events_url, headers=headers)
    response.raise_for_status()
    events = response.json()
    
    for event in events:
        if event['type'] == 'DeleteEvent' and event['payload']['ref_type'] == 'branch' and event['payload']['ref'] == branch:
            return event['actor']['login']
    
    return "未知执行者"

async def report_changes(client, repo_name, action, branch, modified_files, executor):
    if action != "删除分支":
        commit_info = await get_latest_commit_info(client, repo_name, branch)
        executor = commit_info['executor']
        time = commit_info['time']
        summary = commit_info['summary']
    else:
        time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        summary = "分支被删除"
    
    msg = f"仓库 {repo_name} 文件发生变动：\n"
    if modified_files:
        msg += "\n".join(modified_files[:10])
        if len(modified_files) > 10:
            msg += f"\n...等共 {len(modified_files)} 个文件"
    else:
        msg += "无文件变动"
    
    msg += f"\n\n行为：{action}"
    msg += f"\n执行者：{executor}"
    msg += f"\n执行时间：{time}"
    msg += f"\n分支：{branch}"
    msg += f"\n提交摘要：{summary}"
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