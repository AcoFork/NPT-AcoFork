import os
import base64
import logging
import asyncio
from io import BytesIO
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from PIL import Image

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
    message_str = str(message).strip()
    
    if message_str.endswith(" -f"):
        url = message_str[:-3].strip()
        full_page = True
    else:
        url = message_str
        full_page = False
    
    if is_valid_url(url):
        if not any(url.startswith(prefix) for prefix in blacklist_prefixes):
            try:
                await handle_webpage_screenshot(bot, event, url, full_page)
            except Exception as e:
                logger.error(f"处理网页截图时出错：{str(e)}", exc_info=True)
                await bot.send(event, f"处理网页截图时出错：{str(e)}")
            finally:
                raise IgnoredException("网页截图命令已处理")

async def handle_webpage_screenshot(bot: Bot, event: Event, url: str, full_page: bool):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(url, wait_until="networkidle")
            
            if full_page:
                screenshot = await page.screenshot(full_page=True)
            else:
                screenshot = await page.screenshot()
            
            await browser.close()
        
        # 处理图片
        img = Image.open(BytesIO(screenshot))
        
        # 如果是全页截图，可能需要裁剪掉底部的空白
        if full_page:
            # 从底部往上扫描，找到第一个非白色像素的位置
            width, height = img.size
            bottom = height - 1
            while bottom > 0:
                if any(img.getpixel((x, bottom))[:3] != (255, 255, 255) for x in range(width)):
                    break
                bottom -= 1
            
            # 裁剪图片
            img = img.crop((0, 0, width, bottom + 1))
        
        # 保存图片到内存中
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # 转换为base64
        img_base64 = base64.b64encode(img_byte_arr).decode("utf-8")
        
        # 发送图片
        img_segment = MessageSegment.image(f"base64://{img_base64}")
        await bot.send(event, img_segment)

    except Exception as e:
        logger.error(f"截图过程中出错：{str(e)}", exc_info=True)
        raise

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False