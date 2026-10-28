# -*- coding: utf-8 -*-
"""按 line->译文 映射生成 bai 文件；未映射行（韵文/引领语/注文/空行）原样照抄。"""
import sys, importlib.util, os

def load_mod(path):
    spec = importlib.util.spec_from_file_location("mapmod", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def run(ver, num, mappath):
    root = "/home/user/workspace/2301106348078317209/All-Men-Are-Brothers"
    jf = os.path.join(root, "docs/texts/versions", ver, "jian", "ch%03d.txt" % num)
    bf = os.path.join(root, "docs/texts/versions", ver, "bai", "ch%03d.txt" % num)
    src = open(jf, encoding="utf-8").read().split("\n")
    m = load_mod(mappath)
    mp = m.LINES
    out = []
    for i, line in enumerate(src):
        ln = i + 1
        if ln in mp:
            out.append(mp[ln])
        else:
            out.append(line)
    open(bf, "w", encoding="utf-8").write("\n".join(out))
    miss = [k for k in mp if k < 1 or k > len(src) or (not src[k-1].strip())]
    print("wrote", bf, "lines", len(out), "mapped", len(mp), "badkeys", miss)

if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]), sys.argv[3])
