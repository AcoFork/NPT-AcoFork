import os
import json

from nonebot import on_message, get_bot
from nonebot.adapters import Bot, Event

# 自定义回复目录
REPLY_DIR = "qtoa"
USER_KEYWORD_FILE = os.path.join(REPLY_DIR, "user_keyword.json")

# 创建一个事件响应器，用于处理消息
text_reply = on_message()

# 在插件加载时检查目录是否存在，如果不存在则创建
def check_reply_dir():
    if not os.path.exists(REPLY_DIR):
        os.makedirs(REPLY_DIR)

# 检查并创建用户关键词文件
def check_user_keyword_file():
    if not os.path.exists(USER_KEYWORD_FILE):
        with open(USER_KEYWORD_FILE, "w") as f:
            json.dump({}, f)

check_reply_dir()
check_user_keyword_file()

@text_reply.handle()
async def handle_text_reply(event: Event):
    user_msg = str(event.get_message()).strip()

    if user_msg == "列出所有关键词":
        with open(USER_KEYWORD_FILE, "r") as f:
            keyword_dict = json.load(f)

        reply = "JSON文件中的所有关键词和回答：\n\n"
        for keyword, value in keyword_dict.items():
            reply += f"“{keyword}|{value}”\n"

        if reply:
            bot = get_bot()
            await bot.send(event, reply)

            # 发送qtoa文件夹中的所有内容
            file_list = os.listdir(REPLY_DIR)
            file_list_str = "qtoa文件夹中的所有内容：\n\n" + "\n".join(file_list)
            await bot.send(event, file_list_str)
