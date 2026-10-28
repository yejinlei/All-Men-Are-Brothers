# -*- coding: utf-8 -*-
"""白话层（bai）质检：结构一致性 / 韵文一致性 / 文言残留 / 篇幅比。

用法：
  python3 build/check_bai.py            # 全版本体检（摘要 + 问题章节）
  python3 build/check_bai.py v120 0 1   # 只查 v120 的 ch000、ch001（章节号）
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = os.path.join(ROOT, "docs", "texts", "versions")
VERSIONS = ["v120", "v100", "v70", "jin70", "jin70_pi", "jinshengtan", "jiqin", "zsk"]

HAN = re.compile(r"[\u4e00-\u9fff]")
VERSE_LEAD = re.compile(r"(诗曰|词曰|有诗为证|有词为证|正是|但见|只见|有分教|赞曰|偈曰|古风|歌曰)")
SPEECH = re.compile(r"(道：|道:|说道|问道|答道|叫道|喝道|禀道|奏道|应道|骂道|笑道|回说|说：|说:)")
HARD = ["曰", "矣", "焉", "汝", "吾", "哉", "兮"]


def is_verse(s):
    s = s.strip()
    if not s:
        return False
    if re.match(r"^第[一二三四五六七八九十百零〇两]+回", s) or s.startswith("引首") or s.startswith("楔子"):
        return False
    if SPEECH.search(s):
        return False
    parts = [p for p in re.split(r"[，。；：！？、,;:!?]", s) if p.strip()]
    if len(parts) < 2:
        return False
    if len(s) > 60:      # 长行多为叙述长句（如 cross-句短读却被逗号切碎），不计入韵文，避免误报
        return False
    return max(len(p) for p in parts) <= 9


def count_hard(t):
    t2 = VERSE_LEAD.sub("", t)
    return {w: t2.count(w) for w in HARD}


def check_chapter(ver, num):
    jf = os.path.join(VDIR, ver, "jian", "ch%03d.txt" % num)
    bf = os.path.join(VDIR, ver, "bai", "ch%03d.txt" % num)
    if not os.path.exists(jf) or not os.path.exists(bf):
        return None
    jl = open(jf, encoding="utf-8", errors="replace").read().split("\n")
    bl = open(bf, encoding="utf-8", errors="replace").read().split("\n")
    res = {"ver": ver, "num": num, "struct_ok": len(jl) == len(bl),
           "verse_mismatch": 0, "hard": 0, "ratio": 0.0, "note": ""}
    if not res["struct_ok"]:
        res["note"] = "行数 %d vs %d" % (len(jl), len(bl))
    n = min(len(jl), len(bl))
    for i in range(n):
        if is_verse(jl[i]) and jl[i].strip() != bl[i].strip():
            res["verse_mismatch"] += 1
    jt = "\n".join(l for l in jl if not is_verse(l))
    bt = "\n".join(l for l in bl if not is_verse(l))
    res["hard"] = sum(count_hard(bt).values())
    jh, bh = len(HAN.findall(jt)), len(HAN.findall(bt))
    res["ratio"] = round(bh / jh, 3) if jh else 0.0
    return res


def summarize(ver, rows):
    good = bad = 0
    hard_tot = vm_tot = 0
    ratios = []
    worst = []
    for r in rows:
        if r is None:
            continue
        ok = r["struct_ok"] and r["verse_mismatch"] == 0 and r["hard"] == 0 and 1.0 <= r["ratio"] <= 1.9
        if ok:
            good += 1
        else:
            bad += 1
            worst.append(r)
        hard_tot += r["hard"]
        vm_tot += r["verse_mismatch"]
    avg = round(sum(r["ratio"] for r in rows if r) / max(1, len([r for r in rows if r])), 3)
    print("[%s] 合格 %d / 问题 %d  | 文言残留合计 %d | 韵文不符合计 %d | 平均篇幅比 %s"
          % (ver, good, bad, hard_tot, vm_tot, avg))
    for r in sorted(worst, key=lambda x: -(x["hard"] + x["verse_mismatch"] * 3))[:5]:
        print("    ! ch%03d 结构%s 韵文不符%d 文言残留%d 篇幅比%s %s"
              % (r["num"], "OK" if r["struct_ok"] else "ERR", r["verse_mismatch"], r["hard"], r["ratio"], r["note"]))


def main():
    args = sys.argv[1:]
    if args:
        ver = args[0]
        nums = [int(x) for x in args[1:]]
        for n in nums:
            r = check_chapter(ver, n)
            print(r)
        return
    for ver in VERSIONS:
        files = sorted(glob.glob(os.path.join(VDIR, ver, "bai", "ch*.txt")))
        nums = [int(re.search(r"ch(\d+)\.txt", f).group(1)) for f in files]
        rows = [check_chapter(ver, n) for n in nums]
        summarize(ver, rows)


if __name__ == "__main__":
    main()
