# -*- coding: utf-8 -*-
"""把逐行译文(tr/*.txt)按源文结构生成 bai，并做自检。"""
import sys, os, re
ROOT = "/home/user/workspace/2301106348078317209/All-Men-Are-Brothers"
VDIR = os.path.join(ROOT, "docs/texts/versions/jin70")
TRD  = os.path.join(ROOT, "build/tmp/jin70_tr")

sys.path.insert(0, os.path.join(ROOT, "build"))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(ROOT, "build/check_bai.py"))
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)

def rd(p):
    return open(p, encoding="utf-8").read()

def gen(ch):
    src = rd(os.path.join(VDIR, "jian", "ch%03d.txt" % ch))
    traw = rd(os.path.join(TRD, "ch%03d.txt" % ch))
    src_trail = src.endswith("\n")
    tr_trail  = traw.endswith("\n")
    sl = src[:-1].split("\n") if src_trail else src.split("\n")
    tl = traw[:-1].split("\n") if tr_trail else traw.split("\n")
    if len(sl) != len(tl):
        print("!!! ch%03d 行数不符: 源%d 译%d" % (ch, len(sl), len(tl)))
        # 打印错位点，便于定位
        n = min(len(sl), len(tl))
        for i in range(n):
            if (sl[i].strip()=="") != (tl[i].strip()==""):
                print("   首个空行错位 i=%d 源=%r 译=%r" % (i+1, sl[i][:20], tl[i][:20]))
                break
        return False
    out = []
    for s, t in zip(sl, tl):
        ws = s[:len(s)-len(s.lstrip())]
        if s.strip() == "":
            out.append(ws)
        else:
            out.append(ws + t.strip())
    # 生僻字/PUA 照抄：jin70 ch034 行171/186 源文用 U+28C47 表「林冲」之冲
    if ch == 34:
        for ln in (171, 186):
            out[ln-1] = out[ln-1].replace("林冲", "林\U00028C47")
    body = "\n".join(out)
    if src_trail:
        body += "\n"
    open(os.path.join(VDIR, "bai", "ch%03d.txt" % ch), "w", encoding="utf-8").write(body)
    return True

def check(ch):
    jl = open(os.path.join(VDIR,"jian","ch%03d.txt"%ch),encoding="utf-8").read().split("\n")
    bl = open(os.path.join(VDIR,"bai","ch%03d.txt"%ch),encoding="utf-8").read().split("\n")
    vm=0; bad=[]
    for i in range(min(len(jl),len(bl))):
        if cb.is_verse(jl[i]) and jl[i].strip()!=bl[i].strip():
            vm+=1; bad.append(i+1)
    jt="\n".join(l for l in jl if not cb.is_verse(l))
    bt="\n".join(l for l in bl if not cb.is_verse(l))
    hard=cb.count_hard(bt); hn=sum(hard.values())
    jh=len(cb.HAN.findall(jt)); bh=len(cb.HAN.findall(bt))
    ratio=round(bh/jh,3) if jh else 0
    print("ch%03d 结构=%s 译行=%d 源行=%d | verse_mismatch=%d %s | hard=%d %s | ratio=%s"%(
        ch, len(jl)==len(bl), len(bl), len(jl), vm, bad[:20], hn, {k:v for k,v in hard.items() if v}, ratio))

if __name__=="__main__":
    mode=sys.argv[1]; ch=int(sys.argv[2])
    if mode=="gen":
        if gen(ch): check(ch)
    elif mode=="check":
        check(ch)
