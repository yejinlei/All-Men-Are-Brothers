"""Step 9　韵文词牌图谱：抽取全书韵文（诗/词/赋/偈），统计锚点类型、句长与词牌分布。

只读 docs/texts/versions/*/（经 lib/corpus.py），产出 docs/data/verse_index.json。
抽取规则（启发式，页面明示）：
  · 锚点行＝行末为「：」且以「詩曰/詞曰/有詩爲證/古風/贊曰/箴曰/偈曰/格言曰/正是/但見/《詞牌》…」收尾的行；
  · 锚点行之后的连续行，若不含对话引号、不含「道：」类叙述标记，且为短句行（≤24 字）
    或赋体长句（≤130 字且含 3 个以上「，」），即计入韵文块；遇叙述恢复则止。
"""
from __future__ import annotations
import sys, os, json, re, datetime
from collections import OrderedDict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import corpus as corpuslib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.path.join(DOCS, 'data', 'verse_index.json')

ANCHOR_RE = re.compile(
    r'(詩曰|诗曰|詞曰|词曰|又詩曰|又诗曰|有詩爲證|有詩為證|有诗为证|詩云|诗云|古風一首|古風|古风一首|古风|'
    r'贊曰|赞曰|箴曰|箴言|偈曰|格言曰|評曰|评曰|論曰|论曰|詞云|词云|正是|但見|但见|有分教|怎見得|怎见得|'
    r'古人有詩|古人有诗|後人有詩|后人有诗|後人詩曰|古人詩曰|口號|口号|'
    r'《[^》]{2,8}》)(\(\d+\))*[：:]\s*')

DIALOG_RE = re.compile(r'[“”「」]|(道|說|説|曰)[：:]')
NOTE_RE = re.compile(r'\(\s*\d+\s*\)')          # 校注号 (1)(2)…
NARR_HEAD = re.compile(r'^[，。；：]*\s*(話說|话说|且說|且说|卻說|却说|再說|再说|原來|原来|看官|當下|当下|次日|次日|只見|只见|卻纔|却才|后来|後來|自此|當時|当时)')


def strip_note(s: str) -> str:
    return NOTE_RE.sub('', s)


def paragraphs(text: str):
    """把语料还原为段落：连续非空行合并（兼容按列宽折行的版本），空行分段。"""
    paras, cur = [], []
    for raw in text.split('\n'):
        s = raw.strip()
        if s:
            cur.append(re.sub(r'\s+', '', s))
        elif cur:
            paras.append(''.join(cur))
            cur = []
    if cur:
        paras.append(''.join(cur))
    return paras


def is_verse(s: str) -> bool:
    """判断一段是否为韵文：无对话引号与「道：」，且有分句（允许被空行切开的单句段）。"""
    t = strip_note(s)
    if not t or DIALOG_RE.search(t) or NARR_HEAD.match(t):
        return False
    if not (8 <= len(t) <= 240):
        return False
    if t.count('，') >= 2:
        return True
    # 被空行切散的韵文段（如每段一对句）：短、自带标点、不以叙述词起头
    return len(t) <= 40 and t.count('，') >= 1 and not NARR_HEAD.match(t)


def is_bare_verse(s: str) -> bool:
    """无锚点裸韵文：≥4 个整齐短句（各句 4–10 字，句长种类 ≤4），且非叙述语。"""
    t = strip_note(s)
    if not t or DIALOG_RE.search(t) or NARR_HEAD.match(t):
        return False
    if len(t) < 24 or len(t) > 240:
        return False
    sents = [x for x in re.split(r'[，。！？；：]', t) if x]
    if len(sents) < 4:
        return False
    lens = [len(x) for x in sents]
    if any(not (4 <= L <= 10) for L in lens):
        return False
    if len(set(lens)) > 4:
        return False
    return True


TAIL_RE = re.compile(r'(畢竟|毕竟|且聽下回|且听下回|不知後事如何|不知后事如何|後事如何|有分教)')


def trim_tail(lines):
    """剥离块尾粘上的章末套语（「畢竟…且聽下回分解」之类），只保留韵文本身。"""
    out = []
    for s in lines:
        m = TAIL_RE.search(s)
        if m:
            head = s[:m.start()]
            if head.strip():
                out.append(head)
            break
        out.append(s)
    return out


