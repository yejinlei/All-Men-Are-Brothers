"""Step 10　回目对句格律分析：量化各版本回目的字数、平仄与对仗工整度。

只读 docs/texts/versions/*/chapters.json，产出 docs/data/couplet.json。
平仄判定规则（公开可查）：
  · 以普通话读音为准（pypinyin），阴平(1)、阳平(2) 为「平」，上声(3)、去声(4) 为「仄」，
    轻声与多音字默认读音记为「未辨」；
  · 中古入声字在普通话中已派入四声，本方法**不能识别入声**，故平仄结果属「今音近似」，
    不可直接当作近体诗格律核验（详见页面方法说明）。
"""
from __future__ import annotations
import sys, os, json, re, datetime
from collections import OrderedDict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pypinyin import lazy_pinyin, Style

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
VERS = os.path.join(DOCS, 'texts', 'versions')
OUT = os.path.join(DOCS, 'data', 'couplet.json')
REG = os.path.join(DOCS, 'data', 'registry.json')

PREFIX = re.compile(r'^第\s*[一二三四五六七八九十百零〇0-9]+\s*回[\s　]*')
PING = '○'    # 平
ZE = '●'      # 仄
UNK = '△'     # 未辨（轻声／多音／非汉字）


def t2p(ch: str) -> str:
    """单字今音平仄。"""
    if not re.match(r'[\u3400-\u9fff]', ch):
        return UNK
    try:
        syl = lazy_pinyin(ch, style=Style.TONE3, errors='ignore')
        if not syl:
            return UNK
        s = syl[0]
        if s[-1] in '1234':
            return PING if s[-1] in '12' else ZE
        return UNK
    except Exception:
        return UNK


def line_ping(text: str) -> str:
    return ''.join(t2p(c) for c in text)


def dup_chars(a: str, b: str) -> int:
    """上下句共用汉字数（重字越少越工）。"""
    return len(set(a) & set(b))


def analyze(versions):
    pairs = []
    for vid, label in versions:
        cp = os.path.join(VERS, vid, 'chapters.json')
        if not os.path.exists(cp):
            continue
        chapters = json.load(open(cp, encoding='utf-8'))
        if isinstance(chapters, dict):
            chapters = chapters.get('chapters', [])
        for c in chapters:
            title = (c.get('title') or '').strip()
            if not PREFIX.match(title):
                continue
            body = PREFIX.sub('', title).strip()
            parts = [p for p in re.split(r'[\s　]+', body) if p]
            item = OrderedDict([('v', vid), ('hui', c.get('num')),
                                ('title', title)])
            if len(parts) >= 2:
                up, down = parts[0], parts[-1]
                item['up'] = up
                item['down'] = down
                item['up_p'] = line_ping(up)
                item['down_p'] = line_ping(down)
                item['eq_len'] = len(up) == len(down)
                item['end_ok'] = (line_ping(up)[-1:] == ZE and line_ping(down)[-1:] == PING)
                item['dup'] = dup_chars(up, down)
            else:
                item['up'] = body
                item['down'] = ''
                item['up_p'] = line_ping(body)
                item['down_p'] = ''
                item['eq_len'] = False
                item['end_ok'] = False
                item['dup'] = 0
                item['single'] = True
            pairs.append(item)
    return pairs


def main():
    reg = json.load(open(REG, encoding='utf-8'))
    versions = [(v['id'], v.get('label') or v['id']) for v in reg['versions']]
    pairs = analyze(versions)

    by_ver = OrderedDict()
    for p in pairs:
        by_ver.setdefault(p['v'], []).append(p)

    out_vers = []
    for vid, label in versions:
        items = by_ver.get(vid, [])
        if not items:
            continue
        paired = [x for x in items if not x.get('single')]
        lens = Counter(len(x['up']) for x in paired)
        up_lens = Counter(len(x['up']) for x in items)
        out_vers.append(OrderedDict([
            ('id', vid), ('label', label), ('count', len(items)),
            ('paired', len(paired)),
            ('single', len(items) - len(paired)),
            ('avg_up_len', round(sum(len(x['up']) for x in items) / max(1, len(items)), 2)),
            ('eq_len_ratio', round(sum(1 for x in paired if x['eq_len']) / max(1, len(paired)), 4)),
            ('end_ok_ratio', round(sum(1 for x in paired if x['end_ok']) / max(1, len(paired)), 4)),
            ('avg_dup', round(sum(x['dup'] for x in paired) / max(1, len(paired)), 2)),
            ('len_hist', OrderedDict(sorted(lens.items()))),
            ('up_len_hist', OrderedDict(sorted(up_lens.items()))),
        ]))

    all_paired = [x for x in pairs if not x.get('single')]
    payload = OrderedDict([
        ('generated', datetime.date.today().isoformat()),
        ('method', '去「第X回」前缀后按空格切上下句；平仄以普通话四声判定（1/2 声平，3/4 声仄），'
                   '末字「上仄下平」记为合律；对仗工整度以「上下句等长」与「上下句重字少」两项衡量。'),
        ('caveat', '本方法用今音判平仄，**不能识别中古入声**（入声已派入普通话四声），'
                   '故「合律率」是今音近似值，不是近体诗格律结论；对仗只作字数与重字的浅层度量，'
                   '未做词性对品。'),
        ('legend', {'平': PING, '仄': ZE, '未辨': UNK}),
        ('n_pairs', len(pairs)),
        ('versions', out_vers),
        ('sample_note', '全量回目对句在此，供逐条核对。'),
        ('pairs', pairs),
    ])

    json.dump(payload, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('写出', os.path.relpath(OUT, ROOT))
    print('版本 %d 个，回目对句 %d 条（可切上下句 %d 条）' % (len(out_vers), len(pairs), len(all_paired)))
    for v in out_vers:
        print('  %-22s 回目 %3d｜均上句 %4.1f 字｜等长率 %.2f｜上仄下平率 %.2f｜平均重字 %.1f'
              % (v['label'][:20], v['count'], v['avg_up_len'], v['eq_len_ratio'], v['end_ok_ratio'], v['avg_dup']))
    print('文件大小 %.1f KB' % (os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()
