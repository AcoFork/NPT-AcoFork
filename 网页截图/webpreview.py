import os
import base64
import logging
import asyncio
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from urllib.parse import urlparse
from playwright.async_api import async_playwright

blacklist_prefixes = [
    "https://www.bilibili.com/video/",
    "https://b23.tv/"
]

@event_preprocessor
async def preprocess_webpage_screenshot(bot: Bot, event: Event):
    # 只处理消息事件
    if not isinstance(event, MessageEvent):
        return
    
    message = event.get_message()
    if is_valid_url(message):
        url = str(message).strip()
        if not any(url.startswith(prefix) for prefix in blacklist_prefixes):
            try:
                await handle_webpage_screenshot(bot, event, url)
            except Exception as e:
                await bot.send(event, f"处理网页截图时出错：{str(e)}")
            finally:
                raise IgnoredException("网页截图命令已处理")

async def handle_webpage_screenshot(bot: Bot, event: Event, url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        await simulate_scroll(page)
        screenshot_path = "screenshot.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        await browser.close()
        
        with open(screenshot_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            img_segment = MessageSegment.image(f"base64://{img_base64}")
            await bot.send(event, img_segment)

def is_valid_url(message):
    try:
        url = str(message).strip()
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def simulate_scroll(page):
    scroll_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)
        new_scroll_height = await page.evaluate("document.body.scrollHeight")
        if new_scroll_height == scroll_height:
            break
        scroll_height = new_scroll_height