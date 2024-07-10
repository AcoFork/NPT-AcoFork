import os
import aiohttp
from nonebot import on_message, get_bot
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, MessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

waiting_for_url = {}

@event_preprocessor
async def preprocess_emoji_extract(bot: Bot, event: Event):
    # 只处理消息事件
    if not isinstance(event, MessageEvent):
        return

    user_id = event.user_id
    msg = event.get_message()

    if "表情包提取" in str(msg):
        waiting_for_url[user_id] = True
        await bot.send(event, "已开启表情包提取功能，请发送图片。发送 '取消' 以关闭此功能。")
        raise IgnoredException("表情包提取命令已处理")
    
    if user_id in waiting_for_url and waiting_for_url[user_id]:
        if "取消" in str(msg):
            waiting_for_url[user_id] = False
            await bot.send(event, "表情包提取功能已关闭。")
            raise IgnoredException("表情包提取已取消")

        images = [seg.data["url"] for seg in msg if seg.type == "image"]
        if images:
            image_url = images[0]
            await bot.send(event, f"提取到图片链接辣！( ´ ▽ ` ) ：{image_url}")
            waiting_for_url[user_id] = False
            raise IgnoredException("表情包已提取")

    # 如果消息中不包含图片且提取功能开启中，则忽略消息
    if user_id in waiting_for_url and waiting_for_url[user_id]:
        raise IgnoredException("等待用户发送图片")

