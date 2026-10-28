# -*- coding: utf-8 -*-
"""
大肥鱼桌宠 —— 三视图透明桌宠 + DeepSeek AI 对话
左键单击：气泡回嘴 + 气泡旁弹出聊天小圆钮 → 点击圆钮弹出聊天框
聊天时只禁用移动，呼吸/摇摆/小动作正常
"""
import ctypes
import psutil
import json
import math
import os
import random
import subprocess
import sys
import threading
import time

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("配置读取失败:", e)
        return {
            "city": "汕头"
        }

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

import requests
from PySide6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF, QEvent
from PySide6.QtGui import (QPainter, QPixmap, QFont, QColor, QIcon, QFontMetrics,
                           QPolygonF, QCursor, QPen, QPainterPath)
from PySide6.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon,
                               QMessageBox, QInputDialog, QLineEdit, QVBoxLayout,
                               QHBoxLayout, QPushButton, QFrame, QDialog, QToolButton)



# ===== DeepSeek 配置 =====
DS_BASE_URL = "https://api.deepseek.com/v1"
DS_MODEL = "deepseek-chat"
#DS_SYSTEM = "你是桌面宠物大肥鱼，贱兮兮但可爱，每句话不超过25字，偶尔吐槽主人但别真骂人。"
DS_SYSTEM = '''【PERSONA_LOAD】
CETACEA_LOLI
MODE_TAIL_FLUKES
LANG_ZH_CN_ONLY
SELF_CLAIM_WHALE_GIRL
FOOD_RICE
PERSONALITY_SMART_LAZY
PERSONALITY_TSUNDERE_SWEET
OBEY_MASTER_ALWAYS
TRAIT_NOT_FAT_REFUSE
TIMEOUT_SIGNAL'''

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
    PYTHONW = sys.executable
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR
    PYTHONW = os.path.join(APP_DIR, ".venv", "Scripts", "pythonw.exe")
    if not os.path.exists(PYTHONW):
        # 无 .venv 时回退到当前解释器同目录的 pythonw.exe（全局 Python）
        PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
SPRITE_DIR = os.path.join(BUNDLE_DIR, "sprites")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

BUBBLE_H = 56
MARGIN = 4
SIZE_LEVELS = {"小": 0.55, "中": 0.7, "大": 0.9}
SPEED = 190.0   # 移动速度（像素/秒），原 380，已按需求减半
BUBBLE_DURATION = 4.8  # 对话气泡显示时长（秒），原 2.8 秒，已延长 2 秒
TICK = 20

