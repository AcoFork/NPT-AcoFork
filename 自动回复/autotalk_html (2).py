import os
import base64
import logging
import asyncio
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
image_reply = on_message()

# 在插件加载时检查目录是否存在，如果不存在则创建
def check_reply_dir():
    if not os.path.exists(REPLY_DIR):
        os.makedirs(REPLY_DIR)

check_reply_dir()

async def generate_screenshot(html_path, output_path):
    command = [
        "chromium-browser",  # 或者 "chromium"，取决于您的系统
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--screenshot=" + output_path,
        "--window-size=600,1080",  # 设置初始窗口大小
        "--virtual-time-budget=5000",  # 给予页面加载的时间（毫秒）
        "file://" + os.path.abspath(html_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logging.error(f"Chromium 截图失败: {stderr.decode()}")
        raise Exception("截图失败")

@image_reply.handle()
async def handle_image_reply(event: Event):
    # 获取用户发送的消息
    user_msg = str(event.get_message()).strip()
    
    # 构建文件路径
    file_path = os.path.join(REPLY_DIR, user_msg)
    
    # 首先检查是否有对应的 HTML 文件
    if os.path.exists(file_path + ".html"):
        try:
            screenshot_path = file_path + "_screenshot.png"
            
            # 生成截图
            await generate_screenshot(file_path + ".html", screenshot_path)
            
            # 读取并发送截图
            with open(screenshot_path, "rb") as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                img_segment = MessageSegment.image(f"base64://{img_base64}")
                await image_reply.send(img_segment)
            
            # 删除临时截图文件
            os.remove(screenshot_path)
            
        except Exception as e:
            logging.error(f"Failed to send screenshot: {e}")
    else:
        logging.warning(f"No corresponding HTML found for: {file_path}")