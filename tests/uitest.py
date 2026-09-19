# -*- coding: utf-8 -*-
"""心灵共振 - 浏览器真机渲染自检（手机视口 390x844）"""
import json, os, subprocess, time, urllib.request, socket
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "tests", "out")
os.makedirs(OUT, exist_ok=True)
PORT = 8321

def free_port(p):
    s = socket.socket()
    try: s.bind(("127.0.0.1", p)); s.close(); return p
    except OSError: s.close(); return free_port(p+1)

PORT = free_port(PORT)
srv = subprocess.Popen(["C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe",
                        "-m", "http.server", str(PORT)], cwd=BASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/questions.json" % PORT, timeout=1)
        break
    except Exception: time.sleep(0.3)

fails = []
def check(cond, msg):
    print(("  [OK]   " if cond else "  [FAIL] ") + msg, flush=True)
    if not cond: fails.append(msg)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
        page.wait_for_timeout(1200)

        check(page.locator("#mode-grid .mode-card").count() == 4, "首页4个模式入口")
        bg_ok = page.evaluate("getComputedStyle(document.querySelector('#home .bgimg')).backgroundImage.includes('ui-home-bg.webp')")
        check(bg_ok, "首页背景图引用正确")
        page.screenshot(path=os.path.join(OUT, "1-home.png"), full_page=True)

        page.locator("#mode-grid .mode-card").first.click()
        page.wait_for_timeout(400)
        check(page.locator("#setup.active").count() == 1, "进入设置页")
        check(page.locator("#flip-row").is_visible(), "两人模式显示翻转开关")
        page.screenshot(path=os.path.join(OUT, "2-setup.png"), full_page=True)

        page.click("text=开 始")
        page.wait_for_timeout(500)
        check(page.locator("#game.active").count() == 1, "进入游戏页")
        page.screenshot(path=os.path.join(OUT, "3-game-back.png"))

        page.click("#card")
        page.wait_for_timeout(1000)
        img_ok = page.evaluate("document.getElementById('q-img').complete && document.getElementById('q-img').naturalWidth > 0")
        check(img_ok, "题卡配图加载成功")
        qt = page.inner_text("#q-text")
        check(len(qt) > 5, "题目文字渲染: " + qt[:20])
        page.screenshot(path=os.path.join(OUT, "4-game-front.png"))

        page.click("#heart-btn")
        page.wait_for_timeout(200)
        check("marked" in (page.get_attribute("#heart-btn", "class") or ""), "❤️标记生效")

        page.click("text=答完了")
        page.wait_for_timeout(300)
        check("玩家二" in page.inner_text("#turn-name"), "轮到下一位: " + page.inner_text("#turn-name"))

        page.click("#exempt-btn")
        page.wait_for_timeout(300)
        page.on("dialog", lambda d: d.accept())
        page.screenshot(path=os.path.join(OUT, "5-exempt.png"))

        # 快进到结束页验证回顾页
        page.evaluate("G.qi = G.deck.length - 1; G.ai = G.players.length - 1; G.marks.push({key:'t', qtext:'测试题目', player:'玩家一'}); nextAnswer();")
        page.wait_for_timeout(600)
        check(page.locator("#end.active").count() == 1, "进入结束回顾页")
        check(page.locator(".mark-item").count() >= 1, "回顾页展示标记")
        page.screenshot(path=os.path.join(OUT, "6-end.png"), full_page=True)

        # 手动彩蛋：连点标题5次
        for _ in range(5): page.click("#end-title")
        page.wait_for_timeout(500)
        check(page.locator("#gaze.active").count() == 1, "对视彩蛋手动触发成功")
        page.screenshot(path=os.path.join(OUT, "7-gaze.png"))

        real_errors = [e for e in errors if "favicon" not in e and "fonts.g" not in e]
        check(not real_errors, "无JS错误（实际 %d 处: %s）" % (len(real_errors), str(real_errors[:2])))
        browser.close()
finally:
    srv.terminate()

print("自检结果: %s" % ("全部通过 ✅" if not fails else "%d 项失败: %s" % (len(fails), fails)))