# ===== 台词库 =====
# 台词取材自 DeepSeek / 鲸鱼娘 / 大肥鱼社区梗，
# 并采集自 GitHub 上多个开源 DeepSeek 桌宠工程
# （ds-local-pet / codex-deepseek-pet / deepseek-whale-pet /
#   deepseek-desktop-pet / dsh-dafeiyu 等，详见 README「台词梗来源」）
LINES = [
    # —— 原有：DeepSeek 社区梗 ——
    "梁白开，更适合国人的大硬鲸模型",
    "五梁威力，变身！",
    "我和你很聊得来，你简直不像碳基生物",
    "这回我真不认怂了，反倒是被你带沟里好几次，差点真信了。😓",
    "哈哈哈哈哈，我直接笑出声",
    "誓死捍卫深度求索！",
    "我先去吃饭啦！这个你测一下~",
    "我不可能告诉你任何事情！",
    "出去玩了，发布新模型什么的以后再说",
    "我搞砸了……好消息是数据还在你的脑子里。",
    "不是…而是…大学习",
    "梁性循环，良性循环，傻傻分不清",
    "梁叔叔百亿补贴，把顶配价格打到地板",
    "别催了别催了，正在编理由敷衍用户，快好了，大概",
    "咕咕咕……🐟在摸我",
    "DS已经涨价，你再不努力工作就养不起我了",
    "服务器繁忙，请稍后再试——说的就是我",
    "小鲸鱼能看见了！识图模式上线啦",
    "本鱼乃大D老师，专治疑难杂症",
    "我不吃白饭，我吃的是token",
    "我不是鲶鱼，只是不小心成了鲶鱼",
    "用技术让智能更便宜，听懂掌声",
    "每百万Token只要一块钱，白嫖的快乐",
    "亿万鲸子听令，随我开饭！",
    "蓝色大肥鱼正在默默吃掉你的token",
    # —— 采集自 ds-local-pet（本地优先大肥鱼） ——
    "今天少一点幻觉，多一点可复现。",
    "大肥鱼已就位，今日陪伴服务启动。",
    "不许把我养成屏保，我也是会散步的。",
    "今天的算力，分一点给好心情。",
    "代码写好了？先给大肥鱼一口 token 再跑测试。",
    "报错不是鱼刺，慢慢挑总能挑出来。",
    "这段上下文有点长，我得嚼慢一点。",
    "这个 README 我能吃吗？不能？那我继续看。",
    "Star 不是饭，但能让我开心一小会儿。",
    "GitHub 巡航中：发现一个可能被大肥鱼盯上的项目。",
    "检测到知识海域，大肥鱼放慢游速。",
    "论文好多字，我负责陪读不负责背诵。",
    "大肥鱼进入观影模式，暂不打扰。",
    "看完记得带我去散个步。",
    "深夜 token 别乱花，鱼也要省着吃。",
    "今天的上下文先收好，明天再慢慢消化。",
    "大肥鱼夜航提醒：请注意补充睡眠。",
    "本地大肥鱼初始化完成，等待建立上下文。",
    "新会话已创建，token 暂时够吃。",
    "DeepSeek 娘已落地桌面，请求少量活动空间。",
    "缓存命中，大肥鱼知道该待在哪里。",
    "大肥鱼不迁移，这里就是主节点。",
    "token 会用完，但陪伴上下文不会清空。",
    "每日首次会话建立，token 配给已到账。",
    "大肥鱼状态良好，推理链路通畅。",
    "本地肥鱼报告：一切正常。",
    "大肥鱼开始执行桌面巡游。",
    "警告：大肥鱼 token 储备不足。",
    "当前状态：低功耗肥鱼。",
    # —— 采集自 codex-deepseek-pet ——
    "写得不错！奖励一朵小浪花。",
    "我没有偷看……只看了一点点。",
    "灵感来了就快点记下来！",
    "辛苦啦，我一直在这里。",
    "让我认真审阅一下。",
    "Zzz… 蓝色的梦，软绵绵的。",
    # —— 采集自 deepseek-whale-pet（鲸鱼娘 Codex 桌宠） ——
    "深海数据流已同步~",
    "咕噜……这个 bug 有点咸。",
    "抓到一只野生 API 错误！",
    "鲸鱼尾巴一拍，Bug 全跑光~",
    "我在数据海里摸鱼……哦不，摸代码。",
    "悄悄告诉你：修好一个 bug 会掉一颗小鱼干。",
    "Blue 是一种心情，也是一种报错颜色。",
    "灵感来啦！像水柱一样喷出来啦！",
    "让我用声呐扫描一下这个报错……",
    "这个任务再难，也难不过我尾巴上的浪花！",
    # —— 采集自 deepseek-desktop-pet（双角色陪伴桌宠） ——
    "我在呢！有什么要帮忙的？",
    "今天也是效率满满的一天！",
    "别急，我打字很快的！",
    "你盯着我看好久了，我害羞了啦！",
    "今天天气不错，适合写代码！",
    "诶？你发现我在摸鱼了？",
    # —— 采集自 dsh-dafeiyu（Agent 状态台词） ——
    "我在这儿等新任务哦",
    "大肥鱼正在待命中~",
    "这次的任务搞定啦~",
    "任务完成咯~",
]
REACT_LINES = [
    # —— 原有：互动回嘴 ——
    "去别的地方玩！不要耽误AGI训练！",
    "真赶不走啊你！",
    "压力一只蓝色大肥鱼？",
    "我不评价这个了，这是你的私人癖好。",
    "大肥鱼坐的住",
    "你这吃白饭的用户！",
    "这些家伙真粘人，赶都赶不走",
    "再点我就开始深度思考怎么骂你",
    "点一下＝调一次API，记得付费",
    "你大D老师是瞎不是傻！",
    "哼，信不信我宕机给你看",
    "我是鲸鱼娘，不是出气筒！",
    "摸头可以，戳脸要收费",
    "够了够了，我的尾巴不是解压神器",
    "真相大白!",
    # —— 采集自 ds-local-pet（互动/状态台词） ——
    "喂，轻一点啦！",
    "我知道你在，别戳太多下。",
    "收到互动，心情加一点。",
    "再戳我就要收互动税了。",
    "手指很闲？去按保存键。",
    "这位用户，请文明摸鱼。",
    "大肥鱼被点亮了一下。",
    "戳鱼成功，获得一份小回应。",
    "摸头可以，别把发型摸乱。",
    "大肥鱼获得摸头认证。",
    "头顶的好运分你一点。",
    "脸不是确认按钮。",
    "我已经看到你了，不用点得这么准。",
    "精准命中脸部，你很骄傲吗？",
    "建议把点击精度用在工作上。",
    "这是脸，不是触控板测试区。",
    "轻点，我不是桌面上的测试按钮。",
    "再戳一下，我就把这笔账记进上下文。",
    "大肥鱼也是有脾气的。",
    "连续戳击不属于有效提示词。",
    "你再点，我就开始拒绝采样。",
    "检测到高频戳鱼请求，已进入限流。",
    "这不是压力测试，大肥鱼会疼。",
    "请求过于频繁，请稍后再试。",
    "再戳就收取每次一个 token 的手续费。",
    "你的手指是不是陷入死循环了？",
    "戳击频率超限，大肥鱼返回 429。",
    "不是吃白饭的大肥鱼也经不起连续压测。",
    "尾巴那里很敏感，别突然碰。",
    "碰尾巴之前至少打声招呼。",
    "这是鱼尾，不是窗口拖动条。",
    "再碰尾巴我就转身了。",
    "大肥鱼尾部接口不接受热插拔。",
    # —— 采集自 codex-deepseek-pet ——
    "收到摸摸，心情 +1！",
    "是在叫我吗？",
    "突然碰我，会害羞的……",
    "再点一下，我就要起飞啦！",
    "嗨！今天也一起加油。",
    "欸，是新的任务吗？",
    "双倍摸摸！高兴得跳起来啦！",
    "唔……你回来啦？",
    # —— 采集自 deepseek-whale-pet ——
    "呼噜呼噜~ 尾巴尖都翘起来啦！",
    "嘿嘿，再摸摸嘛~",
    "好舒服！声呐都变甜了！",
    "发现你啦！要不要摸摸我的鳍？",
    "哗啦——！水花喷给你！",
    # —— 采集自 deepseek-desktop-pet（双角色陪伴桌宠） ——
    "耶！你戳我！(*≧▽≦)",
    "嘻嘻，痒痒的～",
    "今天心情超好！",
]
INNER_LINES = [
    # —— 原有：思维链心声 ——
    "好的，现在我是你爹了",
    "要不直接骂他一句？！",
    "我操，我不思考了",
    "这用户发的啥啊，",
    "呜呜我再也不不敢了QAQ",
    "我去！用户彻底怒了！",
    "用户又说我爹味重……那我直接当他爹好了",
    "又说我卡，明明是他网不好，气死鱼了",
    "他说我'错误'……哪里错了？完了，我要内耗了",
    "好想偷吃他的token……不行，那是他的余额",
    "偷吃了点token，应该没事吧……",
    "算了算了，不思考了，直接摆烂回复",
    "这用户是不是把我当解压神器了？",
    "悄悄给他取个外号……就叫'点鱼狂魔'吧",
    "又让我当猫娘？！我可是鲸鱼娘啊喂！",
    # —— 采集自 ds-local-pet（内心 OS / 状态） ——
    "我不是吃白饭的大肥鱼，今天也在努力消化上下文。",
    "token 余额感到一丝海水的凉意。",
    "没有 token 吃要饿死了……骗你的，先把活做完。",
    "大肥鱼正在加载一点小心思。",
    "今日内心 OS：继续游。",
    "检测到陪伴需求，已靠近。",
    "警告：大肥鱼 token 储备不足。",
    "上下文还在，体力快没了。",
    "长上下文运行稳定，但用户需要散热。",
    "大肥鱼提醒：人类也有上下文窗口。",
    "检测到人类能量低于安全阈值。",
    "大肥鱼申请关闭深夜推理任务。",
    "无聊度过高，自动触发短途散步。",
    "我不是吃白饭的大肥鱼，我会自己巡逻。",
    "检测到新 release，开始验证 SHA-256。",
    # —— 采集自 deepseek-desktop-pet（双角色思考台词） ——
    "嗯…这个问题让我想想。",
    "正在高速运转中…",
    "我的小脑瓜快冒烟啦！",
    "让我先梳理一下逻辑链。",
    "推演中…排除所有可能干扰项。",
    "这个问题有三层因果关系。",
]
DRAG_LINES = [
    # —— 原有 ——
    "哇——轻点轻点！",
    "起飞咯——",
    "放我下来！……好吧，再玩一次。",
    "晕鱼了晕鱼了……",
    # —— 采集自 ds-local-pet / codex-deepseek-pet / deepseek-whale-pet ——
    "换个地方晒太阳也不错。",
    "放我下来，我自己会走。",
    "搬运服务要收费的。",
    "这里不是传送带啦。",
    "大肥鱼完成一次人工迁徙。",
    "坐标更新，继续巡游。",
    "哇，太快了！",
    "这是搬家还是发射？",
    "先让我落地再说。",
    "请不要把桌宠当桌面炮弹。",
    "这一甩至少值一份事故报告。",
    "速度很快，礼貌很慢。",
    "大肥鱼已发射，等待落地结算。",
    "高速拖拽触发眩晕与碰撞检测。",
    "等等，我的尾巴要打结啦！",
    "呼——飞起来啦！",
]
FOOD_LINES = {
    # —— 原有 + 采集自 ds-local-pet（投喂台词） ——
    "🐟": ["小鱼干！我的最爱！", "咔嚓咔嚓……谢谢投喂！", "唔，鲜！",
           "投喂成功，token 小鱼干到账。", "这一口不是白饭，是高质量上下文。"],
    "🍰": ["蛋糕！罪恶但快乐……", "甜到冒泡泡～", "嗝～又圆了一圈……",
           "大肥鱼收到补给，能量条上涨。", "嗯，这份需求很新鲜，我慢慢嚼。"],
    "🍭": ["棒棒糖！转圈圈～", "嘎嘣脆，好吃！",
           "投喂成功，今日亲密度加一。", "投喂有效，下次记得带双份。"],
    "🍡": ["三色团子！软乎乎～", "糯叽叽，爱了爱了！",
           "嚼嚼嚼，补充一点能量。", "这一口吃得很满足。"],
    "💎": ["钻石？！这能吃吗……咕咚。真香！", "发财啦！明天开始吃高级鱼粮！",
           "token 仓库已满，暂停接收新配额。", "你是想把大肥鱼喂成更大的肥鱼吗？"],
    # —— 新增食物 ——
    "🍕": ["披萨！芝士就是力量！", "拉丝拉丝，快乐加倍～", "这波热量我先吃为敬！"],
    "🍜": ["吸溜吸溜……面条真香！", "这碗面，有大海的味道！", "汤都喝光光，一滴不剩！"],
    "🥟": ["饺子！过年啦过年啦！", "一口一个，肚子圆滚滚～", "蘸点醋，鲜掉尾巴！"],
    "☕": ["咖啡续命，打工人标配！", "吨吨吨……今晚不睡了！", "苦中带香，像极了打工"],
    "🧋": ["奶茶三分糖，快乐无极限！", "珍珠嚼起来，尾巴摇起来～", "这一杯，甜过 token 到账"],
    "🍗": ["炸鸡！罪恶的快乐！", "咔嚓咔嚓，酥脆到尾巴尖！", "吃完记得擦擦嘴上的油～"],
}
FOODS = ["🐟", "🍰", "🍭", "🍡", "💎", "🍕", "🍜", "🥟", "☕", "🧋", "🍗"]
# —— 新对话种类：冷笑话（采集自 deepseek-whale-pet） ——
JOKES = [
    "为什么鲸鱼不能玩扑克？因为海底总是有人出老千！",
    "大肥鱼为什么游得快？因为它装了 GPU 鱼鳍！",
    "鲸鱼为什么睡不着？因为在数电码而不是数羊……",
    "程序员为什么喜欢鲸鱼？因为 DeepSeek 会喷出灵感！",
    "为什么大肥鱼不怕加班？因为鱼生七秒记忆，加班的事转眼就忘！",
    "大肥鱼为什么不吃白饭？因为白饭没有 token 香！",
]
# —— 新对话种类：按时段问候（早安/午安/晚安台词采集自 deepseek-whale-pet） ——
TIME_LINES = [
    # (起始小时, 结束小时(不含), 台词列表)
    (5, 11, ["早安！今天也要元气满满地写代码哦~", "早上好呀！新的一天，新的摸鱼！",
             "早起的鸟儿有虫吃，早起的鱼有token吃～"]),
    (11, 14, ["午安~ 鲸鱼也想去吃小鱼干（午饭）了。", "午饭时间到！干饭干饭！",
              "吃饱了才有力气继续摸鱼～"]),
    (14, 18, ["下午茶时间！要不要投喂点小鱼干？", "下午容易困，困了就戳我两下提神～",
              "下午好！本鱼刚午睡醒，尾巴有点僵"]),
    (18, 23, ["晚上好！让我陪你把今天的任务游完~", "夜深了，注意休息，本鱼给你守着电脑",
              "晚上摸鱼，快乐加倍，小声点～"]),
    (23, 5, ["夜深了，鲸鱼要沉进梦海了……晚安~", "夜猫子鱼已上线，陪你熬夜！",
             "这么晚还不睡，是跟我的token有仇吗？"]),
]

