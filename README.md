# NPT-AcoFork

这个仓库包含所有已公开的由AcoFork使用一些大语言模型编写的NoneBot2插件

___

 - 仓库全名：**N**oneBot-**P**lugin-**T**otal-AcoFork
 - 使用的大语言模型：Copilot、GPT-3.5、GPT-4o、Claude 3.5 Sonnet

___


## 使用方法
将后缀为 **.py** 的文件直接放入你的NoneBot2的 **plugins** 文件夹即可使用

### 各插件使用方法
 - Github汇报插件：编辑插件，写入你自己的Github API Token和你要启用的群和轮询时间。其中 `gh-repo.py` 用于监测仓库变动而 `gh-release.py` 用于监测Release变动
 - URL截图插件：见指令表
 - 表情包转图片插件：见指令表
 - 禁言&踢人插件：编辑插件，写入超级用户QQ号。发送 **禁言/解除禁言 @人 {秒}** 或 **踢人 @人**
 - 娶群友插件：见指令表
 - 群名片前缀插件：编辑插件，写入你的Bot昵称。默认每十秒更新一次群名片。例如：[魔力值:16] 摆烂Bot
 - 入群验证插件：编辑插件，写入你要启用的群。新人入群会发送验证消息，60s后不验证将被踢出群聊（需要Bot为管理员）
 - 设置群头衔插件：见指令表（需要Bot为群主）
 - 早晚安插件：见指令表
 - 自动回复插件：交互式写入自动回复见指令表。将 `.jpg` `.png` `.jpeg` `.mp3` `.txt` `.html` 后缀的文件放入Bot目录下的 `qtoa` 目录即可手动写入自动回复。发送对应文件名即可触发自动回复（支持文字、HTML、图片、语音）
   
## 各插件使用方法： [指令表](https://hfs.acofork.top/help.html)

## 所需依赖
报什么错就装什么，看不懂报错的问GPT

重要依赖列表：（进入虚拟环境安装）
 - nonebot.adapters.onebot.v11
 - playwright（需要使用 `playwright install` 安装浏览器）
 - nonebot_plugin_apscheduler
 - psutil
