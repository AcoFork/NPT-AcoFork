from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

import random
import json
from datetime import date
from pathlib import Path

BLACKLIST = ["2854196310"]  # 配置黑名单

# 数据存储路径
DATA_FILE = Path("data/marry_plugin_data.json")

# 全局数据字典
data = {}

# 初始化数据
def init_data():
    global data
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

# 保存数据
def save_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 获取今天的日期字符串
def get_today():
    return date.today().isoformat()

# 初始化用户数据
def init_user_data(group_id: str, user_id: str):
    if group_id not in data:
        data[group_id] = {}
    if user_id not in data[group_id]:
        data[group_id][user_id] = {
            "spouse": None,
            "divorce_count": 0,
            "force_marry_count": 0,
            "last_update": get_today()
        }

# 重置用户每日数据
def reset_daily_data(group_id: str, user_id: str):
    today = get_today()
    if data[group_id][user_id]["last_update"] != today:
        data[group_id][user_id].update({
            "divorce_count": 0,
            "force_marry_count": 0,
            "last_update": today
        })

# 定义娶群友相关的命令
marry_commands = ["娶群友", "离婚", "强娶", "我的群老婆"]

# 消息预处理器
@event_preprocessor
async def preprocess_marry_commands(bot: Bot, event: GroupMessageEvent, state: T_State):
    if isinstance(event, GroupMessageEvent):
        msg = str(event.get_message()).strip()
        if any(msg.startswith(cmd) for cmd in marry_commands):
            # 如果是娶群友命令，阻止其他插件处理
            try:
                await handle_marry_commands(bot, event, state)
            except Exception as e:
                # 处理异常
                await bot.send(event, f"处理命令时出错：{str(e)}")
            finally:
                raise IgnoredException("娶群友命令已处理")

# 处理娶群友命令的函数
async def handle_marry_commands(bot: Bot, event: GroupMessageEvent, state: T_State):
    cmd = str(event.get_message()).strip().split()[0]
    
    if cmd == "娶群友":
        await handle_marry_random(bot, event)
    elif cmd == "离婚":
        await handle_divorce(bot, event)
    elif cmd == "强娶":
        await handle_force_marry(bot, event)
    elif cmd == "我的群老婆":
        await handle_check_spouse(bot, event)

async def handle_marry_random(bot: Bot, event: GroupMessageEvent):
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    init_user_data(group_id, user_id)
    reset_daily_data(group_id, user_id)
    
    if data[group_id][user_id]["spouse"]:
        await bot.send(event, "你已经有老婆了，不能再娶了！")
        return
    
    group_member_list = await bot.get_group_member_list(group_id=int(group_id))
    available_members = [m for m in group_member_list if str(m['user_id']) != user_id and not data[group_id].get(str(m['user_id']), {}).get("spouse")]
    
    # 过滤掉在黑名单中的成员
    available_members = [m for m in available_members if str(m['user_id']) not in BLACKLIST]
    
    if not available_members:
        await bot.send(event, "群里没有可以娶的群友了！")
        return
    
    lucky_member = random.choice(available_members)
    spouse_id = str(lucky_member['user_id'])
    
    data[group_id][user_id]["spouse"] = spouse_id
    init_user_data(group_id, spouse_id)
    data[group_id][spouse_id]["spouse"] = user_id
    
    save_data()
    
    avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={spouse_id}&s=640"
    await bot.send(event, f"恭喜你娶到了 {lucky_member['card'] or lucky_member['nickname']} 为妻！\n" + MessageSegment.image(avatar_url))


async def handle_divorce(bot: Bot, event: GroupMessageEvent):
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    init_user_data(group_id, user_id)
    reset_daily_data(group_id, user_id)
    
    if not data[group_id][user_id]["spouse"]:
        await bot.send(event, "你还没有老婆，无法离婚！")
        return
    
    if data[group_id][user_id]["divorce_count"] >= 2:
        await bot.send(event, "你今天已经离婚两次了，不能再离了！")
        return
    
    spouse_id = data[group_id][user_id]["spouse"]
    
    # 检查是否是被强娶的
    if data[group_id][spouse_id].get("forced_marry", False):
        await bot.send(event, "你是被强娶的，不能主动离婚！")
        return
    
    spouse_info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(spouse_id))
    spouse_name = spouse_info['card'] or spouse_info['nickname']
    
    data[group_id][user_id]["spouse"] = None
    data[group_id][spouse_id]["spouse"] = None
    data[group_id][user_id]["divorce_count"] += 1
    
    # 清除被强娶标记
    if "forced_marry" in data[group_id][user_id]:
        del data[group_id][user_id]["forced_marry"]
    if "forced_marry" in data[group_id][spouse_id]:
        del data[group_id][spouse_id]["forced_marry"]
    
    save_data()
    
    await bot.send(event, f"你和 {spouse_name}（{spouse_id}） 已经解除婚姻关系。")

async def handle_force_marry(bot: Bot, event: GroupMessageEvent):
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    init_user_data(group_id, user_id)
    reset_daily_data(group_id, user_id)
    
    if data[group_id][user_id]["spouse"]:
        await bot.send(event, "你已经有老婆了，不能再强娶！")
        return
    
    if data[group_id][user_id]["force_marry_count"] >= 5:
        await bot.send(event, "你今天已经强娶5次了，不能再强娶了！")
        return
    
    # 获取at的用户
    message = event.get_message()
    for seg in message:
        if seg.type == "at":
            target_id = str(seg.data["qq"])
            break
    else:
        await bot.send(event, "请@你想强娶的群友！")
        return
    
    init_user_data(group_id, target_id)
    
    success_rate = 0.05 if data[group_id][target_id]["spouse"] else 0.2
    
    data[group_id][user_id]["force_marry_count"] += 1
    
    if random.random() < success_rate:
        # 如果目标已经有配偶，先拆散他们
        if data[group_id][target_id]["spouse"]:
            original_spouse = data[group_id][target_id]["spouse"]
            data[group_id][original_spouse]["spouse"] = None
            if "forced_marry" in data[group_id][original_spouse]:
                del data[group_id][original_spouse]["forced_marry"]
        
        data[group_id][user_id]["spouse"] = target_id
        data[group_id][target_id]["spouse"] = user_id
        data[group_id][target_id]["forced_marry"] = True
        save_data()
        
        target_info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(target_id))
        target_name = target_info['card'] or target_info['nickname']
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={target_id}&s=640"
        await bot.send(event, f"强娶成功！{target_name}（{target_id}）现在是你的老婆了！\n" + MessageSegment.image(avatar_url))
    else:
        await bot.send(event, "强娶失败！")

async def handle_check_spouse(bot: Bot, event: GroupMessageEvent):
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    init_user_data(group_id, user_id)
    
    spouse_id = data[group_id][user_id]["spouse"]
    if spouse_id:
        spouse_info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(spouse_id))
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={spouse_id}&s=640"
        await bot.send(event, f"你的老婆是 {spouse_info['card'] or spouse_info['nickname']}（{spouse_id}）\n" + MessageSegment.image(avatar_url))
    else:
        await bot.send(event, "你还没有老婆哦。")

# 初始化数据
init_data()