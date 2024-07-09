import os
import json
from nonebot import on_message
from nonebot.adapters import Bot, Event
import logging

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
        #logging.info(f"Created 'user_keyword.json' file at {USER_KEYWORD_FILE}")

check_reply_dir()
check_user_keyword_file()

@text_reply.handle()
async def handle_text_reply(event: Event):
    user_msg = str(event.get_message()).strip()

    with open(USER_KEYWORD_FILE, "r") as f:
        keyword_dict = json.load(f)

    if user_msg.startswith("删除关键词"):
        # 删除关键词逻辑
        keyword_to_delete = user_msg.replace("删除关键词", "").strip()
        if keyword_to_delete in keyword_dict:
            del keyword_dict[keyword_to_delete]
            await text_reply.send(f"已删除关键词 '{keyword_to_delete}' 和对应的回答(´-ω-`) ！")
            with open(USER_KEYWORD_FILE, "w") as f:
                json.dump(keyword_dict, f)
        else:
            await text_reply.send(f"找不到关键词 '{keyword_to_delete}'，无法删除＼(º □ º l|l)/ ！")
    elif user_msg.startswith("添加关键词"):
        # 添加关键词逻辑
        keyword_and_reply = user_msg.replace("添加关键词", "").strip().split("|")
        if len(keyword_and_reply) == 2:
            keyword, reply = keyword_and_reply
            keyword_dict[keyword.strip()] = reply.strip()
            await text_reply.send(f"已添加关键词 '{keyword}' 和对应的回答(＾▽＾) ！")
            with open(USER_KEYWORD_FILE, "w") as f:
                json.dump(keyword_dict, f)
        else:
            await text_reply.send("格式错误！请按照 '添加关键词 关键词|回答' 的格式添加Σ(°△°|||)︴ 。")
    else:
        # 匹配关键词并发送回答
        if user_msg in keyword_dict:
            await text_reply.send(keyword_dict[user_msg])
        else:
            # 如果没有匹配到关键词，则可以发送默认回复或不作任何操作
            pass
