# -*- coding: utf-8 -*-
"""通用生成器：逐行处理 jian/chNNN.txt，用 trans 字典替换指定行号（正文段），
其余行（标题、诗曰、韵文、分隔线、注释）原样照抄。"""
import sys, json, os

BASE = '/home/user/workspace/2301106348078317209/All-Men-Are-Brothers/docs/texts/versions/jiqin'

def run(ch, trans):
    src = os.path.join(BASE, 'jian', ch + '.txt')
    dst = os.path.join(BASE, 'bai', ch + '.txt')
    with open(src, encoding='utf-8') as f:
        lines = f.read().split('\n')
    out = []
    for i, l in enumerate(lines, 1):
        if i in trans:
            out.append(trans[i])
        else:
            out.append(l)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    # 校验
    with open(dst, encoding='utf-8') as f:
        nlines = f.read().split('\n')
    assert len(nlines) == len(lines), (len(nlines), len(lines))
    for i, (a, b) in enumerate(zip(lines, nlines), 1):
        if (a == '') != (b == ''):
            print('BLANK MISMATCH line', i)
        if a != b and i not in trans:
            print('UNEXPECTED CHANGE line', i)
    print(ch, 'lines', len(lines), 'ok')
