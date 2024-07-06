import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/TeamFlos/phira/git/trees/main?recursive=1",
    "https://api.github.com/repos/AcoFork/NPT-AcoFork/git/trees/main?recursive=1",
]
GROUP_ID = 12345678  # 你的QQ群号
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

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

            if repo_name not in latest_trees:
                latest_trees[repo_name] = current_tree
                return

            previous_tree = latest_trees[repo_name]
            latest_trees[repo_name] = current_tree

            modified_files = [path for path in current_tree if path not in previous_tree or current_tree[path] != previous_tree[path]]

            if modified_files:
                msg = f"仓库 {repo_name} 有文件发生变动：\n" + "\n".join(modified_files)
                bot = get_bot()
                await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

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
    raise RuntimeError("Bot instance not found")

# 模拟发送文件变动通知的函数
async def simulate_send_notification():
    repo_name = "TeamFlos/phira"
    modified_files = [
        "src/main.py",
        "src/utils/helper.py",
        "README.md"
    ]
    msg = f"仓库 {repo_name} 有文件发生变动：\n" + "\n".join(modified_files)
    bot = get_bot()
    await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))