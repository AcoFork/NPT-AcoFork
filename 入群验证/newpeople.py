# verify_plugin.py

import random
from datetime import datetime, timedelta
from nonebot import on_notice, on_message
from nonebot.adapters.onebot.v11 import (
    Bot, GroupIncreaseNoticeEvent, GroupMessageEvent, MessageSegment
)
from nonebot_plugin_apscheduler import scheduler

verify_plugin = on_notice()
verify_response = on_message()

# 配置需要开启插件的群聊列表
enabled_groups = [1234567, 9876543]  # 替换为你希望开启插件的群聊ID

# 保存未验证用户的验证码和定时任务ID
pending_verifications = {}


@verify_plugin.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    if event.group_id not in enabled_groups:
        return

    # 生成6位随机验证码
    verification_code = ''.join(random.choice('0123456789') for _ in range(6))
    user_id = event.user_id
    group_id = event.group_id

    # 设置定时任务，60秒后检查用户是否已验证
    job = scheduler.add_job(
        kick_unverified_user,
        "date",
        run_date=datetime.now(scheduler.timezone) + timedelta(seconds=60),
        args=[bot, user_id, group_id]
    )

    pending_verifications[user_id] = {
        "code": verification_code,
        "job_id": job.id
    }

    # 发送验证消息
    message = MessageSegment.at(user_id) + f" 请发送以下验证码完成验证，超时60s将会被踢出群喵！\n验证码：{verification_code}"
    await bot.send_group_msg(group_id=group_id, message=message)


async def kick_unverified_user(bot: Bot, user_id: int, group_id: int):
    if user_id in pending_verifications:
        await bot.set_group_kick(group_id=group_id, user_id=user_id)
        del pending_verifications[user_id]


@verify_response.handle()
async def handle_verification_response(bot: Bot, event: GroupMessageEvent):
    user_id = event.user_id
    group_id = event.group_id
    message = event.get_plaintext()

    if group_id in enabled_groups and user_id in pending_verifications:
        verification_code = pending_verifications[user_id]["code"]

        if message == verification_code:
            # 取消定时任务
            job_id = pending_verifications[user_id]["job_id"]
            scheduler.remove_job(job_id)
            del pending_verifications[user_id]
            await verify_response.finish(MessageSegment.at(user_id) + " 验证成功，欢迎加入喵！")
