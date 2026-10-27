"""批语装载器：把九家批注统一解析为规整记录。

解析口径与站点检索页 docs/search.html 完全一致（同一段文本按段落拆条），
因此统计结果可与检索页「载入 8229 条」对齐。

记录字段：cid(批注家 id) / who / tag / color / ver(挂载版本) / hui(回次) /
          type(批注类别) / keyword / text(单段文本)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEXTS = REPO / 'docs' / 'texts' / 'versions'
REGISTRY = REPO / 'docs' / 'data' / 'registry.json'

_VER_CACHE = None


def _ver_chapters():
    """预读各版本章目表，供 pick_ver 判断某回次由哪个版本承载。"""
    global _VER_CACHE
    if _VER_CACHE is None:
        with open(TEXTS / 'versions_index.json', encoding='utf-8') as f:
            idx = json.load(f)
        cache = {}
        for v in idx.get('versions', []):
            p = TEXTS / v['id'] / 'chapters.json'
            try:
                d = json.loads(p.read_text(encoding='utf-8'))
                cache[v['id']] = d if isinstance(d, list) else d.get('chapters', [])
            except Exception:
                cache[v['id']] = []
        _VER_CACHE = cache
    return _VER_CACHE


def _pick_ver(okver, hui):
    ch = _ver_chapters()
    for vid in okver or []:
        chs = ch.get(vid) or []
        if not chs:
            continue
        if hui is None or hui == 0:
            if any(c.get('num') in (0, 1) for c in chs):
                return vid
        if any(c.get('num') == hui for c in chs):
            return vid
    return (okver or [None])[0]


def _paras(t):
    return [s.strip() for s in re.split(r'[\n\r]+', str(t or '')) if s.strip()]


def _add(recs, meta, ver, hui, ctype, kw, text):
    if not text or not str(text).strip():
        return
    for p in _paras(text):
        if not p:
            continue
        recs.append({
            'cid': meta['id'], 'who': meta.get('who', meta['id']),
            'tag': meta.get('tag', ''), 'color': meta.get('color', '#666'),
            'ver': ver, 'hui': hui, 'type': ctype, 'keyword': kw or '', 'text': p,
        })


def _parse(cid, meta, d, recs):
    ok = meta.get('okVer') or []

    if cid == 'jinpi':
        for vid in ('jin70_pi', 'jinshengtan', 'jin70'):
            chs = d.get(vid)
            if not chs:
                continue
            for k, entry in chs.items():
                try:
                    hui = int(k)
                except ValueError:
                    continue
                if not entry:
                    continue
                if entry.get('preface'):
                    _add(recs, meta, vid, hui, 'preface', '总批·序', entry['preface'])
                if entry.get('dufa'):
                    _add(recs, meta, vid, hui, 'huiping', '读法', entry['dufa'])
                if entry.get('houpi'):
                    _add(recs, meta, vid, hui, 'huiping', '回后总评', entry['houpi'])
                meipi = entry.get('meipi')
                if isinstance(meipi, list):
                    for m in meipi:
                        _add(recs, meta, vid, hui, 'meipi', '眉批',
                             m if isinstance(m, str) else m.get('text', ''))
                elif isinstance(meipi, dict):
                    for pos, items in meipi.items():
                        for m in (items if isinstance(items, list) else [items]):
                            _add(recs, meta, vid, hui, 'meipi', '眉批·' + pos,
                                 m if isinstance(m, str) else m.get('text', ''))
                inline = entry.get('inline')
                if isinstance(inline, list):
                    for m in inline:
                        _add(recs, meta, vid, hui, 'meipi', '夹批',
                             m if isinstance(m, str) else m.get('text', ''))
        return

    if cid == 'jiqin':
        ver = ok[0]
        for hui, block in d.items():
            try:
                h = int(hui)
            except (ValueError, TypeError):
                continue
            if not isinstance(block, dict):
                continue
            for k, txt in block.items():
                if not txt:
                    continue
                idx = txt.find('——')
                kw = txt[:idx] if 0 < idx < 30 else ''
                _add(recs, meta, ver, h, 'zhu', kw, txt)
        return

    if cid in ('lizhuo', 'yuanwy'):
        for a in (d.get('art_theory') or []):
            _add(recs, meta, ok[0], None, 'theory', a.get('keyword', ''),
                 (a.get('source', '') or '') + '\n' + (a.get('point', '') or ''))
        for ch in (d.get('chapters') or []):
            m = re.search(r'第\s*(\d+)\s*回', ch.get('chapter', '') or '')
            hui = int(m.group(1)) if m else (0 if '引首' in (ch.get('chapter', '') or '') else None)
            title = ch.get('title') or ch.get('chapter') or ''
            ver = _pick_ver(ok, hui)
            for c in (ch.get('preface_comments') or []):
                txt = c.get('text', '')
                kw = (c.get('author', '') + '·' + (c.get('source', '') or '')) if c.get('author') else None
                _add(recs, meta, ver, hui, 'preface', kw, txt)
            for c in (ch.get('chapter_comments') or []):
                _add(recs, meta, ver, hui, 'meipi', c.get('type', '批'), c.get('text', ''))
            for c in (ch.get('end_comments') or []):
                _add(recs, meta, ver, hui, 'huiping', '回末总评',
                     (c.get('author', '') + '：' if c.get('author') else '') + (c.get('text', '') or ''))
            for it in (ch.get('items') or []):
                _add(recs, meta, ver, hui, 'meipi', it.get('k', ''), it.get('v', ''))
        return

    if cid == 'zhongbo':
        for p in (d.get('pin_ren') or []):
            _add(recs, meta, ok[0], None, 'preface', '评' + p.get('name', ''), p.get('text', ''))
        xu = d.get('xu')
        if isinstance(xu, list) and xu and isinstance(xu[0], dict):
            for x in xu:
                _add(recs, meta, ok[0], 0, 'preface', '叙',
                     (x.get('k', '') or '') + '\n' + (x.get('v', '') or ''))
        for ch in (d.get('chapters') or []):
            ver = _pick_ver(ok, ch.get('num'))
            for it in (ch.get('items') or []):
                _add(recs, meta, ver, ch.get('num'), 'huiping', it.get('k', ''), it.get('v', ''))
        return

    if cid == 'wangping':
        for ch in (d.get('chapters') or []):
            m = re.search(r'第\s*(\d+)\s*回', ch.get('chapter', '') or '')
            hui = int(m.group(1)) if m else None
            ver = _pick_ver(ok, hui)
            ctype = 'huiping' if ch.get('type') == '回末总评' else 'meipi'
            _add(recs, meta, ver, hui, ctype, ch.get('type', '回评'), ch.get('text', ''))
        return

    if cid == 'yuxiangdou':
        if d.get('preface'):
            _add(recs, meta, ok[0], 0, 'preface', d['preface'].get('title', ''), d['preface'].get('text', ''))
        if d.get('bian'):
            _add(recs, meta, ok[0], 0, 'preface', d['bian'].get('title', ''), d['bian'].get('text', ''))
        for v in (d.get('volumes') or []):
            rng = v.get('hui') or []
            hui = rng[0] if rng else None
            ver = _pick_ver(ok, hui)
            for it in (v.get('items') or []):
                txt = it if isinstance(it, str) else (it.get('v') or it.get('text') or '')
                if not txt:
                    continue
                kw = '上栏评' if isinstance(it, str) else (it.get('k') or '上栏评')
                _add(recs, meta, ver, hui, 'meipi', kw, txt)
        return

    if cid == 'chengzhu':
        for v in (d.get('volumes') or []):
            hui = v.get('no')
            ver = _pick_ver(ok, hui)
            for it in (v.get('items') or []):
                _add(recs, meta, ver, hui, 'zhu', it.get('k', ''), it.get('v', ''))
        return

    if cid == 'yannanshang':
        ver = ok[0]
        if d.get('xu'):
            _add(recs, meta, ver, 0, 'preface', d['xu'].get('title', ''), d['xu'].get('text', ''))
        if d.get('huowen'):
            t = d['huowen']
            head = ('【' + str(t.get('title', '')) + '】'
                    + ('（' + str(t['status']) + '）' if t.get('status') else '')
                    + ('\n' + t['note'] if t.get('note') else ''))
            _add(recs, meta, ver, 0, 'preface', t.get('title', ''), head)
            for e in (t.get('excerpts') or []):
                _add(recs, meta, ver, 0, 'preface', '或问·存世引文',
                     (e.get('src') + '\n' if e.get('src') else '')
                     + (e.get('q', '') or '') + ('\n' + e['a'] if e.get('a') else ''))
        for s in (d.get('shiming') or []):
            _add(recs, meta, ver, 0, 'theory', '释名·' + s.get('name', ''), s.get('text', ''))
        for ch in (d.get('chapters') or []):
            _add(recs, meta, ver, ch.get('num', 0), 'meipi', '逐回评', ch.get('text', ''))
        return


def load_all(registry_path=REGISTRY):
    """加载全部批语，返回记录列表。"""
    with open(registry_path, encoding='utf-8') as f:
        reg = json.load(f)
    recs = []
    for meta in reg.get('commentaries', []):
        p = TEXTS / meta['file']
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        _parse(meta['id'], meta, d, recs)
    return recs


def count_by_hui(recs):
    """按批注家统计每条批语归属回次（卷首 -> 0）。"""
    from collections import defaultdict
    out = defaultdict(lambda: defaultdict(int))
    for r in recs:
        out[r['cid']][r['hui'] if r['hui'] is not None else 0] += 1
    return {k: dict(v) for k, v in out.items()}


def chars_by_hui(recs):
    """按批注家统计每条批语归属回次的字数。"""
    from collections import defaultdict
    out = defaultdict(lambda: defaultdict(int))
    for r in recs:
        out[r['cid']][r['hui'] if r['hui'] is not None else 0] += len(r['text'])
    return {k: dict(v) for k, v in out.items()}


if __name__ == '__main__':
    rs = load_all()
    print('总条数:', len(rs))
    from collections import Counter
    print('各家条数:', dict(Counter(r['cid'] for r in rs)))
