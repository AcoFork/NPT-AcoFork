import logging
import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 禁用 httpx 日志
logging.getLogger("httpx").setLevel(logging.WARNING)

GITHUB_API_URLS = [
    {"url": "https://api.github.com/repos/TeamFlos/phira/releases", "repo_name": "TeamFlos/phira"},
    {"url": "https://api.github.com/repos/AcoFork/NPT-AcoFork/releases", "repo_name": "AcoFork/NPT-AcoFork"}
]
GROUP_ID = 123456789
CHECK_INTERVAL = 5
GITHUB_TOKEN = "ghp_122121212121"

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler
repo_info = {}

def get_bot() -> Bot:
    bots = list(get_driver().bots.values())
    if not bots:
        raise RuntimeError("No bot connected")
    return bots[0]

async def process_releases(repo_key, current_releases):
    if repo_key not in repo_info:
        repo_info[repo_key] = current_releases
        return

    added = [r for r in current_releases["releases"] if r not in repo_info[repo_key]["releases"]]
    removed = [r for r in repo_info[repo_key]["releases"] if r not in current_releases["releases"]]

    repo_info[repo_key] = current_releases

    bot = get_bot()
    for release in added:
        msg = f"仓库 {repo_key} 发现了新的 Release: {release['name']}\n{release['url']}"
        await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

    for release in removed:
        msg = f"仓库 {repo_key} 的 Release 已被删除: {release['name']}"
        await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

async def check_github_releases(url, repo_key):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            releases = response.json()

            current_releases = {
                "releases": [{"name": r["name"], "url": r["html_url"]} for r in releases if not r["prerelease"]],
                "pre-releases": [{"name": r["name"], "url": r["html_url"]} for r in releases if r["prerelease"]]
            }

            await process_releases(repo_key, current_releases)
            return current_releases

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred for {repo_key}: {e}")
        except Exception as e:
            logger.error(f"An error occurred for {repo_key}: {e}")
    return None

@scheduler.scheduled_job("interval", seconds=CHECK_INTERVAL)
async def scheduled_check():
    for config in GITHUB_API_URLS:
        await check_github_releases(config["url"], config["repo_name"])

async def startup_report(bot: Bot):
    return
    #report = "仓库 Release 报告:\n"
    #for config in GITHUB_API_URLS:
        #releases = await check_github_releases(config["url"], config["repo_name"])
        #if releases:
        #    report += f"{config['repo_name']}: {len(releases['releases'])} 个 Release, {len(releases['pre-releases'])} 个 Pre-release\n"
    #    else:
    #        report += f"{config['repo_name']}: 获取失败\n"
   #await bot.send_group_msg(group_id=GROUP_ID, message=Message(report))

@driver.on_bot_connect
async def _(bot: Bot):
    await startup_report(bot)
