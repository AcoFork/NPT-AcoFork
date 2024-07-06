from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Event

# 创建一个事件处理器，监听用户的消息
set_special_title = on_message()

@set_special_title.handle()
async def handle_set_special_title(bot: Bot, event: Event):
    # 提取用户发送的消息文本
    message = event.get_plaintext()

    # 判断是否符合“给我头衔 XXX”的格式
    if message.startswith("给我头衔 "):
        # 提取出XXX作为群头衔
        special_title = message[5:]

        # 获取用户的QQ号
        user_id = event.user_id

        # 调用OneBot V11 API设置群头衔
        await bot.call_api("set_group_special_title", group_id=event.group_id, user_id=user_id, special_title=special_title)
        await set_special_title.finish("已设置你的群头衔为：" + special_title)