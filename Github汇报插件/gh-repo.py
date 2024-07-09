import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/TeamFlos/phira/git/trees/main?recursive=1",
    "https://api.github.com/repos/AcoFork/NPT-AcoFork/git/trees/main?recursive=1",
]
GROUP_IDS = [12345678, 12345678]  # 你的QQ群号列表
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler
latest_trees = {}

async def check_github_repo_files(url):
    global latest_trees
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            tree_data = response.json()
            current_tree = {item['path']: item['sha'] for item in tree_data['tree']}
            repo_name = response.url.path.split('/')[2] + '/' + response.url.path.split('/')[3]
            repo_url = f"https://github.com/{repo_name}"
            if repo_name not in latest_trees:
                latest_trees[repo_name] = current_tree
                return
            previous_tree = latest_trees[repo_name]
            latest_trees[repo_name] = current_tree
            modified_files = [path for path in current_tree if path not in previous_tree or current_tree[path] != previous_tree[path]]
            if modified_files:
                commit_summary = await get_latest_commit_summary(client, repo_name)
                msg = (
                    f"仓库 {repo_name} 有文件发生变动：\n" + 
                    "\n".join(modified_files) + 
                    f"\n\n最近一次提交摘要：\n{commit_summary}" +
                    f"\n\n仓库链接：{repo_url}"
                )
                bot = get_bot()
                for group_id in GROUP_IDS:
                    await bot.send_group_msg(group_id=group_id, message=Message(msg))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误：{e}")
        except Exception as e:
            logger.error(f"发生错误：{e}")

async def get_latest_commit_summary(client, repo_name):
    commits_url = f"https://api.github.com/repos/{repo_name}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = await client.get(commits_url, headers=headers)
        response.raise_for_status()
        commits_data = response.json()
        if commits_data:
            latest_commit = commits_data[0]
            commit_message = latest_commit["commit"]["message"]
            return commit_message
        return "无法获取提交信息"
    except httpx.HTTPStatusError as e:
        #logger.error(f"HTTP错误：{e}")
        return "获取提交信息时出错"
    except Exception as e:
        #logger.error(f"发生错误：{e}")
        return "获取提交信息时出错"

# 使用APScheduler插件来实现定时任务
@scheduler.scheduled_job("interval", seconds=CHECK_INTERVAL)
async def scheduled_check():
    for url in GITHUB_API_URLS:
        await check_github_repo_files(url)

# 获取bot实例的函数
def get_bot() -> Bot:
    import nonebot
    for b in nonebot.get_bots().values():
        return b
    raise RuntimeError("未找到Bot实例")

# 模拟发送文件变动通知的函数
async def simulate_send_notification():
    repo_name = "TeamFlos/phira"
    repo_url = f"https://github.com/{repo_name}"
    modified_files = [
        "src/main.py",
        "src/utils/helper.py",
        "README.md"
    ]
    commit_summary = "模拟提交摘要"
    msg = (
        f"仓库 {repo_name} 有文件发生变动：\n" + 
        "\n".join(modified_files) + 
        f"\n\n最近一次提交摘要：\n{commit_summary}" +
        f"\n\n仓库链接：{repo_url}"
    )
    bot = get_bot()
    for group_id in GROUP_IDS:
        await bot.send_group_msg(group_id=group_id, message=Message(msg))
