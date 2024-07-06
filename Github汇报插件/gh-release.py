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
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXX"  # 你的GitHub个人访问令牌

driver = get_driver()
scheduler = require("nonebot_plugin_apscheduler").scheduler

repo_info = {}

# 获取bot实例的函数
def get_bot() -> Bot:
    import nonebot
    for b in nonebot.get_bots().values():
        return b
    raise RuntimeError("Bot instance not found")

async def check_github_releases(url, repo_key):
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

            if repo_key in repo_info:  # 后续轮询处理
                added_releases = []
                removed_releases = []

                for release in current_releases["releases"]:
                    if release not in repo_info[repo_key]["releases"]:
                        added_releases.append(release)

                for release in repo_info[repo_key]["releases"]:
                    if release not in current_releases["releases"]:
                        removed_releases.append(release)

                # 更新 repo_info
                repo_info[repo_key] = current_releases

                # 发送新增和删除的 release 消息
                bot = get_bot()
                for release in added_releases:
                    msg = f"仓库 {repo_key} 发现了新的 Release: {release['name']}\n{release['url']}"
                    await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

                for release in removed_releases:
                    msg = f"仓库 {repo_key} 的 Release 已被删除: {release['name']}"
                    await bot.send_group_msg(group_id=GROUP_ID, message=Message(msg))

            else:  # 第一次轮询
                repo_info[repo_key] = current_releases
                total_releases = len(repo_info[repo_key]["releases"])
                total_prereleases = len(repo_info[repo_key]["pre-releases"])
                latest_release = repo_info[repo_key]["releases"][0]["name"]
                latest_release_url = repo_info[repo_key]["releases"][0]["url"]

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

# 使用APScheduler插件来实现定时任务
@scheduler.scheduled_job("interval", seconds=CHECK_INTERVAL)
async def scheduled_check():
    for config in GITHUB_API_URLS:
        await check_github_releases(config["url"], config["repo_name"])

