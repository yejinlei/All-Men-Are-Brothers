#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析程穆衡《水浒传注略》，生成 docs/texts/versions/chengzhu_notes.json
输出格式：{ "id":..., "name":..., ..., "0": {"1":"...","2":"..."}, "1": {...}, ... }
对齐 jiqin_notes.json 格式。
"""
import re, json, os
from collections import defaultdict

SRC = os.path.join(os.path.dirname(__file__), '_source', 'chengmuheng_zhulue.txt')
OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'texts', 'versions', 'chengzhu_notes.json')

text = open(SRC, encoding='utf-8').read()
lines = text.split('\n')

def cn2int(s):
    if s.isdigit(): return int(s)
    d = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    if s == '十': return 10
    if s.startswith('十'): return 10 + d.get(s[1:], 0)
    if '十' in s:
        a,_,b = s.partition('十')
        return (d.get(a,1) if a else 1)*10 + d.get(b,0)
    return d.get(s, 0)

def detect_chap(s):
    s = s.strip()
    if '楔子' in s: return 0
    m = re.search(r'[（(]\s*第([一二三四五六七八九十百零\d]+)回\s*[）)]', s)
    if m: return cn2int(m.group(1))
    m = re.search(r'第([一二三四五六七八九十百零\d]+)回', s)
    if m: return cn2int(m.group(1))
    return None

SEC_RE = re.compile(r'^[\s　]*(?:第[一二三四五六七八九十百零\d]+卷[（(]\s*)?(?:楔子|第[一二三四五六七八九十百零\d]+回)\s*[）)]?\s*$')
ITEM_RE = re.compile(r'^[\s　]*(\d+)\.(.+)')

# 结果
result = {
    "id": "chengzhu",
    "name": "程穆衡《水浒传注略》",
    "dynasty": "清乾隆四十四年（1779）成书，道光二十五年（1845）王氏听香阁刻王开沃补注本",
    "color": "#2f6f6f",
    "description": "清程穆衡著、王开沃补《水浒传注略》，为章回小说注本之祖。专释《水浒》名物、方言、制度、典故。郑振铎《西谛书话》称「为章回小说作注者，于此书外，未之前闻；引书凡数百种，僻书颇多，水浒多口语方言，作者于此亦多详加注释」。据读书网公版清道光二十五年王氏听香阁刻本电子文本录入。",
    "source": "读书网（dushu.com）公版清道光二十五年王氏听香阁刻本整理文本",
    "total": 0,
    "reliability": "B",
}

chap_data = defaultdict(dict)  # chap -> {no_str: text}
current_chap = None
pending_no = None
pending_text_parts = []
in_preamble = True

def flush():
    global pending_no, pending_text_parts, current_chap
    if pending_no is not None and current_chap is not None:
        t = ''.join(pending_text_parts).strip()
        # 规范化换行：把多空白压成空格，但保留段落分隔为单空格
        t = re.sub(r'\s+', ' ', t).strip()
        if t:
            chap_data[current_chap][str(pending_no)] = t
    pending_no = None
    pending_text_parts = []

for raw in lines:
    line = raw.rstrip()
    s = line.strip()
    if not s:
        continue
    if SEC_RE.match(s) and detect_chap(s) is not None:
        flush()
        current_chap = detect_chap(s)
        in_preamble = False
        continue
    if in_preamble:
        continue
    m = ITEM_RE.match(s)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 1000 and current_chap is not None:
            flush()
            pending_no = num
            pending_text_parts = [m.group(2).strip()]
            continue
    if pending_no is not None:
        pending_text_parts.append(' ' + s)

flush()

total = 0
for chap, items in chap_data.items():
    result[str(chap)] = items
    total += len(items)
result['total'] = total

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"已写入 {OUT}")
print(f"共 {total} 条注释，覆盖 {len(chap_data)} 回")
for ch in sorted(chap_data.keys()):
    print(f"  ch{ch:03d}: {len(chap_data[ch])} 条")
missing = [i for i in range(0,71) if i not in chap_data]
print(f"缺：{missing}")
