import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/TeamFlos/phira",
    "https://api.github.com/repos/AcoFork/NPT-AcoFork",
]
GROUP_IDS = [12345678]  # 你的QQ群号列表
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

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
            else:
                previous_branches = latest_branches[repo_name]
                latest_branches[repo_name] = current_branches
                
                new_branches = set(current_branches.keys()) - set(previous_branches.keys())
                deleted_branches = set(previous_branches.keys()) - set(current_branches.keys())
                
                if new_branches:
                    await report_branch_changes(repo_name, new_branches, "新建")
                if deleted_branches:
                    await report_branch_changes(repo_name, deleted_branches, "删除")
                
                # 检查每个分支的更新和文件变动
                for branch, commit_sha in current_branches.items():
                    if branch in previous_branches and commit_sha != previous_branches[branch]:
                        await check_branch_update(client, repo_name, branch, previous_branches[branch], commit_sha)
                    await check_branch_file_changes(client, repo_name, branch)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误：{e}")
        except Exception as e:
            logger.error(f"发生错误：{e}")

async def check_branch_file_changes(client, repo_name, branch):
    tree_url = f"https://api.github.com/repos/{repo_name}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = await client.get(tree_url, headers=headers)
    response.raise_for_status()
    tree_data = response.json()
    current_tree = {item['path']: item['sha'] for item in tree_data['tree']}
    
    if branch not in latest_trees.get(repo_name, {}):
        latest_trees[repo_name][branch] = current_tree
    else:
        previous_tree = latest_trees[repo_name][branch]
        latest_trees[repo_name][branch] = current_tree
        modified_files = [path for path in current_tree if path not in previous_tree or current_tree[path] != previous_tree[path]]
        if modified_files:
            await report_file_changes(client, repo_name, branch, modified_files)

async def report_file_changes(client, repo_name, branch, modified_files):
    commit_summary, executor = await get_latest_commit_info(client, repo_name, branch)
    repo_url = f"https://github.com/{repo_name}"
    msg = (
        f"仓库 {repo_name} 的 {branch} 分支有文件发生变动：\n" +
        "\n".join(modified_files[:10])  # 限制显示的文件数量
    )
    if len(modified_files) > 10:
        msg += f"\n...等共 {len(modified_files)} 个文件"
    msg += (
        f"\n\n最近一次提交摘要：\n{commit_summary}" +
        f"\n\n执行者：{executor}" +
        f"\n\n仓库链接：{repo_url}"
    )
    await send_group_message(msg)

async def report_branch_changes(repo_name, branches, action):
    msg = f"仓库 {repo_name} 有分支{action}：\n" + "\n".join(branches)
    await send_group_message(msg)

async def check_branch_update(client, repo_name, branch, old_commit, new_commit):
    compare_url = f"https://api.github.com/repos/{repo_name}/compare/{old_commit}...{new_commit}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = await client.get(compare_url, headers=headers)
    response.raise_for_status()
    compare_data = response.json()
    
    if compare_data['merge_base_commit']['sha'] == old_commit:
        # This is a fast-forward update (push)
        commit_summary, executor = await get_latest_commit_info(client, repo_name, branch)
        msg = (
            f"仓库 {repo_name} 的 {branch} 分支收到新的推送：\n" +
            f"提交摘要：{commit_summary}\n" +
            f"执行者：{executor}"
        )
    else:
        # This is a merge
        base_branch = compare_data['base_commit']['commit']['message'].split('\n')[0]
        head_branch = compare_data['head_commit']['commit']['message'].split('\n')[0]
        msg = f"仓库 {repo_name} 发生分支合并：\n{head_branch} 合并到 {base_branch}"
    
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
            return commit_message, executor
        return "无法获取提交信息", "未知执行者"
    except Exception as e:
        logger.error(f"获取提交信息时出错：{e}")
        return "获取提交信息时出错", "未知执行者"

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