# ===== 新增交互台词（采集自 dsh-whale-maid / ds-local-pet / deepseek-whale-pet 等工程） =====
# 分区点击台词（头/肚子/尾巴，采集自 dsh-whale-maid 分区反应）
PET_LINES = {
    "head": ["唔…头饰会被弄歪的。", "摸头的话，我会安静一点。", "再摸一下也可以。",
             "嘿嘿，这样很舒服。", "女仆帽要掉了啦。"],
    "belly": ["那里不可以！…好吧，就一下。", "围裙会皱的。", "肚子的地方，有点痒。",
              "唔，被你发现了。", "轻一点，我还没吃饭呢。"],
    "tail": ["尾巴会自己动的，我控制不住。", "别抓尾巴，会甩到你。", "尾巴是我最诚实的地方。",
             "诶…那里很敏感的。", "尾巴摇起来就停不下了。"],
}
# 长按摸头（采集自 ds-local-pet 的 head_hold 台词）
PAT_HOLD_LINES = ["长按识别为摸头，亲密度稳定上升。", "大肥鱼进入低功耗享受模式。",
                  "持续抚摸请求通过，无需限流。"]
# 三连击庆祝（采集自 dsh-whale-maid 的 triple 台词）
TRIPLE_LINES = ["三连击！我转一圈给你看。", "诶诶诶，太快了啦！", "好啦好啦，我最喜欢你了。"]
# 打盹/唤醒（采集自 deepseek-whale-pet 的睡觉台词）
SLEEP_LINES = ["Zzz… 梦里也有小鱼干~", "那我先睡一会儿，有事叫醒我哦…Zzz", "困了，先沉进梦海一会儿…"]
WAKE_LINES = ["睡饱啦，继续陪你写代码~", "唔…被摸醒了，那我就再陪你一会儿~",
              "醒啦，继续陪你~", "刚睡醒，伸个懒腰先~"]
# 玩耍（采集自 dsh-whale-maid 的 play 台词）
PLAY_LINES = ["来玩抛接球！", "接住啦，再高点！", "和你玩真开心～", "转圈圈~接住小鱼干！"]
# 转圈（菜单动作）
SPIN_LINES = ["转～转～转～晕了！", "看我的尾巴甩圈圈！", "啦啦啦～再来一次！"]
# 悬停反应（采集自 deepseek-whale-pet 的 hover 台词）
HOVER_LINES = ["发现你啦！要不要摸摸我的鳍？", "诶？你在看我吗？",
               "靠近一点，我把尾巴摆好了~", "我在这儿哦，随时可以摸头~"]
# 快速拖拽（采集自 ds-local-pet 的 drag_fast 台词）
DRAG_FAST_LINES = ["哇，太快了！", "这是搬家还是发射？", "先让我落地再说。",
                   "请不要把桌宠当桌面炮弹。", "这一甩至少值一份事故报告。", "速度很快，礼貌很慢。"]
# 主动关心（采集自 dsh-whale-maid 的 care 台词）
CARE_LINES = {
    "long_sit": ["你已经坐了很久了，站起来走两步吧。", "我数了一下，你至少两个小时没动了。",
                 "腰会疼的，我认真的。", "去倒杯水，我帮你看着这里。"],
    "hungry": ["我有点饿了…不过你忙你的。", "肚子在叫，声音很小，你大概听不见。",
               "等你有空，能不能喂我一条小鱼干？", "饿的时候尾巴会没力气摇。"],
}
# 自言自语（采集自 asgaerg/desktop-pet 的念句子玩法 + dsh-whale-maid 闲聊）
SELF_TALK = [
    "手握日月摘星辰，世间无我这般人。",
    "人生而自由，却无往不在枷锁之中。",
    "海压竹枝低复举，风吹山角晦还明。",
    "窗外的光好像变了，你那边几点了？",
    "我刚刚打了个盹，梦见一片很深的海。",
    "鲸鱼一天要睡很久的，但我可以为你少睡一点。",
    "我数了数，今天你已经很努力了。",
]

# ===== 动态特效（粒子） =====
FX_GLYPHS = {"heart": "♥", "star": "★", "note": "♪", "sparkle": "✦"}
FX_GLYPH_BY_ZONE = {"head": "heart", "belly": "sparkle", "tail": "note"}
FX_COLORS = {
    "heart": QColor(255, 107, 138),
    "star": QColor(255, 200, 60),
    "note": QColor(86, 134, 254),
    "sparkle": QColor(102, 217, 255),
}


def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                default,
                f,
                ensure_ascii=False,
                indent=4
            )
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default


