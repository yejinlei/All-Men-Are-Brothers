#!/usr/bin/env python3
"""
把公版金批正文 build/_source/jin70_pi_jianpi.txt 拆成 71 个章回文件：
- 楔子  → ch000.txt
- 第一回→ch001.txt ... 第七十回→ch070.txt
同时：
1) 去掉文件头（序一/二/三、宋史断、读第五才子书法、贯华堂原序）
2) 去掉回前总批「总批：…」整段（已由 comments.json 的 zongpi 渲染，避免重复）
3) 保留「…」夹批在正文里（前端渲染成段间块）
4) 源文是按约 30 字硬换行，我们先把 prose 段内换行合并为连续字符串，再按句末（。！？…）
   自然切分为 40–90 字的小段；诗/词块逐行保留
5) 简体版用源文直接；繁体版用 OpenCC 简→繁
输出到 build/_source/jinpi_jian/ 和 build/_source/jinpi_fan/
"""
import os, re, sys
from pathlib import Path

try:
    from opencc import OpenCC
    HAS_OPENCC = True
    cc = OpenCC('s2t')
except ImportError:
    HAS_OPENCC = False
    print('WARN: opencc not installed, fan will be same as jian.', file=sys.stderr)
    cc = None

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'build/_source/jin70_pi_jianpi.txt'
OUT_JIAN = ROOT / 'build/_source/jinpi_jian'
OUT_FAN = ROOT / 'build/_source/jinpi_fan'
OUT_JIAN.mkdir(parents=True, exist_ok=True)
OUT_FAN.mkdir(parents=True, exist_ok=True)

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
    return CN_NUM.get(m.group(1)) if m else None

def s2t(s): return cc.convert(s) if cc else s

POEM_LEADS = ('诗曰','词曰','有诗为证','有词为证','古风','赞曰','偈曰','七绝','七律','五言','七言','词云','诗云','乃诗曰','又诗曰','道是','却似','怎见得','但见','只见','有分教')
PROSE_FORBIDDEN = ('说话','只见','话说','且说','来到','说道','一个','怎么','如何','甚么','什么','那里','哪里')

def is_poem_block(joined, lines):
    if any(joined.startswith(l) for l in POEM_LEADS):
        return True
    if len(lines) >= 2 and all(4 <= len(l) <= 11 for l in lines):
        if not any(w in joined for w in PROSE_FORBIDDEN):
            return True
    return False

def strip_zongpi(body):
    i = 0; n = len(body)
    while i < n:
        while i < n and body[i] in ' \n\u3000\r\t　': i += 1
        if i >= n: break
        if body[i] == '「':
            end = body.find('」', i+1)
            if end == -1: break
            inner = body[i+1:end].strip()
            if inner.startswith(('总批：','金批：','總批：')):
                i = end+1; continue
        break
    return body[i:].lstrip()

def split_sentences(prose):
    """按句末标点切分，保留引号闭合"""
    parts = []
    buf = ''
    i = 0; n = len(prose)
    while i < n:
        ch = prose[i]
        buf += ch
        if ch in '。！？…':
            # 往后吞并闭合引号
            j = i+1
            while j < n and prose[j] in '”’」』"\'）)':
                buf += prose[j]; j += 1
            parts.append(buf); buf = ''
            i = j; continue
        i += 1
    if buf: parts.append(buf)
    return [p for p in parts if p.strip()]

def reflow(text):
    text = text.replace('\r','')
    raw_blocks = re.split(r'\n\s*\n', text)
    out = []
    prose_buf = ''
    def flush():
        nonlocal prose_buf
        if not prose_buf: return
        sents = split_sentences(prose_buf)
        cur = ''
        for s in sents:
            if len(cur) + len(s) <= 70:
                cur += s
            else:
                if cur: out.append(cur)
                cur = s
        if cur: out.append(cur)
        prose_buf = ''
    for blk in raw_blocks:
        lines = [l.strip() for l in blk.split('\n') if l.strip()]
        if not lines: continue
        joined = ''.join(lines)
        if is_poem_block(joined, lines):
            flush()
            out.append('\n'.join(lines))
        else:
            prose_buf += joined
    flush()
    return '\n\n'.join(out)

def split_chaps():
    text = SRC.read_text(encoding='utf-8')
    CHAP_RE = re.compile(r'(楔子|第[一二三四五六七八九十百零〇]+回)\u3000[^\n]*')
    positions = []
    for m in CHAP_RE.finditer(text):
        idx = cn2i(m.group(1))
        if idx is not None:
            positions.append((idx, m.start(), m.end(), m.group(0)))
    positions.sort()
    files = {}
    for i, (idx, st, ed, title) in enumerate(positions):
        nxt = positions[i+1][1] if i+1 < len(positions) else len(text)
        body = text[ed:nxt]
        body = strip_zongpi(body)
        body = reflow(body)
        title_line = title.replace('\u3000',' ')
        files[idx] = title_line + '\n\n' + body.strip() + '\n'
    return files

def main():
    files = split_chaps()
    miss = sorted(set(range(71)) - set(files.keys()))
    assert not miss, f'缺回: {miss}'
    total = 0
    for idx in range(71):
        jian = files[idx]
        pi_count = len(re.findall(r'「[^」]+」', jian))
        total += pi_count
        (OUT_JIAN / f'ch{idx:03d}.txt').write_text(jian, encoding='utf-8')
        (OUT_FAN / f'ch{idx:03d}.txt').write_text(s2t(jian), encoding='utf-8')
    print(f'完成 71 回，夹批总数 {total}')
    # 抽查
    sample = (OUT_JIAN/'ch002.txt').read_text(encoding='utf-8')
    paras = sample.split('\n\n')
    print(f'ch002 段落数 {len(paras)}')
    for i,p in enumerate(paras[:8]):
        show = re.sub(r'「[^」]{0,30}[^」]*」','[批]',p)
        print(f'  [{i}] len={len(p)}: {show[:70]}')

if __name__ == '__main__':
    main()
