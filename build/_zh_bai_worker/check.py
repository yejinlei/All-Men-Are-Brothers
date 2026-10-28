# -*- coding: utf-8 -*-
"""检查：jie 与 bai 之间所有被改动（jian!=bai）的正文行，标出疑似韵文/注释行。"""
import re, sys
BASE='/home/user/workspace/2301106348078317209/All-Men-Are-Brothers/docs/texts/versions/jiqin'
for ch in ['ch000','ch001','ch002','ch003','ch004','ch005','ch006','ch007','ch008']:
    j=open(f'{BASE}/jian/{ch}.txt',encoding='utf-8').read().split('\n')
    b=open(f'{BASE}/bai/{ch}.txt',encoding='utf-8').read().split('\n')
    for i,(x,y) in enumerate(zip(j,b),1):
        if x!=y:
            # 疑似韵文/注释/分隔：改动不该发生在这些行
            if x.startswith('(') or x.strip()=='--------------------':
                print('!!',ch,i,'(notes/sep changed)')
            elif len(x.strip())<50 and ('。' not in x) and ('：“' not in x) and ('道：' not in x):
                print('??',ch,i,'|j|',x.strip()[:40])
    sys.stdout.flush()
print('scan done')
