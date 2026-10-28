# 大肥鱼桌宠 🐋

DeepSeek V4 Pro 二创形象「鲸鱼娘·大肥鱼」的透明桌面宠物。

基于三视图素材（正面 / 侧面 / 背面），用 Python + PySide6 实现，无边框透明置顶窗口。

## 功能

- **三视图行走**：左右走用侧面（自动镜像）、向上走用背面、向下走用正面

- **三种模式**：自由散步 / 跟随鼠标 / 原地待着（右键菜单切换）

- **互动**：
  - 左键按住：拖拽（会侧身朝向拖动方向，松手会说话；快速甩动会触发「快速拖拽」专属台词 + 晕眩摇摆）
  - 单击：蹦跳 + 回嘴（互动台词）+ 气泡右侧弹出聊天小圆钮（矢量图标，与气泡同步消失，点击打开聊天输入框）
  - 点击分区：按点到的位置（头 / 肚子 / 尾巴）说不同台词，并冒出爱心 ♥ / 星光 ✦ / 音符 ♪ 粒子
  - 长按 0.6 秒：摸头（爱心粒子 + 摸头台词）
  - 三连击（1.2 秒内点 3 下）：转圈庆祝 + 星星粒子 + 专属台词
  - 悬停：轻微摇摆，偶尔打招呼
  - 双击：喂食面板（小鱼干 / 蛋糕 / 棒棒糖 / 团子 / 钻石 / 披萨 / 拉面 / 饺子 / 咖啡 / 奶茶 / 炸鸡）
  - 右键：完整菜单（模式 / 大小 / 转个圈 / 打个盹 / 一起玩 / 说句话 / 设置 Key / 显示隐藏 / 鼠标穿透 / 置顶 / 开机自启 / 退出；托盘右键是同款菜单，穿透后可从托盘解除）

- **动态动作与特效**：呼吸 / 摇摆 / 蹦跳 / 眨眼 / 转圈 / 晕眩摇摆 / 悬停摇摆 / 进食 / 打盹（60 秒无互动自动睡着，点一下就叫醒）/ 爱心·星星·音符粒子飘落；转向交叉淡化、加减速惯性、散步自动休息、说话冷却；气泡与聊天按钮同步消失、弹窗自动夹入屏幕内

- **台词系统**：日常随机台词 + 互动回嘴 + 思维链心声（灰色斜体括号气泡，小概率冒出）+ 冷笑话 + 自言自语（偶尔念一句诗）+ 按时段问候（早/午/晚/深夜）+ 分区/摸头/三连击/唤醒/玩耍/快速拖拽等交互台词，全部取材自社区 DS 梗与多个开源 DeepSeek 桌宠工程

- **主动关心**：久坐 25 分钟提醒站起来活动、30 分钟没投喂会喊饿

- 托盘图标、窗口置顶、鼠标穿透、开机自启、配置记忆（config.json）；穿透 / 置顶状态重启后自动恢复

- ##### AI 对话（新增）

  - 左键单击弹出聊天小圆钮，点击后弹出聊天输入框
  - 调用 DeepSeek API（`deepseek-chat` 模型），每句话不超过 25 字，风格贱兮兮但可爱
  - 对话历史保留最近 40 条（自动记忆上下文）
  - API Key 通过右键菜单「设置 Key」输入，保存到 `config.json`
  - 聊天期间鱼会暂停移动，但呼吸/摇摆/小动作照常
  - 未设置 Key 时点击聊天按钮会直接弹出 Key 设置框，设置成功后自动打开聊天
  - 对话框弹出即自动聚焦输入框；失去鼠标焦点 5 秒后自动消失，桌宠恢复自动运行

  ##### 天气查询（新增）

  - 右键菜单「查看天气」→ 调用 `wttr.in` 获取当前城市天气
  - 城市默认从 `config.json` 读取，可手动修改配置文件中的 `"city"` 字段
  - 鱼会气泡播报：「汕头今天 26°，天气多云」

  ##### 系统状态监控（新增）

  - **CPU**：超过 90% 时冒泡提醒
  - **内存**：超过 95% 时冒泡提醒
  - **显卡（NVIDIA）**：温度超过 80°C 时冒泡提醒（`pynvml` 读取）
  - 检测间隔 10 秒，不频繁打扰

## 运行

需要 **Python 3.11+**

```bash
pip install -r requirements.txt
# 或
pip install PySide6
```

然后双击 `启动桌宠.bat`，或：

```bash
python 桌宠.py
```

