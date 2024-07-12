import os
import ssl
import aiohttp
from nonebot import on_message, get_bot
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

# 自定义回复目录
REPLY_DIR = "qtoa"

# 创建一个事件响应器，用于处理消息
text_reply = on_message()

# 全局变量来管理交互状态和关键词字典
waiting_for_image_keyword = {}
keyword_dict = {}

# 在插件加载时检查目录是否存在，如果不存在则创建
def check_reply_dir():
    if not os.path.exists(REPLY_DIR):
        os.makedirs(REPLY_DIR)

check_reply_dir()

@text_reply.handle()
async def handle_text_reply(bot: Bot, event: Event):
    global waiting_for_image_keyword
    user_msg = str(event.get_message()).strip()
    user_id = event.get_user_id()  # 获取用户唯一标识符，这里假设是QQ号

    print(f"Received message from user {user_id}: {user_msg}")

    if user_id not in waiting_for_image_keyword and user_msg.startswith("添加图片关键词"):
        keyword = user_msg.replace("添加图片关键词", "").strip()
        waiting_for_image_keyword[user_id] = keyword
        print(f"User {user_id} entering state: waiting_for_image with keyword: {keyword}")
        await bot.send(event, f"请发送关键词 '{keyword}' 对应的图片或表情包（这将是跨纬度的，你也可以在别的群聊发送一张图或表情包），发送0退出(๑•́ ₃ •̀๑)ｴｰ")
    elif user_id in waiting_for_image_keyword:
        keyword = waiting_for_image_keyword[user_id]
        if user_msg == "0":
            print(f"User {user_id} exiting state: waiting_for_image for keyword: {keyword}")
            await bot.send(event, "已退出图片上传交互状态(ノ_<。) 。")
            del waiting_for_image_keyword[user_id]
        else:
            images = [seg.data["url"] for seg in event.get_message() if seg.type == "image"]
            if images:
                image_url = images[0]
                ssl_context = ssl.create_default_context()
                ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')  # Set a more lenient SSL context

                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                    async with session.get(image_url) as response:
                        content = await response.read()
                        # Get file extension from URL or response headers
                        file_ext = '.gif' if image_url.lower().endswith('.gif') else os.path.splitext(image_url)[1]
                        if not file_ext:
                            file_ext = '.jpg' if 'image/jpeg' in response.headers.get('Content-Type', '') else '.png'
                        image_path = os.path.join(REPLY_DIR, f"{keyword}{file_ext}")
                        with open(image_path, "wb") as f:
                            f.write(content)
                        print(f"Image downloaded and saved to: {image_path}")

                keyword_dict[keyword] = image_path
                await bot.send(event, f"已添加关键词 '{keyword}' 和对应的图片回答ヽ(o^ ^o)ﾉ ！")
                print(f"Keyword '{keyword}' and image path '{image_path}' added to dictionary")
                del waiting_for_image_keyword[user_id]
                return  # 立即返回，避免发送错误路径消息
            else:
                print("No image found in message")
                await bot.send(event, "消息中未包含图片链接，请重新发送(´-ω-`( _ _ ) 。")
    else:
        if user_msg in keyword_dict:
            await bot.send(event, MessageSegment.image(keyword_dict[user_msg]))
        else:
            return
            #print(f"No matching keyword found for message: {user_msg}")

