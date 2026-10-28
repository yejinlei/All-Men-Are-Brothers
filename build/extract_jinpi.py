#!/usr/bin/env python3
"""
从公版金批水浒 (build/_source/jin70_pi_jianpi.txt) 中抽取夹批，
按回切分、定位锚句（夹批前的正文片段），输出到四个金本的 comments.json，
类型 type=jiapi（金批夹批），字段:
  {chap, no, type:'jiapi', anchor: 锚句文本（简体）, text: 批语文本}
前端读到 type=jiapi 的块时，在正文首次出现 anchor 的段落后面插入 cmt-block。

策略：
- 逐字符扫描源文，遇到「…」就把里面的文本当批语；
- 夹批前最近一段非标点正文（前约8–25字，截到最近句末或逗号等停顿处）作为 anchor；
- 如果 anchor 太短（<4字），多向前取；太长（>30字）截断到最近停顿处。
- 回前总批「总批：…」整段跳过（已有 zongpi）。
- 眉批「眉批：…」单独标记 type=meipi。
"""
import re, json, os, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'build/_source/jin70_pi_jianpi.txt')

CHAP_FILES = [f'ch{i:03d}' for i in range(0, 71)]
CHAP_RE = re.compile(r'(楔子|第[一二三四五六七八九十百零〇]+回)\u3000[^\n]*')

CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,'二十':20,
          '二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,'二十六':26,'二十七':27,'二十八':28,'二十九':29,'三十':30,
          '三十一':31,'三十二':32,'三十三':33,'三十四':34,'三十五':35,'三十六':36,'三十七':37,'三十八':38,'三十九':39,'四十':40,
          '四十一':41,'四十二':42,'四十三':43,'四十四':44,'四十五':45,'四十六':46,'四十七':47,'四十八':48,'四十九':49,'五十':50,
          '五十一':51,'五十二':52,'五十三':53,'五十四':54,'五十五':55,'五十六':56,'五十七':57,'五十八':58,'五十九':59,'六十':60,
          '六十一':61,'六十二':62,'六十三':63,'六十四':64,'六十五':65,'六十六':66,'六十七':67,'六十八':68,'六十九':69,'七十':70}

def cn2i(s):
    if s == '楔子': return 0
    m = re.match(r'第([一二三四五六七八九十百零〇]+)回', s)
    if not m: return None
    return CN_NUM.get(m.group(1))

def split_chapters(src):
    """返回 {chap_idx: body_text}，body不含标题行和回前总批包裹"""
    text = open(src, encoding='utf-8').read()
    # 找所有章回起始点
    positions = []
    for m in CHAP_RE.finditer(text):
        idx = cn2i(m.group(1))
        if idx is not None:
            positions.append((idx, m.start(), m.end()))
    positions.sort()
    chaps = {}
    for i, (idx, st, ed) in enumerate(positions):
        nxt = positions[i+1][1] if i+1 < len(positions) else len(text)
        body = text[ed:nxt].strip()
        # 去掉"序一/序二/序三/宋史断/读第五才子书法" 等前置材料 — 只保留楔子以后
        # 楔子的 idx=0，前面的内容是序/读法，直接丢弃
        chaps[idx] = body
    return chaps

def extract_pi(body, chap_idx):
    """从一章正文中抽取夹批列表: [{type,anchor,text}]"""
    out = []
    i = 0
    n = len(body)
    # 去除回前总批段（以「总批：开头，下一个」后可能紧跟段落结束）
    # 策略：开头连续的「总批：…」块整段跳过
    # 先匹配
    while i < n:
        if body[i] == '「':
            end = body.find('」', i+1)
            if end == -1: break
            inner = body[i+1:end]
            if inner.startswith('总批：') or inner.startswith('金批：'):
                # 跳过这块回前总批（含块前后空白换行）
                j = end+1
                while j < n and body[j] in ' \n\u3000\r\t':
                    j += 1
                i = j
                continue
            break
        i += 1
    # 现在 i 指到正文起始
    # 重新从头扫
    text_start = i
    # 重置 i
    i = text_start
    buf = ''  # 已扫描的正文（不含批语）
    while i < n:
        if body[i] == '「':
            end = body.find('」', i+1)
            if end == -1:
                buf += body[i:]
                break
            inner = body[i+1:end].strip()
            if not inner:
                i = end+1
                continue
            # 分类：眉批/夹批
            if inner.startswith('眉批：') or inner.startswith('眉批:'):
                ptype = 'meipi'
                ptext = inner[3:].strip()
            elif inner.startswith('夹批：') or inner.startswith('夹批:'):
                ptype = 'jiapi'
                ptext = inner[3:].strip()
            else:
                ptype = 'jiapi'
                ptext = inner
            # 从 buf 尾部取 anchor：找最近一个有意义的句末/停顿后的片段
            anchor = pick_anchor(buf)
            if anchor and ptext:
                out.append({'type': ptype, 'anchor': anchor, 'text': ptext})
            i = end+1
            continue
        buf += body[i]
        i += 1
    return out

def pick_anchor(buf):
    """从 buf 末尾截取锚句（8–28字，优先在句末处截断）"""
    # 先去掉尾部空白
    tail = buf.rstrip()
    if not tail: return ''
    # 向前取合适长度
    END_CHARS = '。！？；…'
    PAUSE_CHARS = '，、：）」'
    # 从尾部先找 28 字以内的句末
    for L in (28, 24, 20, 16, 12):
        if len(tail) < L: continue
        seg = tail[-L:]
        # 在 seg 前部找第一个句末点（避免断在句子最尾，锚句要完整）
        # 取 seg 中从位置 4 到 L-2 的最后一个句末
        cut = -1
        for j in range(len(seg)-2, 3, -1):
            if seg[j] in END_CHARS:
                cut = j+1; break
        if cut > 0:
            cand = seg[cut:].strip()
            # 去掉开头标点
            cand = cand.lstrip('，。、；：！？""''）」』】 \n\u3000')
            if len(cand) >= 4:
                return cand
    # 退而求其次：找逗号/顿号截断
    for L in (28, 24, 20, 16):
        if len(tail) < L: continue
        seg = tail[-L:]
        cut = -1
        for j in range(len(seg)-2, 3, -1):
            if seg[j] in PAUSE_CHARS:
                cut = j+1; break
        if cut > 0:
            cand = seg[cut:].strip().lstrip('，。、；：！？""''）」』】 \n\u3000')
            if len(cand) >= 4:
                return cand
    # 最后直接取末尾 10–18 字
    cand = tail[-18:].lstrip('，。、；：！？""''）」』】 \n\u3000')
    return cand[:28] if cand else tail[-12:]

def main():
    chaps = split_chapters(SRC)
    print(f'共解析 {len(chaps)} 回', file=sys.stderr)
    total_pi = 0
    pi_by_chap = {}
    for idx in range(0, 71):
        body = chaps.get(idx, '')
        pis = extract_pi(body, idx)
        pi_by_chap[idx] = pis
        total_pi += len(pis)
        print(f'ch{idx:03d}: {len(pis)} 条夹批', file=sys.stderr)
    print(f'合计 {total_pi} 条', file=sys.stderr)
    # 写入临时文件供后续使用
    out_p = os.path.join(ROOT, 'build/_source/jinpi_jiapi.json')
    with open(out_p, 'w', encoding='utf-8') as f:
        json.dump(pi_by_chap, f, ensure_ascii=False, indent=2)
    print(f'已写入 {out_p}', file=sys.stderr)

if __name__ == '__main__':
    main()
