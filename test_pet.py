# -*- coding: utf-8 -*-
"""桌宠.py 基础功能自动化测试（PySide6.QtTest 模拟真实鼠标/键盘事件）
运行：python test_pet.py
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
pet_mod = importlib.import_module("桌宠")

from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint, QTimer

# 备份 config.json：测试中 set_mode/set_size/Key 设置会立即写配置，结束后恢复，避免污染用户配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
_CONFIG_BACKUP = None
if os.path.exists(_CONFIG_PATH):
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _CONFIG_BACKUP = f.read()

app = pet_mod.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

pet = pet_mod.PetWindow()
pet.set_mode("still")          # 冻结散步，便于断言
pet.cfg["ds_api_key"] = "sk-test-fake"  # 主流程用假 Key，跳过设置框
pet.show()
QTest.qWait(400)

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))

CENTER = QPoint(pet.width() // 2, pet.height() // 2)

# ---------- 1. 单击：气泡 + 聊天按钮 + 暂停 ----------
QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(500)
check("单击弹出气泡台词", bool(pet.bubble_text), pet.bubble_text)
check("单击弹出聊天按钮", pet.chat_button.isVisible())
check("按钮出现时鱼暂停", pet.chat_paused is True)

# ---------- 2. 点击按钮 → 聊天对话框打开、可聚焦、可输入 ----------
QTest.mouseClick(pet.chat_button, Qt.MouseButton.LeftButton)
QTest.qWait(350)
check("点击按钮打开聊天对话框", pet.chat_dialog.isVisible())
fw = app.focusWidget()
check("输入框获得焦点", fw is pet.chat_dialog.input, str(fw) if fw else "no focus widget")
QTest.keyClicks(pet.chat_dialog.input, "hello")
QTest.qWait(50)
check("对话框可输入文字", pet.chat_dialog.input.text() == "hello", pet.chat_dialog.input.text())
check("聊天期间鱼暂停", pet.chat_paused is True)

# ---------- 3. ESC 关闭对话框 → 恢复移动 ----------
QTest.keyClick(pet.chat_dialog, Qt.Key.Key_Escape)
QTest.qWait(150)
check("ESC 关闭对话框", not pet.chat_dialog.isVisible())
check("关闭后鱼恢复移动", pet.chat_paused is False)

# ---------- 4. 气泡与聊天按钮同步消失 ----------
QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(500)
check("再次单击按钮出现", pet.chat_button.isVisible())
QTest.qWait(2000)   # 到 2.5s：气泡与按钮应同时还在
check("气泡到期前仍在显示", pet._bubble_geometry() is not None)
check("按钮与气泡同步仍显示", pet.chat_button.isVisible())
QTest.qWait(2600)   # 到 ~5.1s：气泡（显示 4.8s）与按钮应同时消失
check("气泡与按钮同步消失", pet._bubble_geometry() is None and not pet.chat_button.isVisible())
check("同步消失后鱼恢复移动", pet.chat_paused is False)

# ---------- 5. 双击 → 喂食面板（且不残留聊天按钮） ----------
QTest.mouseDClick(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(250)
check("双击弹出喂食面板", pet.food_panel.isVisible())
check("双击后无聊天按钮残留", not pet.chat_button.isVisible())
food_btns = [b for b in pet.food_panel.findChildren(pet_mod.QToolButton) if b.text() in pet_mod.FOODS]
check("喂食面板有食物按钮", len(food_btns) == len(pet_mod.FOODS), str(len(food_btns)))
QTest.mouseClick(food_btns[0], Qt.MouseButton.LeftButton)
QTest.qWait(150)
check("选择食物后面板关闭", not pet.food_panel.isVisible())
check("喂食有回应台词", bool(pet.bubble_text), pet.bubble_text)
check("喂食后鱼恢复移动", pet.chat_paused is False)

# ---------- 6. 拖拽：位置变化 + 松手恢复 ----------
pos0 = pet.pos()
QTest.mousePress(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.mouseMove(pet, QPoint(CENTER.x() + 40, CENTER.y() + 40))
QTest.qWait(60)
QTest.mouseMove(pet, QPoint(CENTER.x() + 80, CENTER.y() + 80))
QTest.qWait(60)
QTest.mouseRelease(pet, Qt.MouseButton.LeftButton, pos=QPoint(CENTER.x() + 80, CENTER.y() + 80))
QTest.qWait(150)
check("拖拽后位置变化", pet.pos() != pos0, f"{pos0} -> {pet.pos()}")
check("拖拽松手后鱼恢复移动", pet.chat_paused is False)

# ---------- 7. 右键菜单结构 ----------
menu = pet._build_menu()
top = [a.text() for a in menu.actions()]
sub = [a.text() for sm in menu.findChildren(pet_mod.QMenu) for a in sm.actions()]
all_items = top + sub
for need in ("模式", "大小", "设置 Key", "查看天气", "显示/隐藏", "鼠标穿透（点不到它）",
             "窗口置顶", "开机自启", "退出", "自由散步", "跟随鼠标", "原地待着",
             "转个圈", "打个盹", "一起玩", "说句话"):
    check(f"菜单含「{need}」", need in all_items)
menu.close()

# ---------- 8. 模式 / 大小切换 ----------
pet.set_mode("follow")
check("切换到跟随模式", pet.mode == "follow")
pet.set_mode("wander")
check("切换到散步模式", pet.mode == "wander")
pet.set_size(0.55)
check("切换小尺寸", pet.cur_h == int(340 * 0.55), str(pet.cur_h))
pet.set_size(0.7)
check("切回中尺寸", pet.cur_h == int(340 * 0.7), str(pet.cur_h))

# ---------- 9. 未设置 Key 时：自动弹出 Key 设置框，设置后打开聊天 ----------
pet.chat_dialog.hide()
pet.cfg["ds_api_key"] = ""
def auto_fill_key():
    dlg = app.activeModalWidget()
    if dlg is not None:
        le = dlg.findChild(pet_mod.QLineEdit)
        if le is not None:
            le.setText("sk-auto-123")
        dlg.accept()
QTimer.singleShot(400, auto_fill_key)
pet._show_chat_dialog()
QTest.qWait(400)
check("无 Key 时自动弹出设置框并填入", pet.cfg["ds_api_key"] == "sk-auto-123", pet.cfg["ds_api_key"])
check("设置 Key 后聊天对话框打开", pet.chat_dialog.isVisible())
check("聊天输入框可聚焦", app.focusWidget() is pet.chat_dialog.input)
QTest.keyClick(pet.chat_dialog, Qt.Key.Key_Escape)
QTest.qWait(120)

# ---------- 10. 对话框失去鼠标焦点 5 秒自动消失，桌宠恢复自动运行 ----------
pet.cfg["ds_api_key"] = "sk-test-fake"
pet._show_chat_dialog()
QTest.qWait(300)
check("聊天对话框打开", pet.chat_dialog.isVisible())
check("对话框打开时鱼暂停", pet.chat_paused is True)
# 模拟失去焦点（点击窗口外）
pet.chat_dialog.event(pet_mod.QEvent(pet_mod.QEvent.Type.WindowDeactivate))
QTest.qWait(5300)
check("失焦 5 秒后对话框自动消失", not pet.chat_dialog.isVisible())
check("对话框消失后鱼恢复自动运行", pet.chat_paused is False)

# 失焦后重新获得焦点 → 不消失
pet._show_chat_dialog()
QTest.qWait(200)
pet.chat_dialog.event(pet_mod.QEvent(pet_mod.QEvent.Type.WindowDeactivate))
QTest.qWait(800)
pet.chat_dialog.event(pet_mod.QEvent(pet_mod.QEvent.Type.WindowActivate))
QTest.qWait(5300)
check("重新获焦后对话框不消失", pet.chat_dialog.isVisible())
pet.chat_dialog.hide()
QTest.qWait(100)
check("手动关闭后鱼恢复自动运行", pet.chat_paused is False)

# ---------- 11. 互动增强：分区点击 / 三连击 / 眨眼 / 打盹 / 粒子 / 快速拖拽 / 关心 ----------
pet.set_mode("still")
pet.sleeping = False
pet.chat_paused = False
pet.last_interact_tick = pet.t
QTest.qWait(100)

# 分区判定（头 / 肚子 / 尾巴）
head_pt = QPoint(pet.width() // 2, pet_mod.BUBBLE_H + pet_mod.MARGIN + 8)
belly_pt = QPoint(pet.width() // 2, pet_mod.BUBBLE_H + pet_mod.MARGIN + int(pet.cur_h * 0.6))
tail_pt = QPoint(int(pet.width() * 0.85), pet_mod.BUBBLE_H + pet_mod.MARGIN + int(pet.cur_h * 0.7))
check("分区：头部", pet._zone_at(head_pt) == "head", pet._zone_at(head_pt))
check("分区：肚子", pet._zone_at(belly_pt) == "belly", pet._zone_at(belly_pt))
check("分区：尾巴", pet._zone_at(tail_pt) == "tail", pet._zone_at(tail_pt))

# 粒子特效：生成 → 随时间消散
pet.particles.clear()
pet._spawn_fx("heart", 4)
check("点击产生爱心粒子", len(pet.particles) == 4, str(len(pet.particles)))
for _ in range(90):
    pet._tick_particles()
check("粒子会随时间消散", len(pet.particles) == 0, str(len(pet.particles)))

# 三连击：1.2 秒内三次轻点 → 转圈庆祝 + 台词
pet.spin_t = 0.0
pet.bubble_text = ""
now_ms = pet.t * pet_mod.TICK
pet._tap_times = [now_ms - 300, now_ms - 150]
check("三连击触发转圈", pet._register_tap() and pet.spin_t > 0, str(pet.spin_t))
check("三连击有庆祝台词", pet.bubble_text in pet_mod.TRIPLE_LINES, pet.bubble_text)

# 眨眼
pet.blink_t = 0.0
pet._trigger_blink()
check("眨眼动画触发", pet.blink_t > 0)

# 打盹与点击唤醒
pet._start_nap()
check("打盹状态激活", pet.sleeping is True)
check("打盹有睡眠台词", pet.bubble_text in pet_mod.SLEEP_LINES, pet.bubble_text)
QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(450)  # 单击延迟 280ms 后说唤醒台词
check("点击唤醒打盹的鱼", pet.sleeping is False)
check("唤醒台词", pet.bubble_text in pet_mod.WAKE_LINES, pet.bubble_text)
pet.chat_button.hide()
QTest.qWait(100)

# 长按摸头：按住 0.7 秒松开 → 摸头台词 + 爱心
pet.chat_paused = False
pet.bubble_text = ""
pet.particles.clear()
QTest.mousePress(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(700)
QTest.mouseRelease(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.qWait(150)
check("长按摸头台词", pet.bubble_text in pet_mod.PAT_HOLD_LINES, pet.bubble_text)
check("长按摸头产生爱心", len(pet.particles) > 0, str(len(pet.particles)))
check("长按摸头后鱼恢复移动", pet.chat_paused is False)

# 快速拖拽：快速甩动 → 快速拖拽台词 + 位置变化
pet.set_mode("still")
pos0 = pet.pos()
QTest.mousePress(pet, Qt.MouseButton.LeftButton, pos=CENTER)
QTest.mouseMove(pet, QPoint(CENTER.x() + 60, CENTER.y() + 60))
QTest.qWait(40)
QTest.mouseMove(pet, QPoint(CENTER.x() + 140, CENTER.y() + 140))
QTest.qWait(40)
QTest.mouseRelease(pet, Qt.MouseButton.LeftButton, pos=QPoint(CENTER.x() + 140, CENTER.y() + 140))
QTest.qWait(150)
check("快速拖拽被识别", pet._last_drag_fast is True)
check("快速拖拽台词", pet.bubble_text in pet_mod.DRAG_FAST_LINES, pet.bubble_text)
check("快速拖拽后位置变化", pet.pos() != pos0, f"{pos0} -> {pet.pos()}")

# 主动关心：久坐提醒 / 饿了提醒
pet.sleeping = False
pet.chat_paused = False
pet.bubble_text = ""
pet.last_interact_tick = pet.t - 999999
pet.last_care_long_sit = pet.t - 999999
pet._check_care()
check("久坐提醒", pet.bubble_text in pet_mod.CARE_LINES["long_sit"], pet.bubble_text)
pet.last_care_long_sit = pet.t
pet.last_feed_tick = pet.t - 999999
pet.last_care_hungry = pet.t - 999999
pet.bubble_text = ""
pet._check_care()
check("饿了提醒", pet.bubble_text in pet_mod.CARE_LINES["hungry"], pet.bubble_text)

# 悬停反应
pet.hover_t = 0.0
pet._on_hover()
check("悬停触发摇摆", pet.hover_t > 0)

# 菜单新交互项：转个圈 / 打个盹 / 一起玩 / 说句话
menu2 = pet._build_menu()
top2 = [a.text() for a in menu2.actions()]
sub2 = [a.text() for sm in menu2.findChildren(pet_mod.QMenu) for a in sm.actions()]
all2 = top2 + sub2
for need in ("转个圈", "打个盹", "一起玩", "说句话"):
    check(f"菜单含「{need}」", need in all2)
menu2.close()
pet.spin_t = 0.0
pet.do_spin()
check("菜单转个圈触发旋转", pet.spin_t > 0)
pet.toggle_nap()
check("菜单打个盹", pet.sleeping is True)
pet.toggle_nap()
check("菜单醒醒", pet.sleeping is False)

# ---------- 恢复测试前的 config.json（防止测试写入的 size/mode/key 残留） ----------
try:
    if _CONFIG_BACKUP is not None:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(_CONFIG_BACKUP)
    elif os.path.exists(_CONFIG_PATH):
        os.remove(_CONFIG_PATH)
except Exception as e:
    print("config.json 恢复失败:", e)

# ---------- 汇总 ----------
failed = [r for r in results if not r[1]]
print("\n" + "=" * 50)
print(f"总用例: {len(results)}  通过: {len(results) - len(failed)}  失败: {len(failed)}")
if failed:
    print("失败项:")
    for name, ok, detail in failed:
        print("  -", name, detail)
    sys.exit(1)
else:
    print("全部通过 ✅")
    sys.exit(0)
