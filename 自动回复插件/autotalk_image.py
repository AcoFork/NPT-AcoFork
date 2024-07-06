import os
import base64
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment
import logging

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
image_reply = on_message()

@image_reply.handle()
async def handle_image_reply(event: Event):
    # 获取用户发送的消息
    user_msg = str(event.get_message()).strip()
    
    # 构建文件路径
    file_path = os.path.join(REPLY_DIR, user_msg)
    
    image_found = False

    # 然后检查是否有对应的图片文件
    for ext in [".jpg", ".png", ".jpeg"]:
        image_path = file_path + ext
        if os.path.exists(image_path):
            logging.info(f"Image file found: {image_path}")  # 调试信息
            # 读取图片文件并编码为Base64字符串
            try:
                with open(image_path, "rb") as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    img_segment = MessageSegment.image(f"base64://{img_base64}")
                    await image_reply.send(img_segment)
                    image_found = True
                    logging.info(f"Sent image: {image_path}")  # 调试信息
                    break  # 发送一张图片后停止
            except Exception as e:
                logging.error(f"Failed to send image: {e}")

    # 如果没有找到对应的图片
    if not image_found:
        logging.warning(f"No corresponding image found for: {file_path}")
