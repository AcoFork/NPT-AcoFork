import os
import base64
import logging
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment
from playwright.async_api import async_playwright

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
image_reply = on_message()

# 在插件加载时检查目录是否存在，如果不存在则创建
def check_reply_dir():
    if not os.path.exists(REPLY_DIR):
        os.makedirs(REPLY_DIR)

check_reply_dir()

async def generate_full_page_screenshot(page):
    # 获取页面高度
    body_height = await page.evaluate('document.body.scrollHeight')

    # 计算适合的视窗高度，确保宽度不超过480px
    viewport_width = min(await page.evaluate('document.body.clientWidth'), 480)
    viewport_height = int(body_height * viewport_width / await page.evaluate('document.body.clientWidth'))

    # 设置视窗大小和页面高度
    await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
    await page.evaluate('window.scrollTo(0, 0)')

    # 滚动并截取整个页面
    img_data = await page.screenshot(full_page=True)
    return img_data

@image_reply.handle()
async def handle_image_reply(event: Event):
    # 获取用户发送的消息
    user_msg = str(event.get_message()).strip()
    
    # 构建文件路径
    file_path = os.path.join(REPLY_DIR, user_msg)
    
    # 首先检查是否有对应的 HTML 文件
    if os.path.exists(file_path + ".html"):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                with open(file_path + ".html", "r", encoding="utf-8") as html_file:
                    html_content = html_file.read()
                    await page.set_content(html_content)
                    
                    # 等待页面元素加载完毕
                    await page.wait_for_selector('body')

                    # 获取整个页面的滚动截图
                    img_data = await generate_full_page_screenshot(page)
                    
                    await browser.close()
                
                # 将截图转换为 base64 格式并发送
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                img_segment = MessageSegment.image(f"base64://{img_base64}")
                await image_reply.send(img_segment)
                logging.info(f"Sent full page screenshot from HTML: {file_path}.html")  # 调试信息
            
        except Exception as e:
            logging.error(f"Failed to send full page screenshot from HTML: {e}")
    else:
        logging.warning(f"No corresponding HTML found for: {file_path}")
