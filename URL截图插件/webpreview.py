import os
import base64
import logging
import asyncio
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# 创建一个事件响应器，用于处理消息
reply = on_message()

# 定义黑名单列表，列出不希望解析的网址前缀
blacklist_prefixes = [
    "https://www.bilibili.com/video/",
    "https://b23.tv/"
]

@reply.handle()
async def handle_reply(event: Event):
    # 获取用户发送的消息
    message = event.get_message()
    
    # 检查消息是否是网址
    if not is_valid_url(message):
        return
    
    url = str(message).strip()
    
    # 检查网址是否在黑名单中（根据前缀检查）
    if any(url.startswith(prefix) for prefix in blacklist_prefixes):
        return  # 如果在黑名单中，直接返回，不进行后续操作
    
    async with async_playwright() as p:
        # 启动浏览器并打开网页
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        
        # 等待页面加载完成
        await page.wait_for_load_state("networkidle")
        
        # 模拟滚动，确保所有内容都加载
        await simulate_scroll(page)
        
        # 捕获整个页面的截图
        screenshot_path = "screenshot.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        
        # 关闭浏览器
        await browser.close()
        
        # 发送截图给用户
        with open(screenshot_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            img_segment = MessageSegment.image(f"base64://{img_base64}")
            await reply.send(img_segment)

# 判断消息是否是合法的网址
def is_valid_url(message):
    try:
        url = str(message).strip()
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# 模拟滚动，确保所有内容都加载
async def simulate_scroll(page):
    scroll_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)  # 等待滚动
        new_scroll_height = await page.evaluate("document.body.scrollHeight")
        if new_scroll_height == scroll_height:
            break
        scroll_height = new_scroll_height
