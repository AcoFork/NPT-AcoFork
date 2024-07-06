import httpx
from nonebot import require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger

# 配置部分
GITHUB_API_URLS = [
    {
        "url": "https://api.github.com/repos/TeamFlos/phira/releases",
        "repo_name": "TeamFlos/phira"
    },
    {
        "url": "https://api.github.com/repos/AcoFork/NPT-AcoFork/releases",
        "repo_name": "AcoFork/NPT-AcoFork"
    }
]
GROUP_ID = 12345678  # 你的QQ群号
CHECK_INTERVAL = 5  # 检查间隔时间（秒）
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler

repo_info = {}

async def check_github_releases(url, repo_name):
    global repo_info
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            releases = response.json()
            current_releases = {
                "releases": [],
                "pre-releases": []
            }

            for release in releases:
                if release["prerelease"]:
                    current_releases["pre-releases"].append({
                        "name": release["name"],
                        "url": release["html_url"]
                    })
                else:
                    current_releases["releases"].append({
                        "name": release["name"],
                        "url": release["html_url"]
                    })

            if repo_name not in repo_info:  # 第一次轮询
                repo_info[repo_name] = current_releases
                total_releases = len(repo_info[repo_name]["releases"])
                total_prereleases = len(repo_info[repo_name]["pre-releases"])
                latest_release = repo_info[repo_name]["releases"][0]["name"]
                latest_release_url = repo_info[repo_name]["releases"][0]["url"]
                msg = (
                    f"仓库 {repo_name} 现有 {total_releases} 个 Release 和 {total_prereleases} 个 Pre-Release。\n"
                    f"最新的 Release 版本: {latest_release}\n"
                    f"[Release链接]({latest_release_url})"
                )
                bot = get_bot()
                await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))
                return

            # 后续轮询处理
            added_releases = []
            removed_releases = []

            for release in current_releases["releases"]:
                if release not in repo_info[repo_name]["releases"]:
                    added_releases.append(release)

            for release in repo_info[repo_name]["releases"]:
                if release not in current_releases["releases"]:
                    removed_releases.append(release)

            # 更新 repo_info
            repo_info[repo_name] = current_releases

            # 发送新增和删除的 release 消息
            for release in added_releases:
                msg = f"仓库 {repo_name} 发现了新的 Release: {release['name']}\n{release['url']}"
                bot = get_bot()
                await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

            for release in removed_releases:
                msg = f"仓库 {repo_name} 的 Release 已删除: {release['name']}"
                bot = get_bot()
                await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

# 使用APScheduler插件来实现定时任务
@scheduler.scheduled_job("interval", seconds=CHECK_INTERVAL)
async def scheduled_check():
    for config in GITHUB_API_URLS:
        await check_github_releases(config["url"], config["repo_name"])

# 获取bot实例的函数
def get_bot() -> Bot:
    import nonebot
    for b in nonebot.get_bots().values():
        return b
    raise RuntimeError("Bot instance not found")