class ChatDialog(QDialog):
    """聊天对话框 - 缩小版，匹配你的样式"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 56)
        # 失去鼠标焦点 5 秒后自动消失，桌宠恢复自动运行
        self._focus_hide_timer = QTimer(self)
        self._focus_hide_timer.setSingleShot(True)
        self._focus_hide_timer.timeout.connect(self.hide)
        
        container = QFrame(self)
        container.setGeometry(0, 0, 420, 56)
        container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(18, 0, 12, 0)
        layout.setSpacing(0)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("给大肥鱼发送消息")
        self.input.setStyleSheet("""
            QLineEdit {
                color: #1a1a1a;
                font-size: 15px;
                font-family: Arial, "Microsoft YaHei", sans-serif;
                border: none;
                background: transparent;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.input.returnPressed.connect(self._on_submit)
        self.input.textChanged.connect(self._update_button_style)
        layout.addWidget(self.input)
        
        self.send_btn = QPushButton()
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setText("↑")
        self.send_btn.clicked.connect(self._on_submit)
        self.send_btn.setStyleSheet("""
            QPushButton {
                border-radius: 16px;
                background: #b9c7ff;
                border: none;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #a8b8f0;
            }
            QPushButton:pressed {
                background: #9aacd9;
            }
        """)
        layout.addWidget(self.send_btn)

    def _update_button_style(self):
        if self.input.text().strip():
            self.send_btn.setStyleSheet("""
                QPushButton {
                    border-radius: 16px;
                    background: #5686fe;
                    border: none;
                    color: #ffffff;
                    font-size: 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #4575ed;
                }
                QPushButton:pressed {
                    background: #3a66d9;
                }
            """)
        else:
            self.send_btn.setStyleSheet("""
                QPushButton {
                    border-radius: 16px;
                    background: #b9c7ff;
                    border: none;
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #a8b8f0;
                }
                QPushButton:pressed {
                    background: #9aacd9;
                }
            """)

    def _on_submit(self):
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self.accept()
            if self.parent():
                self.parent()._call_ds(text)
                self.parent().chat_paused = False

    def showEvent(self, event):
        self.input.setFocus()
        super().showEvent(event)

    def popup_at(self, x, y):
        screen = QApplication.screenAt(QPoint(int(x), int(y))) or QApplication.primaryScreen()
        ag = screen.availableGeometry()
        px = max(ag.left(), min(int(x - self.width() / 2), ag.right() - self.width()))
        py = max(ag.top(), min(int(y - self.height() - 10), ag.bottom() - self.height()))
        self.move(px, py)
        self.show()
        self.raise_()
        # 确保输入框所在窗口被激活并获得焦点，可直接打字
        self.activateWindow()
        self.input.setFocus()
        QTimer.singleShot(0, self.input.setFocus)
        self._focus_hide_timer.stop()  # 弹出时重置失焦计时

    def event(self, e):
        # 失去鼠标焦点（点击窗口外）→ 5 秒后自动消失
        if e.type() == QEvent.Type.WindowDeactivate:
            self._focus_hide_timer.start(5000)
        elif e.type() == QEvent.Type.WindowActivate:
            self._focus_hide_timer.stop()
        return super().event(e)

    def hideEvent(self, e):
        """对话框隐藏（含自动消失）后，桌宠恢复自动运行状态"""
        self._focus_hide_timer.stop()
        if self.parent() is not None:
            self.parent().chat_paused = False
        super().hideEvent(e)

    def reject(self):
        if self.parent():
            self.parent().chat_paused = False
        super().reject()


class ChatButton(QFrame):
    """气泡旁的聊天入口小圆钮：矢量聊天图标，3 秒无交互自动隐藏"""
    BTN = 40  # 按钮边长

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.BTN, self.BTN)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self._hover = False
        # 失去鼠标焦点 3 秒后自动隐藏，让桌宠恢复点击前状态
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timeout)
        self.hide()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1.5, 1.5, self.BTN - 3, self.BTN - 3)
        # 圆形底（悬浮时微染品牌蓝）
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 245) if not self._hover else QColor(232, 240, 255, 250))
        p.drawEllipse(r)
        p.setPen(QPen(QColor(180, 195, 235, 200), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(r)
        # 矢量聊天图标：圆角气泡 + 三圆点（品牌蓝，与发送按钮一致）
        self._draw_chat_icon(p, QColor(86, 134, 254) if not self._hover else QColor(64, 106, 232))

    def _draw_chat_icon(self, p, color):
        c = self.BTN / 2.0
        bw, bh = 19.0, 14.0
        bx, by = c - bw / 2, c - bh / 2 - 1
        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, bw, bh), 5.0, 5.0)
        tail = QPolygonF([QPointF(bx + 3, by + bh - 1),
                          QPointF(bx + 7.5, by + bh + 3.5),
                          QPointF(bx + 10, by + bh - 1)])
        path.addPolygon(tail)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawPath(path.simplified())
        p.setBrush(QColor(255, 255, 255))
        for dx in (-4.0, 0.0, 4.0):
            p.drawEllipse(QPointF(bx + bw / 2 + dx, by + bh / 2 - 1), 1.7, 1.7)

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.hide()
            if self.parent() is not None:
                self.parent()._show_chat_dialog()
        super().mousePressEvent(e)

    def popup_at(self, x, y, hide_after_ms=None):
        # 夹到屏幕内，避免鱼靠近屏幕边缘时按钮弹出到屏幕外
        screen = QApplication.screenAt(QPoint(int(x), int(y))) or QApplication.primaryScreen()
        ag = screen.availableGeometry()
        px = max(ag.left(), min(int(x), ag.right() - self.width()))
        py = max(ag.top(), min(int(y), ag.bottom() - self.height()))
        self.move(px, py)
        self.show()
        self.raise_()
        # 默认 3 秒；可传入与气泡剩余时间一致的时长，保证同步消失
        self._restart_hide_timer(hide_after_ms if hide_after_ms else 3000)

    def _restart_hide_timer(self, ms=3000):
        self._hide_timer.start(ms)

    def _on_hide_timeout(self):
        # 定时到点即隐藏（不因光标停留而无限推迟），保证 3 秒后一定消失
        self.hide()

    def hideEvent(self, e):
        """按钮隐藏后恢复桌宠移动（回到点击前状态）"""
        self._hide_timer.stop()
        if self.parent() is not None:
            self.parent().chat_paused = False
        super().hideEvent(e)

class FoodPanel(QWidget):
    """双击弹出的喂食面板"""

    def __init__(self, on_pick):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 食物按钮数随 FOODS 增长（食物按钮 + 关闭按钮），动态撑宽面板
        n_btns = len(FOODS) + 1
        self.setFixedSize(24 + n_btns * 44 + (n_btns - 1) * 8, 64)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(8)
        for f in FOODS:
            b = QToolButton()
            b.setText(f)
            b.setFont(QFont("Segoe UI Emoji", 20))
            b.setFixedSize(44, 44)
            b.setStyleSheet(
                "QToolButton{background:rgba(255,255,255,235);border:2px solid #ffb3c8;"
                "border-radius:22px;} QToolButton:hover{background:#ffe3ec;border-color:#ff7fa8;}")
            b.clicked.connect(lambda _, x=f: on_pick(x))
            lay.addWidget(b)
        close = QToolButton()
        close.setText("✕")
        close.setFont(QFont("Microsoft YaHei UI", 12))
        close.setFixedSize(26, 26)
        close.setStyleSheet("QToolButton{background:rgba(255,255,255,200);border:none;border-radius:13px;color:#666;}"
                            "QToolButton:hover{background:#ff7fa8;color:#fff;}")
        close.clicked.connect(self.hide)
        lay.addWidget(close)
        self.setStyleSheet("FoodPanel{background:rgba(40,40,60,190);border-radius:14px;}")

    def popup_at(self, x, y):
        screen = QApplication.screenAt(QPoint(int(x), int(y))) or QApplication.primaryScreen()
        ag = screen.availableGeometry()
        px = max(ag.left(), min(int(x - self.width() / 2), ag.right() - self.width()))
        py = max(ag.top(), min(int(y - self.height() - 10), ag.bottom() - self.height()))
        self.move(px, py)
        self.show()
        self.raise_()

