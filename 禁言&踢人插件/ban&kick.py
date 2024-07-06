from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.permission import SUPERUSER

# 定义超级用户的QQ号
SUPERUSER_ID = XXXXXXXX

# 创建消息处理器
message_handler = on_message(permission=SUPERUSER)

@message_handler.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent):
    # 获取消息内容
    message = event.get_message()
    # 获取群号
    group_id = event.group_id

    # 处理禁言命令
    if message[0].type == "text" and message[0].data["text"].startswith("禁言"):
        # 确保消息中包含@和禁言时间
        if len(message) >= 3 and message[1].type == "at" and message[2].type == "text":
            user_id = int(message[1].data["qq"])
            duration = int(message[2].data["text"].strip())
            
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=duration)
            await bot.send(event, f"已禁言用户 {user_id} {duration}秒")

    # 处理踢人命令
    elif message[0].type == "text" and message[0].data["text"].startswith("踢人"):
        # 确保消息中包含@
        if len(message) >= 2 and message[1].type == "at":
            user_id = int(message[1].data["qq"])
            
            await bot.set_group_kick(group_id=group_id, user_id=user_id)
            await bot.send(event, f"已踢出用户 {user_id}")