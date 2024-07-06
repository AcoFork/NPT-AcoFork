import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger
from datetime import datetime

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/TeamFlos/phira/releases",
    "https://api.github.com/repos/AcoFork/NPT-AcoFork/releases",
]
GROUP_ID = 12345678  # 你的QQ群号
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler

latest_release_ids = {}

async def check_github_release(url):
    global latest_release_ids
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            releases = response.json()
            
            if not releases:
                return

            # 找到最新的 release
            latest_release = max(releases, key=lambda r: datetime.strptime(r["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
            release_id = latest_release["id"]
            release_name = latest_release["name"]
            release_url = latest_release["html_url"]
            repo_name = response.url.path.split('/')[2] + '/' + response.url.path.split('/')[3]

            if repo_name not in latest_release_ids:
                latest_release_ids[repo_name] = release_id
                return

            if release_id != latest_release_ids[repo_name]:
                latest_release_ids[repo_name] = release_id
                msg = f"仓库 {repo_name} 发布了新的 release: {release_name}\n{release_url}"
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
        await check_github_release(url)

# 获取bot实例的函数
def get_bot() -> Bot:
    import nonebot
    for b in nonebot.get_bots().values():
        return b
    raise RuntimeError("Bot instance not found")
