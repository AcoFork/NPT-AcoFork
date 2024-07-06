import os
import base64
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment
import logging

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
voice_reply = on_message()

@voice_reply.handle()
async def handle_voice_reply(event: Event):
    # 获取用户发送的消息
    user_msg = str(event.get_message()).strip()
    
    # 构建文件路径
    file_path = os.path.join(REPLY_DIR, user_msg)
    
    voice_found = False

    # 然后检查是否有对应的语音文件
    for ext in [".mp3", ".wav"]:
        voice_path = file_path + ext
        if os.path.exists(voice_path):
            logging.info(f"Voice file found: {voice_path}")  # 调试信息
            # 读取语音文件并编码为Base64字符串
            try:
                with open(voice_path, "rb") as voice_file:
                    voice_data = voice_file.read()
                    logging.debug(f"Voice data: {voice_data[:50]}")  # 输出前50个字节的数据，用于检查语音文件是否被正确读取
                    voice_base64 = base64.b64encode(voice_data).decode("utf-8")
                    logging.debug(f"Base64 encoded voice: {voice_base64[:100]}")  # 输出前100个字符的编码数据，用于检查编码后的数据是否正确
                    voice_segment = MessageSegment.record(f"base64://{voice_base64}")
                    await voice_reply.send(voice_segment)
                    voice_found = True
                    logging.info(f"Sent voice: {voice_path}")  # 调试信息
                    break  # 发送一段语音后停止
            except Exception as e:
                logging.error(f"Failed to send voice: {e}")

    # 如果没有找到对应的语音
    if not voice_found:
        logging.warning(f"No corresponding voice found for: {file_path}")
