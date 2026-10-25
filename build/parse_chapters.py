#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将四个版本原文按"===== 第N回 标题 ====="分割，生成 data/chapters_{edition}.json
"""
import re, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(BASE, 'raw')
DATA = os.path.join(BASE, 'data')
DOCS_TEXTS = os.path.join(BASE, 'docs', 'texts')
os.makedirs(DATA, exist_ok=True)
os.makedirs(DOCS_TEXTS, exist_ok=True)

EDITIONS = [
    # (key, file, label, total_hui_expected)
    ('jinshengtan', 'jinshengtan_70hui.txt', '金圣叹批评第五才子书（七十回本·贯华堂本）', 70),
    ('rongyutang',  'rongyutang_100hui.txt', '容与堂本（百回繁本·李卓吾评）', 100),
    ('yuanwuya',    'yuanwuya_120hui.txt',   '袁无涯原刊本（百二十回水浒全传）', 120),
]

CHAPTER_RE = re.compile(r'^={5}\s*第([一二三四五六七八九十百零\d]+)回\s*([^=]+?)\s*={5}\s*$')
XIEZI_RE  = re.compile(r'^={5}\s*(楔子|引首)\s*([^=]*?)\s*={5}\s*$')

CN_NUM = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '百':100,'两':2}
def cn2int(s):
    s = s.strip()
    if s.isdigit(): return int(s)
    # 支持 一百单八 / 一百〇八 / 二十 等
    total = 0
    if '百' in s:
        b, _, a = s.partition('百')
        if b: total += CN_NUM.get(b,1)*100
        rest = a.replace('单','').replace('〇','零').replace('零','')
        if rest:
            if '十' in rest:
                t,_,o = rest.partition('十')
                total += CN_NUM.get(t,1)*10
                if o: total += CN_NUM[o]
            elif len(rest)==1:
                total += CN_NUM[rest]
    elif '十' in s:
        t,_,o = s.partition('十')
        total += CN_NUM.get(t,1)*10
        if o: total += CN_NUM[o]
    else:
        for c in s:
            total = total*10 + CN_NUM.get(c,0)
    return total

def parse_edition(key, fname, label, expect):
    path = os.path.join(RAW, fname)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    chapters = []
    cur_id, cur_title, cur_lines = None, None, []
    preamble = []
    in_preamble = True
    def push(ch_id, ch_title, body_lines):
        body = '\n'.join(body_lines).strip()
        chapters.append({
            'id': ch_id,
            'num': cn2int(ch_id.split('_')[0]) if ch_id.startswith('hui_') else 0,
            'title': ch_title.strip(),
            'content': body,
            'chars': len(body),
        })
    for line in lines:
        m = XIEZI_RE.match(line.strip())
        if m:
            if cur_id is not None:
                push(cur_id, cur_title, cur_lines)
            cur_id, cur_title = 'xiezi_0', m.group(1)+(m.group(2) or '')
            cur_lines = []
            in_preamble = False
            continue
        m = CHAPTER_RE.match(line.strip())
        if m:
            if cur_id is not None:
                push(cur_id, cur_title, cur_lines)
            elif preamble:
                # save preamble
                pass
            num = cn2int(m.group(1))
            cur_id = f"hui_{num}"
            cur_title = f"第{m.group(1)}回 " + m.group(2).strip()
            cur_lines = []
            in_preamble = False
            continue
        if in_preamble:
            preamble.append(line)
        else:
            cur_lines.append(line)
    if cur_id is not None:
        push(cur_id, cur_title, cur_lines)
    # 写入data JSON (不含正文，节省大小)
    meta = {
        'key': key,
        'label': label,
        'total_hui_expected': expect,
        'actual_hui': len([c for c in chapters if c['id'].startswith('hui_')]),
        'total_chars': sum(c['chars'] for c in chapters),
        'chapters': [{'id':c['id'],'num':c['num'],'title':c['title'],'chars':c['chars']} for c in chapters],
    }
    with open(os.path.join(DATA, f'chapters_{key}.json'),'w',encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # 写入 docs/texts 完整JSON（浏览器按需fetch）
    full = {'key':key,'label':label,'chapters':chapters}
    # 为减小体积，把每章正文单独写入 texts/{key}/{id}.txt
    edir = os.path.join(DOCS_TEXTS, key)
    os.makedirs(edir, exist_ok=True)
    toc = []
    for c in chapters:
        with open(os.path.join(edir, f"{c['id']}.txt"),'w',encoding='utf-8') as f:
            f.write(c['content'])
        toc.append({'id':c['id'],'num':c['num'],'title':c['title'],'chars':c['chars']})
    with open(os.path.join(DOCS_TEXTS, f'{key}.json'),'w',encoding='utf-8') as f:
        json.dump({'key':key,'label':label,'chapters':toc,'total_chars':sum(x['chars'] for x in toc)},
                  f, ensure_ascii=False, indent=2)
    print(f"[{key}] {label}")
    print(f"  - 解析到 {len(chapters)} 个章节单元（含楔子/引首），回目数 {len([c for c in chapters if c['id'].startswith('hui_')])}")
    print(f"  - 总字数 {meta['total_chars']:,}")
    return meta

for e in EDITIONS:
    parse_edition(*e)

# 征四寇是简本招安后段，单独处理（作为征四寇版本的附录章节）
def parse_zhengsikou():
    path = os.path.join(RAW, 'zhengsikou.txt')
    with open(path,'r',encoding='utf-8') as f:
        text = f.read()
    # 征四寇按大段分（征辽/田虎/王庆/方腊）
    # 简单做：整体保存
    out = os.path.join(DOCS_TEXTS, 'zhengsikou')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out,'full.txt'),'w',encoding='utf-8') as f:
        f.write(text)
    print(f"[zhengsikou] 征四寇简本/后传，字数 {len(text):,}（作为版本附录）")

parse_zhengsikou()
print("\n=== 完成 ===")
