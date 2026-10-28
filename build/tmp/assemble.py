# -*- coding: utf-8 -*-
import os,sys,json
VDIR="docs/texts/versions/jiqin"; BODY="build/tmp/body"
FIX=json.load(open("build/tmp/tailfix.json",encoding="utf-8")) if os.path.exists("build/tmp/tailfix.json") else {}
def assemble(n):
    jl=open(os.path.join(VDIR,"jian","ch%03d.txt"%n),encoding="utf-8").read().split("\n")
    sep=jl.index("--------------------")
    bt=open(os.path.join(BODY,"ch%03d.txt"%n),encoding="utf-8").read().split("\n")
    if bt and bt[-1]=="": bt=bt[:-1]
    if len(bt)!=sep:
        print("MISMATCH ch%03d: body %d vs jian %d"%(n,len(bt),sep)); return
    tail="\n".join(jl[sep:])
    for a,b in FIX.get("ch%03d"%n,[]):
        assert a in tail, ("fix-not-found",n,a)
        tail=tail.replace(a,b)
    open(os.path.join(VDIR,"bai","ch%03d.txt"%n),"w",encoding="utf-8").write("\n".join(bt)+"\n"+tail)
    print("wrote ch%03d"%n)
for a in sys.argv[1:]:
    assemble(int(a))
