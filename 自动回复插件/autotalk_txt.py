import os
from nonebot import on_message
from nonebot.adapters import Bot, Event
import logging

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
text_reply = on_message()

@text_reply.handle()
async def handle_text_reply(event: Event):
    # 获取用户发送的消息
    user_msg = str(event.get_message()).strip()
    
    # 构建文件路径
    file_path = os.path.join(REPLY_DIR, user_msg)
    
    text_found = False
    reply_msg = ""

    # 首先检查是否有对应的 txt 文件
    if os.path.exists(file_path + ".txt"):
        try:
            with open(file_path + ".txt", "r", encoding="utf-8") as file:
                reply_msg = file.read()
                text_found = True
                #logging.info(f"Text file found and read: {file_path}.txt")  # 调试信息
                await text_reply.send(reply_msg)
        except FileNotFoundError:
            return
            #logging.warning(f"Text file not found after being found: {file_path}.txt")  # 调试信息

    # 如果没有找到对应的文本
    if not text_found:
        return
        #logging.warning(f"No corresponding text found for: {file_path}")

# 在插件加载时检查目录是否存在，如果不存在则创建
def check_reply_dir():
    if not os.path.exists(REPLY_DIR):
        os.makedirs(REPLY_DIR)

check_reply_dir()