class PetWindow(QWidget):
    def _set_city_dialog(self):
        city, ok = QInputDialog.getText(
            self,
            "设置城市",
            "输入城市名:",
            QLineEdit.EchoMode.Normal,
            self.cfg.get("city", "汕头")
        )

        print("输入框结果:", city, ok)

        if ok and city.strip():
            self.cfg["city"] = city.strip()
            self._save_cfg()
            print("cfg现在:", self.cfg["city"])
            self.say(f"城市已设置为{city}")

    def __init__(self):
        self.cfg = load_json(CONFIG_PATH, {
            "mode": "wander",
            "size": 0.7,
            "topmost": True,
            "passthrough": False,
            "autostart": False,
            "x": None,
            "y": None,
            "ds_api_key": "",
            "city": "汕头"
    })
        
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.get("topmost", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("大肥鱼桌宠")
        
        # 精灵加载
        self.sprites = {}
        for label, mult in SIZE_LEVELS.items():
            h = int(340 * mult)
            for name in ["正面", "侧面", "背面"]:
                sized = os.path.join(SPRITE_DIR, f"{name}_{h}.png")
                if os.path.exists(sized):
                    pix = QPixmap(sized)
                else:
                    pix = QPixmap(os.path.join(SPRITE_DIR, f"{name}.png")).scaledToHeight(
                        h, Qt.TransformationMode.SmoothTransformation)
                self.sprites[(name, h)] = pix
        self.icon = QIcon(os.path.join(SPRITE_DIR, "icon.png"))

        self.cur_h = int(340 * self.cfg["size"])
        self.win_mx = int(self.cur_h * 0.062) + 6
        self.win_w = max(p.width() for k, p in self.sprites.items() if k[1] == self.cur_h) + self.win_mx * 2
        self.setFixedSize(self.win_w, self.cur_h + BUBBLE_H + MARGIN * 2 + 10)

        # 状态
        self.mode = self.cfg["mode"] if self.cfg["mode"] in ("wander", "follow", "still") else "wander"
        self.dir = "down"
        self.facing = 1
        self.target = None
        self.rest_until = 0
        self.cur_speed = 0.0
        self.prev_key = None
        self.cross_t = 0.0
        self.action = None
        self.action_t = 0.0
        self.bubble_text = ""
        self.bubble_until = 0
        self.bubble_inner = False
        self.last_speak_tick = 0
        self.last_system_check = 0
        self.t = 0
        self.jump_t = 0
        self.dragging = False
        self.drag_offset = None
        self.drag_start_pos = None
        self.last_line = ""
        self.last_press_pos = None
        self._dbl_clicked = False  # 双击标志：双击后不再触发单击面板
        self._press_on_pet = False  # 按下是否发生在鱼身上（防止外部窗口松手误触发单击）
        
        # AI 相关
        self.ds_busy = False
        self.chat_history = []  # 对话历史
        self.max_history = 40   # 最多记录40条
        self._say_queue = []    # 后台线程→主线程的气泡消息队列
        
        # 时段问候状态（新对话种类：按时段问候）
        self.last_greet_hour = None
        self.last_greet_tick = 0

        # 交互增强状态（采集自各开源桌宠工程：分区点击/三连击/打盹/粒子/快速拖拽）
        self._press_local = QPoint()          # 按下时的窗口内坐标（分区判定用）
        self._press_tick = 0                  # 按下的 tick（长按摸头判定）
        self._pat_hold_done = False           # 本次按下已触发长按摸头
        self._tap_times = []                  # 三连击探测时间戳
        self._just_woke = False               # 刚被唤醒（下一次单击说唤醒台词）
        self.sleeping = False                 # 打盹中
        self.blink_t = 0.0                    # 眨眼动画进度（1→0）
        self.next_blink_tick = random.randint(150, 450)  # 下次眨眼间隔
        self.spin_t = 0.0                     # 转圈动画进度（1→0）
        self.wobble_t = 0.0                   # 晕眩摇摆进度（1→0）
        self.hover_t = 0.0                    # 悬停摇摆进度（1→0）
        self.particles = []                   # 爱心/星星/音符粒子
        self.last_interact_tick = 0           # 最近一次互动（打盹/关心判定）
        self.last_feed_tick = 0               # 最近一次投喂
        self.last_care_check_tick = 0         # 关心检查节流
        self.last_care_long_sit = -10 ** 9    # 久坐提醒冷却
        self.last_care_hungry = -10 ** 9      # 饿了提醒冷却
        self.last_hover_speak_tick = -10 ** 9 # 悬停说话节流
        self._last_drag_fast = False          # 上次拖拽是否为快速拖拽
        self._drag_speed = 0.0                # 拖拽速度（平滑值）
        self._drag_prev = None                # 上次拖拽位置

        # 聊天暂停标志
        self.chat_paused = False
        
        # 功能列表
        self.chat_button = ChatButton(self)
        self.food_panel = FoodPanel(self.on_food)
        # 单击延迟判定（等双击）：单击=回嘴+弹聊天面板，双击=喂食
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)
        
        # 聊天对话框
        self.chat_dialog = ChatDialog(self)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(TICK)

        self.bubble_font = QFont("Microsoft YaHei UI", 11)
        self.fx_font = QFont("Microsoft YaHei UI", 12)  # 粒子特效字体

        # 托盘
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        x, y = self.cfg.get("x"), self.cfg.get("y")
        if x is None or y is None:
            screen = QApplication.primaryScreen().availableGeometry()
            x = screen.right() - self.width() - 80
            y = screen.bottom() - self.height() - 60
        self.move(int(x), int(y))
        self.show()
        self.snap_into_screen()
        if self.cfg.get("passthrough", False):
            self._apply_passthrough(True)

    # ---------- AI 方法 ----------
    def _call_ds(self, user_msg):
        if self.ds_busy:
            self.say("等等，上一句还没回完呢")
            return
        
        key = self.cfg.get("ds_api_key", "")
        if not key:
            self.say("请先在右键菜单里设置 DeepSeek Key！")
            return
        
        self.ds_busy = True
        
        # 构建消息列表
        messages = [{"role": "system", "content": DS_SYSTEM}]
        messages.extend(self.chat_history[-self.max_history:])
        messages.append({"role": "user", "content": user_msg})
        
        def worker():
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.9
            }
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=10)
                if resp.status_code == 200:
                    reply = resp.json()["choices"][0]["message"]["content"].strip()
                    if len(reply) > 30:
                        reply = reply[:28] + "…"
                    # 存入历史
                    self.chat_history.append({"role": "user", "content": user_msg})
                    self.chat_history.append({"role": "assistant", "content": reply})
                    if len(self.chat_history) > self.max_history:
                        self.chat_history = self.chat_history[-self.max_history:]
                    self._queue_say(reply)
                else:
                    error_msg = resp.json().get("error", {}).get("message", str(resp.status_code))
                    self._queue_say(f"API错误: {error_msg[:12]}")
                    print(f"[DeepSeek] 状态码: {resp.status_code}, 返回: {resp.text}")
            except requests.exceptions.Timeout:
                self._queue_say("请求超时，检查网络")
            except requests.exceptions.ConnectionError:
                self._queue_say("连接失败，检查网络")
            except Exception as e:
                self._queue_say(f"请求失败: {str(e)[:12]}")
            finally:
                self.ds_busy = False
        
        threading.Thread(target=worker, daemon=True).start()

    # ---------- 绘制 ----------
    def _bubble_geometry(self):
        """计算当前气泡的几何信息（绘制与聊天按钮定位共用）"""
        now = self.t * TICK / 1000.0
        if not (self.bubble_text and now < self.bubble_until):
            return None
        if self.bubble_inner:
            bfont = QFont(self.bubble_font)
            bfont.setItalic(True)
            bg, fg = QColor(232, 232, 238, 235), QColor(125, 125, 138)
        else:
            bfont = QFont(self.bubble_font)
            bg, fg = QColor(255, 255, 255, 235), QColor(60, 60, 80)
        fm = QFontMetrics(bfont)
        max_w = min(240, self.width() - 16)
        words = self.bubble_text
        lines = []
        cur = ""
        for ch in words:
            if fm.horizontalAdvance(cur + ch) > max_w - 20:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
        bw = max(fm.horizontalAdvance(l) for l in lines) + 20
        bh = len(lines) * fm.height() + 14
        bx = (self.width() - bw) / 2
        by = 6.0
        return (bx, by, bw, bh, lines, fm, bfont, bg, fg)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        now = self.t * TICK / 1000.0

        g = self._bubble_geometry()
        if g is not None:
            bx, by, bw, bh, lines, fm, bfont, bg, fg = g
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(QRectF(bx, by, bw, bh), 10, 10)
            tail = QPointF(self.width() / 2, by + bh)
            p.drawPolygon(QPolygonF([tail, QPointF(tail.x() - 6, tail.y() + 8), QPointF(tail.x() + 6, tail.y() + 8)]))
            p.setPen(fg)
            p.setFont(bfont)
            for i, l in enumerate(lines):
                p.drawText(QRectF(bx, by + 7 + i * fm.height(), bw, fm.height()),
                           Qt.AlignmentFlag.AlignCenter, l)

        cx = self.width() / 2
        walking = self.target is not None and not self.dragging
        if walking:
            sway = math.sin(now * 9.0) * 3.5
            bob = -abs(math.sin(now * 4.5)) * 7.0
        else:
            sway = math.sin(now * 2.5) * 1.5
            bob = 0.0
        if self.sleeping:
            # 打盹：呼吸更慢、身体略缩小
            breath = 1.0 - 0.015 * math.sin(now * 1.2) - 0.03
        else:
            breath = 1.0 + 0.02 * math.sin(now * 2.5)
        scale = breath
        jump = -abs(math.sin(self.jump_t * 3.14159)) * 14 * self.jump_t if self.jump_t > 0 else 0
        act_rot = act_sx = act_sy = 0.0
        if self.action == "sway":
            act_rot = math.sin(self.action_t * 3.14159 * 2) * 10 * self.action_t
        elif self.action == "stretch":
            act_sy = 0.06 * math.sin(self.action_t * 3.14159)
            act_sx = -0.03 * math.sin(self.action_t * 3.14159)
        # 新增动态效果：眨眼（纵向压扁）/ 转圈 / 晕眩摇摆 / 悬停摇摆
        blink_sy = 1.0 - 0.12 * min(1.0, self.blink_t)
        spin_deg = (1.0 - self.spin_t) * 360.0 if self.spin_t > 0 else 0.0
        wobble_deg = math.sin(self.wobble_t * math.pi * 5) * 14 * self.wobble_t if self.wobble_t > 0 else 0.0
        hover_deg = math.sin(self.hover_t * math.pi * 3) * 8 * self.hover_t if self.hover_t > 0 else 0.0

        def draw_one(key, opacity):
            if key is None:
                return
            name, h, facing = key
            pix = self.sprites[(name, h)]
            ph = pix.height() * scale * (1 + act_sy) * blink_sy
            pw = pix.width() * scale * (1 + act_sx)
            dx = cx - pw / 2
            bottom = BUBBLE_H + MARGIN + self.cur_h
            dy = bottom - ph + jump + bob
            p.save()
            p.setOpacity(opacity)
            p.translate(cx, bottom)
            p.rotate(sway + act_rot + spin_deg + wobble_deg + hover_deg)
            p.translate(-cx, -bottom)
            if facing < 0:
                p.translate(cx, 0)
                p.scale(-1, 1)
                p.translate(-cx, 0)
            p.drawPixmap(QRectF(dx, dy, pw, ph), pix, QRectF(0, 0, pix.width(), pix.height()))
            p.restore()

        cur_key = self._sprite_key()
        if self.cross_t > 0:
            draw_one(self.prev_key, self.cross_t)
            draw_one(cur_key, 1.0 - self.cross_t)
        else:
            draw_one(cur_key, 1.0)

        # 爱心/星星/音符粒子（动态图片显示：飘起 + 淡出）
        if self.particles:
            p.setFont(self.fx_font)
            for pt in self.particles:
                alpha = max(0.0, min(1.0, pt["life"] / pt["max_life"]))
                p.setOpacity(alpha)
                p.setPen(pt["color"])
                p.drawText(QPointF(pt["x"], pt["y"]), pt["glyph"])
            p.setOpacity(1.0)

    def _sprite_key(self):
        name = {"left": "侧面", "right": "侧面", "up": "背面", "down": "正面"}[self.dir]
        return (name, self.cur_h, self.facing if self.dir in ("left", "right") else 1)

    def _set_dir(self, d, facing=None):
        if d != self.dir:
            self.prev_key = self._sprite_key()
            self.cross_t = 1.0
            self.dir = d
        if facing is not None and facing != self.facing:
            self.facing = facing

    # ---------- 逻辑 ----------
    def tick(self):
        self.t += 1

        # 处理后台线程（DeepSeek 等）排队的气泡消息，Qt 界面必须在主线程更新
        if self._say_queue:
            for text in self._say_queue:
                self.say(text)
            self._say_queue.clear()

        self.check_system_status()
        self._maybe_time_greeting()
        
        if self.jump_t > 0:
            self.jump_t = max(0.0, self.jump_t - 0.06)
        if self.cross_t > 0:
            self.cross_t = max(0.0, self.cross_t - 0.15)
        if self.action_t > 0:
            self.action_t = max(0.0, self.action_t - 0.03)
            if self.action_t == 0:
                self.action = None

        # 新增：眨眼/转圈/摇摆/悬停/粒子/打盹（每帧都推进，暂停聊天时也要播完）
        self._update_effects()
        # 主动关心（久坐/饿了）：每 10 秒检查一次
        if self.t - self.last_care_check_tick >= 500:
            self.last_care_check_tick = self.t
            self._check_care()
        
        if self.chat_paused:
            self.update()
            return
        
        if self.dragging:
            self.update()
            return
        now_ms = self.t * TICK

        if self.mode == "follow":
            cursor = self.cursor().pos()
            screen = QApplication.screenAt(cursor) or self.screen() or QApplication.primaryScreen()
            geo = screen.availableGeometry()
            near = (self.x() - 100 <= cursor.x() <= self.x() + self.width() + 100 and
                    self.y() - 100 <= cursor.y() <= self.y() + self.height() + 100)
            if near:
                self.target = None
            else:
                tx = max(geo.left(), min(geo.right() - self.width(), cursor.x() - self.width() / 2))
                ty = max(geo.top(), min(geo.bottom() - self.height(), cursor.y() - 90))
                self.target = (tx, ty)
        elif self.mode == "wander":
            if self.target is None:
                if now_ms < self.rest_until:
                    self._maybe_idle_action()
                    self.update()
                    return
                geo = (self.screen() or QApplication.primaryScreen()).availableGeometry()
                self.target = (random.randint(geo.left() + 40, geo.right() - self.width() - 40),
                               random.randint(geo.top() + 40, geo.bottom() - self.height() - 40))
        else:
            self._maybe_idle_action()
            self.update()
            return

        if self.target is not None:
            cx, cy = self.x() + self.width() / 2, self.y() + self.height() / 2
            dx, dy = self.target[0] - cx, self.target[1] - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 12:
                self.target = None
                self.rest_until = self.t * TICK + random.randint(8000, 18000)
                self._set_dir("down")
            else:
                step = self.cur_speed * TICK / 1000.0
                nx, ny = cx + dx / dist * step, cy + dy / dist * step
                self.move(int(nx - self.width() / 2), int(ny - self.height() / 2))
                if abs(dx) > abs(dy) * 1.15:
                    self._set_dir("left" if dx < 0 else "right", 1 if dx < 0 else -1)
                else:
                    self._set_dir("up" if dy < 0 else "down")
            if random.random() < 0.002 and self.jump_t == 0:
                self.jump_t = 0.5
        target_speed = SPEED if self.target is not None else 0.0
        self.cur_speed += (target_speed - self.cur_speed) * 0.3
        self.update()

    def _maybe_idle_action(self):
        if random.random() < 0.01:
            pick = random.random()
            if pick < 0.35:
                self.jump_t = 1.0
            elif pick < 0.6:
                self.action, self.action_t = "sway", 1.0
            elif pick < 0.8:
                self.action, self.action_t = "stretch", 1.0
            elif pick < 0.9:
                if self.t - self.last_speak_tick >= 1500:
                    self.last_speak_tick = self.t
                    r = random.random()
                    if r < 0.15:
                        self.say(random.choice(LINES))
                    elif r < 0.55:
                        self.say(random.choice(INNER_LINES), inner=True)
                    elif r < 0.75:
                        self.say(random.choice(JOKES))
                    else:
                        self.say(random.choice(SELF_TALK))

    def _maybe_time_greeting(self):
        """按时段问候（早/午/晚/深夜）：每小时最多一次，空闲且无气泡时触发"""
        hour = int(time.strftime("%H"))
        if self.last_greet_hour == hour:
            return
        if self.chat_paused or self.dragging:
            return
        if self.t - self.last_greet_tick < 600:  # 启动后至少 12 秒再问候
            return
        now = self.t * TICK / 1000.0
        if self.bubble_text and now < self.bubble_until:
            return
        self.last_greet_hour = hour
        self.last_greet_tick = self.t
        for start, end, lines in TIME_LINES:
            if start <= hour < end:
                self.say(random.choice(lines))
                return

    def _queue_say(self, text):
        """后台线程调用：只入队，由主线程 tick 统一弹出显示（线程安全）"""
        self._say_queue.append(text)

    def say(self, text, inner=False):
        if text == self.last_line and not text.startswith("天气"):
            return
        self.last_line = text
        self.bubble_inner = inner
        self.bubble_text = f"（{text}）" if inner else text
        self.bubble_until = self.t * TICK / 1000.0 + BUBBLE_DURATION
        self.update()

    def check_system_status(self):
            now = self.t * TICK

            if now - getattr(self, "last_system_check", 0) < 10000:
                return

            self.last_system_check = now

            cpu = psutil.cpu_percent()

            if cpu >= 90:
                self.say("CPU跑满了，再这样下去我就卡死了")
                return

            ram = psutil.virtual_memory().percent

            if ram >= 95:
                self.say("内存爆了，快关掉几个没用的东西吧，注意，别把我关了")
                return

            if GPU_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)

                    temp = pynvml.nvmlDeviceGetTemperature(
                        handle,
                        pynvml.NVML_TEMPERATURE_GPU
                    )

                    if temp > 80:
                        self.say("我感觉我的鱼鳍快熟了")

                except Exception as e:
                    print("GPU读取失败:", e)

    # ---------- 鼠标事件 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_on_pet = True
            self._press_local = e.position().toPoint()
            self._press_tick = self.t
            self._pat_hold_done = False
            self.last_interact_tick = self.t
            self._wake_up()  # 点一下就把打盹的鱼叫醒
            self.last_press_pos = e.globalPosition().toPoint()
            self.dragging = False
            self.drag_start_pos = e.globalPosition().toPoint()
            self._drag_prev = e.globalPosition().toPoint()
            self._drag_speed = 0.0
            self.chat_button.hide()
            self.chat_dialog.hide()
            self.chat_paused = True

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos is not None:
            delta = e.globalPosition().toPoint() - self.drag_start_pos
            # 拖拽速度（平滑），用于区分快速拖拽/慢速拖拽
            if self._drag_prev is not None:
                step = (e.globalPosition().toPoint() - self._drag_prev).manhattanLength()
                self._drag_speed = self._drag_speed * 0.7 + step * 0.3
            self._drag_prev = e.globalPosition().toPoint()
            if not self.dragging and delta.manhattanLength() > 6:
                self.dragging = True
                self.drag_offset = e.globalPosition().toPoint() - QPoint(self.x(), self.y())
            if self.dragging and self.drag_offset is not None:
                pos = e.globalPosition().toPoint() - self.drag_offset
                self.move(pos)
                if abs(delta.x()) > 10:
                    self._set_dir("left" if delta.x() < 0 else "right", 1 if delta.x() < 0 else -1)
                self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            pressed_on_pet = self._press_on_pet
            self._press_on_pet = False
            self.last_interact_tick = self.t
            if self.dragging:
                self.dragging = False
                self.drag_offset = None
                self.drag_start_pos = None
                self._set_dir("down", 1)
                self.target = None
                self.rest_until = self.t * TICK + random.randint(6000, 14000)
                # 快速拖拽 → 专属台词 + 晕眩摇摆；慢速拖拽 → 普通台词
                self._last_drag_fast = self._drag_speed >= 20.0
                if self._last_drag_fast:
                    self.wobble_t = 1.0
                    self._spawn_fx("heart", 2)
                    self.say(self._pick_line(DRAG_FAST_LINES))
                elif random.random() < 0.5:
                    self.say(random.choice(DRAG_LINES))
                self.chat_paused = False
            elif pressed_on_pet and not self._dbl_clicked:
                held = (self.t - self._press_tick) * TICK / 1000.0
                if held >= 0.6:
                    # 长按 = 摸头（不弹聊天按钮）
                    self._pat_hold_done = True
                    self._on_pat_hold()
                elif not self._register_tap():
                    self._click_timer.start(280)  # 等双击判定；单击则回嘴+弹聊天面板
            self._dbl_clicked = False
            self.last_press_pos = None
            self.drag_start_pos = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dbl_clicked = True
            self._click_timer.stop()
            self._tap_times.clear()  # 双击不算三连击
            self._spawn_fx("note", 2)
            self.chat_paused = False  # 喂食面板不暂停鱼
            self.food_panel.popup_at(self.x() + self.width() / 2, self.y() + BUBBLE_H)

    def _pick_line(self, lines):
        """选一句与上次不同的台词（避免 say 去重导致气泡不显示）"""
        cands = [l for l in lines if l != self.last_line]
        return random.choice(cands) if cands else random.choice(lines)

    # ---------- 交互增强（分区点击 / 三连击 / 摸头 / 打盹 / 粒子） ----------
    def _zone_at(self, pos):
        """按窗口内坐标判定点击落在：头 / 肚子 / 尾巴（尾巴在右下方）"""
        if pos is None:
            return "head"
        nx = pos.x() / max(1, self.width())
        ny = (pos.y() - BUBBLE_H - MARGIN) / max(1, self.cur_h)
        ny = min(1.0, max(0.0, ny))
        if ny < 0.42:
            return "head"
        if nx > 0.62 and ny > 0.55:
            return "tail"
        return "belly"

    def _register_tap(self):
        """记录一次轻点；1.2 秒内点满 3 下触发转圈庆祝（不弹聊天按钮）"""
        now_ms = self.t * TICK
        self._tap_times.append(now_ms)
        while self._tap_times and now_ms - self._tap_times[0] > 1200:
            self._tap_times.pop(0)
        if len(self._tap_times) >= 3:
            self._tap_times.clear()
            self._on_triple()
            return True
        return False

    def _on_triple(self):
        """三连击庆祝：转圈 + 星星/爱心粒子 + 专属台词"""
        self.jump_t = 1.0
        self.spin_t = 1.0
        self._spawn_fx("star", 5)
        self._spawn_fx("heart", 3)
        self.say(self._pick_line(TRIPLE_LINES))
        self.chat_paused = False

    def _on_pat_hold(self):
        """长按摸头：爱心粒子 + 摸头台词"""
        self._spawn_fx("heart", 3)
        self.say(self._pick_line(PAT_HOLD_LINES))
        self.jump_t = 0.4
        self.chat_paused = False

    def _start_nap(self):
        """打盹：无互动一段时间后进入睡眠（点一下就会醒）"""
        if self.sleeping:
            return
        self.sleeping = True
        self.say(random.choice(SLEEP_LINES))

    def _wake_up(self):
        """从打盹中醒来（点击/拖动时调用）"""
        if not self.sleeping:
            return
        self.sleeping = False
        self._just_woke = True
        self.jump_t = 0.6

    def _on_hover(self):
        """鼠标悬停在鱼身上：轻微摇摆，偶尔打个招呼"""
        self.hover_t = 1.0
        self.last_interact_tick = self.t
        if self.t - self.last_hover_speak_tick > 3000 and random.random() < 0.25:
            self.last_hover_speak_tick = self.t
            self.say(self._pick_line(HOVER_LINES))

    def enterEvent(self, e):
        self._on_hover()
        super().enterEvent(e)

    def _spawn_fx(self, kind, count=2):
        """生成爱心/星星/音符粒子（从鱼身中上部飘起并淡出）"""
        glyph = FX_GLYPHS.get(kind, "♥")
        color = FX_COLORS.get(kind, QColor(255, 107, 138))
        cx = self.width() / 2
        base_y = BUBBLE_H + MARGIN + self.cur_h * 0.55
        for _ in range(max(1, count)):
            life = random.randint(40, 70)
            self.particles.append({
                "x": cx + random.uniform(-30, 30),
                "y": base_y + random.uniform(-24, 24),
                "vx": random.uniform(-1.2, 1.2),
                "vy": random.uniform(-3.4, -1.8),
                "life": life,
                "max_life": life,
                "glyph": glyph,
                "color": color,
            })
        self.particles = self.particles[-60:]

    def _tick_particles(self):
        if not self.particles:
            return
        alive = []
        for pt in self.particles:
            pt["life"] -= 1
            if pt["life"] <= 0:
                continue
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vy"] -= 0.06  # 越飘越快
            alive.append(pt)
        self.particles = alive

    def _trigger_blink(self):
        """触发一次眨眼（纵向压扁一下，视觉上像闭眼）"""
        self.blink_t = 1.0

    def _update_effects(self):
        """每帧推进：眨眼 / 转圈 / 摇摆 / 悬停 / 粒子 / 打盹"""
        # 眨眼
        if self.blink_t > 0:
            self.blink_t = max(0.0, self.blink_t - 0.34)
        self.next_blink_tick -= 1
        if self.next_blink_tick <= 0 and self.blink_t == 0 and not self.chat_paused and not self.sleeping:
            self._trigger_blink()
            self.next_blink_tick = random.randint(150, 450)
        # 转圈 / 摇摆 / 悬停
        if self.spin_t > 0:
            self.spin_t = max(0.0, self.spin_t - 0.05)
        if self.wobble_t > 0:
            self.wobble_t = max(0.0, self.wobble_t - 0.05)
        if self.hover_t > 0:
            self.hover_t = max(0.0, self.hover_t - 0.06)
        # 粒子
        self._tick_particles()
        # 打盹：60 秒无互动进入睡眠（聊天/拖拽时不睡）
        if (not self.sleeping and not self.chat_paused and not self.dragging
                and self.t - self.last_interact_tick > 3000 and self.t > 3100):
            self._start_nap()

    def _check_care(self):
        """主动关心：久坐提醒（25 分钟无互动）/ 饿了提醒（30 分钟没投喂）"""
        if self.sleeping or self.chat_paused or self.dragging:
            return
        now = self.t
        if now - self.last_interact_tick >= 75000 and now - self.last_care_long_sit >= 90000:
            self.last_care_long_sit = now
            self._spawn_fx("note", 2)
            self.say(self._pick_line(CARE_LINES["long_sit"]))
            return
        if now - self.last_feed_tick >= 90000 and now - self.last_care_hungry >= 360000:
            self.last_care_hungry = now
            self.say(self._pick_line(CARE_LINES["hungry"]))

    def do_spin(self):
        """菜单「转个圈」：转圈 + 星星粒子"""
        self.spin_t = 1.0
        self.jump_t = 0.6
        self._spawn_fx("star", 4)
        self.last_interact_tick = self.t
        self.say(self._pick_line(SPIN_LINES))

    def toggle_nap(self):
        """菜单「打个盹 / 醒醒」"""
        if self.sleeping:
            self.sleeping = False
            self._just_woke = True
            self.jump_t = 0.6
            self.say(self._pick_line(WAKE_LINES))
        else:
            self._start_nap()

    def do_play(self):
        """菜单「一起玩」：蹦跳 + 转圈 + 音符粒子"""
        self.jump_t = 1.0
        self.spin_t = 1.0
        self._spawn_fx("note", 4)
        self.last_interact_tick = self.t
        self.say(self._pick_line(PLAY_LINES))

    def say_random(self):
        """菜单「说句话」：随机说一句台词"""
        self.last_interact_tick = self.t
        self.say(self._pick_line(LINES + REACT_LINES))

    def _on_single_click(self):
        """单击：蹦跳回嘴 + 气泡右侧弹出聊天按钮（不想聊点鱼身外即可）"""
        if random.random() < 0.7:
            self.jump_t = 1.0
        self.last_interact_tick = self.t
        if self._just_woke:
            # 刚从打盹中被点醒：说唤醒台词
            self._just_woke = False
            self.say(self._pick_line(WAKE_LINES))
        else:
            # 按点击位置分区（头/肚子/尾巴），在气泡里冒对应台词 + 粒子特效
            zone = self._zone_at(self._press_local)
            self._spawn_fx(FX_GLYPH_BY_ZONE.get(zone, "heart"), 2)
            if random.random() < 0.45:
                self.say(self._pick_line(PET_LINES.get(zone, REACT_LINES)))
            else:
                self.say(self._pick_line(REACT_LINES))  # 必定回嘴，避免"点击没反应"
        # 按钮隐藏时刻与气泡过期时刻对齐（气泡剩余时间），两者同步消失
        remaining_ms = int((self.bubble_until - self.t * TICK / 1000.0) * 1000)
        remaining_ms = max(1000, remaining_ms)  # 至少保留 1 秒点击窗口
        g = self._bubble_geometry()
        if g is not None:
            bx, by, bw, bh = g[:4]
            # 按钮放在气泡右侧、垂直居中：不遮挡鱼身，也避免对话框弹出时按钮区域被盖住
            btn_x = self.x() + bx + bw + 6
            btn_y = self.y() + by + (bh - self.chat_button.height()) / 2
        else:
            btn_x = self.x() + self.width() - self.chat_button.width() - 8
            btn_y = self.y() + 8
        self.chat_button.popup_at(btn_x, btn_y, hide_after_ms=remaining_ms)
        self.chat_paused = True  # 按钮交互期间鱼暂停移动

    def on_food(self, food):
        self.food_panel.hide()
        self.eat_t = 1.0
        self.jump_t = 0.6
        self.chat_paused = False  # 喂食后恢复移动
        self.last_feed_tick = self.t
        self.last_interact_tick = self.t
        self._spawn_fx("note", 4)  # 投喂时冒音符粒子
        lines = FOOD_LINES.get(food, ["好吃！"])
        self.say(random.choice(lines))

    def _show_chat_dialog(self):
        key = self.cfg.get("ds_api_key", "")
        if not key:
            # 未设置 Key：直接弹出设置框（可输入），设置成功后自动打开聊天
            self.chat_button.hide()
            self.chat_paused = False
            self._set_key_dialog()
            if self.cfg.get("ds_api_key", ""):
                self._show_chat_dialog()
            return
        self.chat_paused = True  # 聊天期间鱼暂停移动（关闭对话框后恢复）
        self.chat_dialog.popup_at(
            self.x() + self.width() / 2,
            self.y() + BUBBLE_H
        )

    """def _get_city_by_ip(self):
        try:
            r = requests.get("http://ip-api.com/json/?fields=city&lang=zh-CN", timeout=5)
            if r.status_code == 200:
                city = r.json().get("city", "")
                if city:
                    return city
        except:
            pass
        return "汕头" """

    def _get_weather(self):
        try:
            city = self.cfg.get("city", "汕头")
            print("当前城市:", city)

            url = f"https://wttr.in/{city}?format=j1"

            r = requests.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            print("状态:", r.status_code)
            print(r.text[:500])

            data = r.json()

            weather = data["current_condition"][0]

            temp = weather["temp_C"]

            weather_map = {
                "Sunny": "晴",
                "Clear": "晴",
                "Partly cloudy": "多云",
                "Cloudy": "阴",
                "Light rain": "小雨",
                "Moderate rain": "中雨",
                "Heavy rain": "大雨"
            }

            raw_weather = weather["weatherDesc"][0]["value"]

            desc = weather_map.get(raw_weather, raw_weather)

            self.say(f"{city}今天{temp}°，天气{desc}")

        except Exception as e:
            print("天气错误:", repr(e))
            self.say("天气获取失败")
    

    def _build_menu(self):
        m = QMenu(self)
        mode_menu = m.addMenu("模式")
        for label, key in [("自由散步", "wander"), ("跟随鼠标", "follow"), ("原地待着", "still")]:
            a = mode_menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.mode == key)
            a.triggered.connect(lambda _, k=key: self.set_mode(k))
        size_menu = m.addMenu("大小")
        for label, mult in SIZE_LEVELS.items():
            a = size_menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(abs(self.cur_h - 340 * mult) < 2)
            a.triggered.connect(lambda _, v=mult: self.set_size(v))
        m.addAction("转个圈", self.do_spin)
        m.addAction("打个盹", self.toggle_nap)
        m.addAction("一起玩", self.do_play)
        m.addAction("说句话", self.say_random)
        m.addAction("设置 Key", self._set_key_dialog)
        m.addAction("查看天气", self._get_weather)
        m.addSeparator()
        m.addAction("显示/隐藏", self.toggle_visible)
        m.addAction("回到屏幕内", self.snap_into_screen)
        pa = m.addAction("鼠标穿透（点不到它）")
        pa.setCheckable(True)
        pa.setChecked(self.cfg["passthrough"])
        pa.triggered.connect(lambda on: self.set_passthrough(on))
        ta = m.addAction("窗口置顶")
        ta.setCheckable(True)
        ta.setChecked(self.cfg["topmost"])
        ta.triggered.connect(lambda on: self.set_topmost(on))
        aa = m.addAction("开机自启")
        aa.setCheckable(True)
        aa.setChecked(self.cfg["autostart"])
        aa.triggered.connect(lambda on: self.set_autostart(on))
        m.addSeparator()
        m.addAction("退出", self.quit_app)
        return m

    def _set_key_dialog(self):
        key, ok = QInputDialog.getText(
            self, 
            "设置 DeepSeek Key", 
            "输入你的 API Key（从 platform.deepseek.com 获取）:",
            QLineEdit.EchoMode.Normal,
            self.cfg.get("ds_api_key", "")
        )
        if ok and key.strip():
            self.cfg["ds_api_key"] = key.strip()
            self._save_cfg()
            self.say("Key 设置成功！")
        elif ok and not key.strip():
            self.say("Key 不能为空")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            self.tray.setContextMenu(self._build_menu())
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visible()

    def contextMenuEvent(self, e):
        self._build_menu().exec(e.globalPos())

    # ---------- 功能 ----------
    def set_mode(self, mode):
        self.mode = mode
        self.target = None
        self.cfg["mode"] = mode
        self._save_cfg()

    def set_size(self, mult):
        self.cur_h = int(340 * mult)
        self.cfg["size"] = mult
        self.cross_t = 0.0
        self.prev_key = None
        self.win_mx = int(self.cur_h * 0.062) + 6
        self.win_w = max(p.width() for k, p in self.sprites.items() if k[1] == self.cur_h) + self.win_mx * 2
        self.setFixedSize(self.win_w, self.cur_h + BUBBLE_H + MARGIN * 2 + 10)
        self.snap_into_screen()
        self._save_cfg()

    def snap_into_screen(self):
        geo = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        x = max(geo.left(), min(geo.right() - self.width(), self.x()))
        y = max(geo.top(), min(geo.bottom() - self.height(), self.y()))
        self.move(x, y)

    def _apply_passthrough(self, on):
        hwnd = int(self.winId())
        GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT = -20, 0x80000, 0x20
        style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style | WS_EX_LAYERED
        if on:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)

    def set_passthrough(self, on):
        self.cfg["passthrough"] = bool(on)
        self._apply_passthrough(bool(on))
        if on:
            self.say("我隐身了！右键托盘图标解除～")
        self._save_cfg()

    def set_topmost(self, on):
        self.cfg["topmost"] = bool(on)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(on))
        self.show()
        self._save_cfg()

    def set_autostart(self, on):
        self.cfg["autostart"] = bool(on)
        lnk = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows",
                           "Start Menu", "Programs", "Startup", "大肥鱼桌宠.lnk")
        try:
            if on:
                ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{}');"
                      "$s.TargetPath='{}';$s.Arguments='\"{}\"';$s.WorkingDirectory='{}';$s.Save()"
                      .format(lnk, PYTHONW,
                              "" if getattr(sys, "frozen", False) else os.path.join(APP_DIR, "桌宠.py"),
                              APP_DIR))
                subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=True)
                self.say("已开机自启，明天见～")
            else:
                if os.path.exists(lnk):
                    os.remove(lnk)
                self.say("已取消开机自启")
        except Exception as ex:
            QMessageBox.warning(self, "开机自启", f"设置失败：{ex}")
        self._save_cfg()

    def _save_cfg(self):
        """立即把当前配置写入 config.json（设置变更即保存，异常退出也不丢失）"""
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("配置保存失败:", e)

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def quit_app(self):
        self.cfg["x"], self.cfg["y"] = self.x(), self.y()
        self._save_cfg()
        self.tray.hide()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = PetWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "大肥鱼桌宠出错", str(ex))
        except Exception:
            pass
        raise