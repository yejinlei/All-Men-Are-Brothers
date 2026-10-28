# -*- coding: utf-8 -*-
import importlib.util, sys, re
import gen
gen.run = lambda *a, **k: None
BASE='/home/user/workspace/2301106348078317209/All-Men-Are-Brothers/docs/texts/versions/jiqin'
mark = re.compile(r'\((\d+)\)')

def load(mod):
    spec=importlib.util.spec_from_file_location(mod, mod+'.py')
    m=importlib.util.module_from_spec(spec)
    sys.modules[mod]=m
    spec.loader.exec_module(m)
    return m

for n in ['000','001','002','003','004','005','006','007','008']:
    c='c'+n; e='e'+n
    try:
        mc=load(c)
    except Exception as ex:
        print(c,'no base?',ex); continue
    base=dict(mc.trans)
    try:
        me=load(e)
    except Exception as ex:
        print(e,'skip',ex); continue
    new=mc.trans  # e updated in place
    tot=0
    for k in sorted(new):
        if k not in base: 
            print('!!',e,k,'not in base'); continue
        ms_old=mark.findall(base[k]); ms_new=mark.findall(new[k])
        if ms_old!=ms_new:
            print('!! MARKER MISMATCH',e,k,'old',ms_old,'new',ms_new)
        d=len(new[k])-len(base[k]); tot+=d
        if d<0:
            print('?? NEG',e,k,d)
    print(e,'total delta',tot)