def extract_paras(text: str):
    """通道 B：先按空行合并为段落再判定（适配按列宽折行的整理本，如金批繁本）。"""
    paras = paragraphs(text)
    blocks, i = [], 0
    while i < len(paras):
        p = paras[i]
        m = ANCHOR_RE.search(p)
        if m:
            tail = p[m.end():]
            cand = []
            if tail and is_verse(tail):
                cand = [tail]
            elif not tail.strip():
                # 锚点在段尾：向下收集所有连续的韵文段（兼容每句一段的版本）
                j = i + 1
                acc = 0
                while j < len(paras) and is_verse(paras[j]) and len(cand) < 24 and acc < 300:
                    cand.append(paras[j]); acc += len(paras[j])
                    j += 1
                if cand:
                    i = j - 1
            if cand:
                cand = trim_tail(cand)
                blocks.append({'anchor': m.group(1), 'lines': cand,
                               'chars': sum(len(x) for x in cand)})
            i += 1
            continue
        if is_bare_verse(p):
            blocks.append({'anchor': '(无锚点·结构判定)', 'lines': [p], 'chars': len(p)})
        i += 1
    return blocks


def extract_lines(text: str):
    """通道 A：逐行判定（适配「一段一行」的版本，为多数版本的实际形态）。"""
    lines = [x.strip() for x in text.split('\n') if x.strip()]
    blocks, i = [], 0
    while i < len(lines):
        ln = lines[i]
        m = ANCHOR_RE.search(ln)
        if m:
            tail = ln[m.end():]
            cand = []
            if tail and is_verse(tail):
                cand = [tail]
            elif not tail.strip():
                j = i + 1
                acc = 0
                while j < len(lines) and is_verse(lines[j]) and len(cand) < 24 and acc < 300:
                    cand.append(lines[j]); acc += len(lines[j])
                    j += 1
                if cand:
                    i = j - 1
            if cand:
                cand = trim_tail(cand)
                blocks.append({'anchor': m.group(1), 'lines': cand,
                               'chars': sum(len(x) for x in cand)})
            i += 1
            continue
        if is_bare_verse(ln):
            blocks.append({'anchor': '(无锚点·结构判定)', 'lines': [ln], 'chars': len(ln)})
        i += 1
    return blocks


def extract(text: str):
    """自动择通道：两通道分别抽取，取块数多者（折行本会自然落到段落通道）。"""
    a = extract_lines(text)
    b = extract_paras(text)
    if len(a) >= len(b):
        return a, 'line'
    return b, 'para'


CIPAI = [
    '臨江仙', '西江月', '鷓鴣天', '念奴嬌', '滿庭芳', '水調歌頭', '如夢令', '浣溪沙', '減字木蘭花',
    '南鄉子', '滿江紅', '沁園春', '菩薩蠻', '清平樂', '虞美人', '好事近', '漁家傲', '醉蓬萊', '行香子',
    '踏莎行', '點絳唇', '憶江南', '長相思', '一剪梅', '蝶戀花', '玉樓春', '鵲橋仙', '相見歡', '浪淘沙',
    '採桑子', '采桑子', '青玉案', '感皇恩', '驀山溪', '永遇樂', '桂枝香', '喜遷鶯', '千秋歲', '定風波',
    '蘇幕遮', '天仙子', '調笑令', '聲聲慢', '雨霖鈴', '揚州慢', '沁園春', '望海潮', '燭影搖紅',
]
CIPAI_SIMP = {c: None for c in CIPAI}

_CC = None


def simp(s: str) -> str:
    global _CC
    if _CC is None:
        try:
            import opencc
            _CC = opencc.OpenCC('t2s')
        except Exception:
            _CC = False
    if not _CC:
        return s
    return _CC.convert(s)


def _init_cipai_simp():
    """预先算出每个词牌名的简体形式，避免逐块转换。"""
    for c in CIPAI:
        CIPAI_SIMP[c] = simp(c).lstrip('《').rstrip('》')


_init_cipai_simp()


def is_verse_line(s: str) -> bool:
    """（历史遗留的逐行判据，现由段落级 is_verse / is_bare_verse 取代。）"""
    if not s:
        return False
    if DIALOG_RE.search(s):
        return False
    if len(s) <= 24:
        return True
    if len(s) <= 140 and s.count('，') >= 3:
        return True
    return False


def _unused():
    return None


