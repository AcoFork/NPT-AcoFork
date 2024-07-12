import os
import base64
import logging
import asyncio
import subprocess
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 黑名单前缀
blacklist_prefixes = [
    "https://www.bilibili.com/video/",
    "https://b23.tv/"
]

@event_preprocessor
async def preprocess_webpage_screenshot(bot: Bot, event: Event):
    if not isinstance(event, MessageEvent):
        return
    
    message = event.get_message()
    if is_valid_url(message):
        url = str(message).strip()
        if not any(url.startswith(prefix) for prefix in blacklist_prefixes):
            try:
                await handle_webpage_screenshot(bot, event, url)
            except Exception as e:
                logger.error(f"处理网页截图时出错：{str(e)}", exc_info=True)
                await bot.send(event, f"处理网页截图时出错：{str(e)}")
            finally:
                raise IgnoredException("网页截图命令已处理")

async def handle_webpage_screenshot(bot: Bot, event: Event, url: str):
    screenshot_path = "screenshot.png"
    try:
        # 使用 Chromium 进行截图
        command = [
            "chromium-browser",  # 或者 "chromium"，取决于您的系统
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--screenshot=" + screenshot_path,
            "--window-size=1920,1080",
            "--virtual-time-budget=10000",  # 给予页面加载的时间（毫秒）
            url
        ]
        
        # 异步执行命令
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 等待命令执行完成
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Chromium 截图失败: {stderr.decode()}")
            raise Exception("截图失败")

        # 发送截图
        with open(screenshot_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            img_segment = MessageSegment.image(f"base64://{img_base64}")
            await bot.send(event, img_segment)

    finally:
        # 清理截图文件
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def is_valid_url(message):
    try:
        url = str(message).strip()
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False