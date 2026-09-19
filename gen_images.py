# -*- coding: utf-8 -*-
"""心灵共振卡牌 - 即梦批量生图脚本（5.0-pro，断点续跑）"""
import json, os, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

API = "http://127.0.0.1:3000/v1/images/generations"
KEY = "sk-fcZ85kCG984arkccmuMmiuXGsOoMZzuRywiZ2Tiyotq12w6X"
MODEL = "jimeng-image-5.0-pro"
SIZE = "1024x1536"
STYLE = "新中式暗夜高级感插画风格，深墨蓝色夜色基调，暗金色暖光点缀，电影感光影构图，人物剪影化处理不露正脸，细腻颗粒质感，氛围温暖治愈，画面中不出现任何文字，竖版构图。"

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def gen(prompt, out_path, retries=6):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        log("跳过(已存在): " + os.path.basename(out_path))
        return True
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": SIZE, "response_format": "url"}).encode("utf-8")
    for i in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode("utf-8"))
            url = d["data"][0]["url"]
            urllib.request.urlretrieve(url, out_path)
            log("OK: %s (%.1fKB)" % (os.path.basename(out_path), os.path.getsize(out_path)/1024))
            time.sleep(2)
            return True
        except Exception as e:
            wait = 8 + i * 5
            log("失败第%d次 %s: %s，%d秒后重试" % (i+1, os.path.basename(out_path), str(e)[:120], wait))
            time.sleep(wait)
    log("放弃: " + os.path.basename(out_path))
    return False

def main():
    data = json.load(open(os.path.join(BASE, "questions.json"), encoding="utf-8"))
    tasks = []
    for mode in data["modes"].values():
        for lv in mode["levels"]:
            for q in lv["questions"]:
                tasks.append((q["id"], STYLE + q["scene"]))
    for p in data["punishments"]:
        tasks.append((p["id"], STYLE + p["scene"] + "，喜剧幽默氛围"))
    # 卡背 + 三层纹理 + 首页背景
    tasks.append(("ui-cardback", "新中式暗夜高级感卡牌背面设计，深墨蓝底，中央暗金色圆形徽章纹样，四周精致烫金卷草纹边框，对称构图，无文字，竖版"))
    tasks.append(("ui-frame-1", "新中式暗夜高级感卡牌边框纹理，浅层淡雅暗金细线描边，深墨蓝底配极淡云纹，简约克制，无文字，竖版"))
    tasks.append(("ui-frame-2", "新中式暗夜高级感卡牌边框纹理，中层暗金双线描边带缠枝纹，深墨蓝底配暗纹，典雅，无文字，竖版"))
    tasks.append(("ui-frame-3", "新中式暗夜高级感卡牌边框纹理，深层浓重烫金宽边框带龙鳞云纹，深墨蓝近黑底，华丽庄重，无文字，竖版"))
    tasks.append(("ui-home-bg", "新中式暗夜高级感首页背景，深邃墨蓝夜空，远处零星暗金灯火与灯笼，星点散布，大面积留白，神秘温暖，无文字，竖版"))
    # 已有样张直接复用
    reuse = {"c01": "样张5.0-c01.png", "l11": "样张5.0-l11.png", "c05": "样张5.0-c05.png"}
    ok, fail = 0, []
    for qid, prompt in tasks:
        out = os.path.join(IMG_DIR, qid + ".png")
        if qid in reuse and not os.path.exists(out):
            src = os.path.join(IMG_DIR, reuse[qid])
            if os.path.exists(src):
                import shutil
                shutil.copy(src, out)
                log("复用样张: " + qid)
                ok += 1
                continue
        if gen(prompt, out):
            ok += 1
        else:
            fail.append(qid)
    log("全部结束: 成功%d / 失败%d" % (ok, len(fail)))
    if fail:
        log("失败清单: " + ",".join(fail))
    open(os.path.join(BASE, "gen_done.txt"), "w", encoding="utf-8").write(
        "ok=%d fail=%s" % (ok, ",".join(fail)))

if __name__ == "__main__":
    main()