## 打包成独立 exe（可分享给朋友）

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name 大肥鱼桌宠 --add-data "sprites;sprites" --icon icon.ico 桌宠.py
```

产物在 `dist/大肥鱼桌宠.exe`，对方双击即用，无需安装 Python。
（杀毒软件可能对 PyInstaller 产物误报，加信任即可。）

## 更换形象

把新的三视图（白底）放到程序目录：

1. 正面.png / 侧面.png / 背面.png（原图）
2. 运行 `python preprocess.py` —— 白底抠图 + 统一高度
3. 运行 `python preprocess2.py` —— 边缘去污 + 预乘 alpha 缩放出各尺寸精灵

## 文件说明

| 文件 | 说明 |
|------|------|
| 桌宠.py | 主程序（全部逻辑） |
| preprocess.py | 白底三视图抠图脚本 |
| preprocess2.py | 精灵边缘去污 + 多尺寸生成脚本 |
| sprites/ | 精灵图（正面/侧面/背面 各尺寸 + 图标） |
| 启动桌宠.bat | 启动脚本（自动选择 venv 或系统 Python） |
| requirements.txt | 依赖 |
| 桌宠.spec | PyInstaller 打包配置（含新依赖收集） |
| test_pet.py | 自动化功能测试（QtTest 模拟鼠标/键盘交互，覆盖单击/双击/拖拽/聊天/喂食/分区点击/三连击/打盹/粒子/快速拖拽/主动关心等 79 项） |

## 贡献与致谢

- **AI 对话 / 天气查询 / 系统监控 / PyInstaller 打包配置**：由 [Cpanoe](https://github.com/Cpanoe) 通过 [PR#3](https://github.com/1190fasheqi/dafeiyu-pet/pull/3) 贡献（DeepSeek API 聊天、wttr.in 天气、CPU/内存/GPU 监控、桌宠.spec）。
- 合并时维护方修复：
  - 线程安全：DeepSeek 回复由后台线程直接调用 Qt 界面改为经队列转发主线程（`_say_queue`）
  - 配置保护：`config.json` 保持不入仓库（本地配置含 API Key，防止泄露）
- 桌面宠物朝向修复由 [B-A-A-GE](https://github.com/B-A-A-GE) 通过 [PR#1](https://github.com/1190fasheqi/dafeiyu-pet/pull/1) 提交（未合并，当前为维护方修复版）。

## 台词梗来源

台词均取自 DeepSeek / 鲸鱼娘 / 大肥鱼社区梗（D指导去吃饭、吃白饭、梁文锋会议三连、"才不是大肥鱼"、思维链心声等），感谢社区整活。

扩充台词时采集参考了以下 GitHub 上的 DeepSeek 桌宠工程：

- [QCYTSN/ds-local-pet](https://github.com/QCYTSN/ds-local-pet) —— 本地优先大肥鱼（日常/互动/内心OS/状态/长短按台词）
- [YunYueSama/codex-deepseek-pet](https://github.com/YunYueSama/codex-deepseek-pet) —— Codex 大肥鱼（随机动作/点击互动台词）
- [chenthreegold/deepseek-whale-pet](https://github.com/chenthreegold/deepseek-whale-pet) —— 鲸鱼娘 Codex 桌宠（语录/冷笑话/时段问候/睡觉唤醒）
- [lov0vo/dsh-whale-maid](https://github.com/lov0vo/dsh-whale-maid) —— 鲸鱼女仆十状态桌宠（分区摸头台词/三连击/主动关心/爱心星星音符粒子）
- [gmskywalker/deepseek-fat-fish-codex-pet](https://github.com/gmskywalker/deepseek-fat-fish-codex-pet) —— 大肥鱼 Codex 动画桌宠
- [sjmsltx/deepseek-desktop-pet](https://github.com/sjmsltx/deepseek-desktop-pet) —— 双角色陪伴桌宠（问候/思考/情绪台词）
- [asgaerg/desktop-pet](https://github.com/asgaerg/desktop-pet) —— 桌面 AI 伴侣（自言自语念句子玩法）
- [FlytoMAYDAY80/dsh-pet](https://github.com/FlytoMAYDAY80/dsh-pet) —— 像素小鲸鱼桌宠（待机/工作/完成/离线状态图）
- [xiaoshihou514/dsh-desktop-pet](https://github.com/xiaoshihou514/dsh-desktop-pet) —— 鲸鱼娘桌宠（眨眼/睡眠/唤醒状态机）
- [nolodjska/dsh-dafeiyu](https://github.com/nolodjska/dsh-dafeiyu) —— DSH Agent 状态台词
- [Egger0/desk-pet](https://github.com/Egger0/desk-pet) —— 透明动画桌宠 + DeepSeek 余额显示
- [ymhyyds/DesktopPet](https://github.com/ymhyyds/DesktopPet) —— Qt6 + Live2D 桌宠（DeepSeek 对话 + Edge TTS）
- [waterfeet/DoroPet](https://github.com/waterfeet/DoroPet) —— Doro 桌宠（PyQt5 + DeepSeek 等多模型）
- [Maboroshinatsu/maibot-deskpet-plugin](https://github.com/Maboroshinatsu/maibot-deskpet-plugin) —— MaiBot Live2D 桌宠插件
- [anneheartrecord/dsh-desk-pet](https://github.com/anneheartrecord/dsh-desk-pet) / [cpp285/OceanPet](https://github.com/cpp285/OceanPet) —— macOS 桌宠

## 协议

MIT
