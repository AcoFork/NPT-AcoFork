import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 配置部分
GITHUB_API_URLS = [
    "https://api.github.com/repos/simple/demo/releases/latest",
    "https://api.github.com/repos/simple/demo/releases/latest",

]
GROUP_ID = 12345678  # 你的QQ群号
CHECK_INTERVAL = 60  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"  # 你的GitHub个人访问令牌

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
            release = response.json()
            release_id = release["id"]
            release_name = release["name"]
            release_url = release["html_url"]
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
