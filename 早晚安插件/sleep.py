from nonebot import on_message
from nonebot.adapters import Bot, Event
import time
import json
import os

# 获取插件目录的绝对路径
plugin_dir = os.path.dirname(__file__)
# 拼接完整的文件路径
json_file = os.path.join(plugin_dir, 'data', 'sleep_time.json')

# 确保 data 目录存在
os.makedirs(os.path.dirname(json_file), exist_ok=True)

# 定义一个全局变量，用于存储用户的睡眠时间
user_sleep_time = {}

# 定义一个函数，用于将用户的睡眠时间写入到 JSON 文件中
def save_sleep_time():
    with open(json_file, 'w') as f:
        json.dump(user_sleep_time, f)

# 定义一个函数，用于从 JSON 文件中读取用户的睡眠时间
def load_sleep_time():
    global user_sleep_time
    try:
        with open(json_file, 'r') as f:
            user_sleep_time = json.load(f)
    except FileNotFoundError:
        user_sleep_time = {}

# 在插件初始化时加载用户的睡眠时间
load_sleep_time()

# 创建一个事件响应器，当收到消息时触发
echo = on_message()

# 在事件响应器上注册一个处理函数，处理函数会接收一个事件对象
@echo.handle()
async def _(bot: Bot, event: Event):
    # 获取用户的 QQ 号
    user_id = str(event.user_id)
    # 获取消息内容
    message = str(event.message).strip()
    # 判断消息内容是否为 "晚安"
    if message == "晚安":
        # 记录晚安时间
        user_sleep_time[user_id] = time.time()
        # 保存用户的睡眠时间到 JSON 文件中
        save_sleep_time()
        # 回复晚安信息
        reply = "晚安，有个好梦( ´ ▿ ` )~"
        await bot.send(event, reply)
    # 判断消息内容是否为 "早安"
    elif message == "早安":
        # 如果没有记录晚安时间，则提示用户先发送晚安
        if user_id not in user_sleep_time:
            reply = "请先发送晚安，再发送早安哦(*￣▽￣)b~"
        else:
            # 计算时间差
            time_diff = time.time() - user_sleep_time[user_id]
            # 将时间差转换为小时、分钟、秒的形式
            hours, remainder = divmod(time_diff, 3600)
            minutes, seconds = divmod(remainder, 60)
            # 构造回复消息
            reply = f"你的睡眠时间是(◎ ◎)ゞ：{int(hours)}小时{int(minutes)}分钟{int(seconds)}秒"
        await bot.send(event, reply)