def main():
    c = corpuslib.Corpus()
    reg = json.load(open(os.path.join(DOCS, 'data', 'registry.json'), encoding='utf-8'))
    labels = {v['id']: (v.get('label') or v['id']) for v in reg['versions']}

    anchor_by_v, cipai_by_v, len_by_v, per_v, samples = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict(), []
    for vid in c.version_ids():
        anchors, cipais, lens, chan = Counter(), Counter(), Counter(), Counter()
        blocks_all, nblocks, nlines, nchars = [], 0, 0, 0
        for num in c.nums(vid):
            try:
                txt = c.text(vid, num, 'fan')
            except Exception:
                continue
            blocks, ch = extract(txt)
            chan[ch] = chan.get(ch, 0) + 1
            for b in blocks:
                nblocks += 1
                nlines += len(b['lines'])
                nchars += b['chars']
                anchors[b['anchor']] += 1
                joined = b['anchor'] + ''.join(b['lines'])
                js = simp(joined)
                for cp in CIPAI:
                    if cp in joined or CIPAI_SIMP[cp] in js:
                        cipais[cp] += 1
                for s in re.split(r'[，。；！？]', joined):
                    s = s.strip()
                    if 4 <= len(s) <= 12:
                        lens[len(s)] += 1
                blocks_all.append(OrderedDict([
                    ('hui', num), ('anchor', b['anchor']), ('n', len(b['lines'])),
                    ('chars', b['chars']), ('first', b['lines'][0][:40]),
                ]))
                # 每版最多留 60 块全文，供页面抽样复核
                if len([x for x in samples if x['v'] == vid]) < 60:
                    samples.append(OrderedDict([
                        ('v', vid), ('hui', num), ('anchor', b['anchor']),
                        ('text', '\n'.join(b['lines'])[:400]),
                    ]))
        anchor_by_v[vid] = OrderedDict(anchors.most_common())
        cipai_by_v[vid] = OrderedDict(cipais.most_common())
        len_by_v[vid] = OrderedDict(sorted(lens.items()))
        per_v[vid] = OrderedDict([
            ('label', labels.get(vid, vid)),
            ('blocks', nblocks), ('lines', nlines), ('chars', nchars),
            ('channel', chan.most_common(1)[0][0] if chan else 'line'),
            ('avg_line_chars', round(nchars / max(1, nlines), 2)),
            ('blocks_list', blocks_all),
        ])

    payload = OrderedDict([
        ('generated', datetime.date.today().isoformat()),
        ('method', '锚点行识别（行末「：」＋固定套语，如 詩曰／詞曰／有詩爲證／古風／贊曰／《詞牌》／正是／但見 等）'
                   '＋其后连续非对话短句行（≤24 字）或赋体长句（≤130 字且多分句）合并为韵文块。'),
        ('caveat', '抽取属启发式：章回体叙述中「正是」「但見」亦可用于散文收尾，'
                   '故块数略偏多属正常；句长与词牌统计用于看趋势，不作校勘依据。'),
        ('totals', OrderedDict([(vid, OrderedDict([('label', v['label']), ('blocks', v['blocks']),
                                                   ('lines', v['lines']), ('chars', v['chars']),
                                                   ('channel', v['channel']),
                                                   ('avg_line_chars', v['avg_line_chars'])]))
                                for vid, v in per_v.items()])),
        ('anchors', anchor_by_v),
        ('cipai', cipai_by_v),
        ('line_lens', len_by_v),
        ('blocks', OrderedDict([(vid, v['blocks_list']) for vid, v in per_v.items()])),
        ('samples', samples),
    ])
    json.dump(payload, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('写出', os.path.relpath(OUT, ROOT), '%.1f KB' % (os.path.getsize(OUT) / 1024))
    for vid, v in per_v.items():
        cp = cipai_by_v[vid]
        top = '，'.join('%s%d' % (k, n) for k, n in list(cp.items())[:4]) or '无'
        print('  %-22s 韵文块 %4d｜句 %5d｜字 %7d｜词牌命中 主要：%s'
              % (v['label'][:20], v['blocks'], v['lines'], v['chars'], top))
    allc = Counter()
    for cp in cipai_by_v.values():
        allc.update(cp)
    print('  词牌总计:', '，'.join('%s%d' % (k, n) for k, n in allc.most_common(12)))


if __name__ == '__main__':
    main()
