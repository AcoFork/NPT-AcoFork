import os
import aiohttp
from nonebot import on_message, get_bot
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

# 使用字典来跟踪每个用户是否在等待图片URL
waiting_for_url = {}

emoji_extract_cmd = on_message()

@emoji_extract_cmd.handle()
async def handle_emoji_extract_command(bot: Bot, event: Event):
    user_id = event.sender.user_id
    msg = event.get_message()
    if "表情包提取" in str(msg):
        waiting_for_url[user_id] = True
        await bot.send(event, "已开启表情包提取功能，请发送图片。")

@emoji_extract_cmd.handle()
async def handle_message(bot: Bot, event: Event):
    user_id = event.sender.user_id
    if user_id in waiting_for_url and waiting_for_url[user_id]:
        msg = event.get_message()
        images = [seg.data["url"] for seg in msg if seg.type == "image"]
        if images:
            image_url = images[0]
            await bot.send(event, f"提取到图片链接辣！( ´ ▽ ` ) ：{image_url}")
            waiting_for_url[user_id] = False  # 提取成功后，关闭等待状态