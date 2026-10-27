"""语料装载器：按版本 / 回次 / 语体读取，跨版本以『回次 num』对齐。

数据源：docs/texts/versions/versions_index.json（版本 <-> 章节文件映射）。
"""
from __future__ import annotations

import json
from pathlib import Path

from . import textutil as tu

REPO = Path(__file__).resolve().parents[2]
TEXTS = REPO / 'docs' / 'texts' / 'versions'
INDEX = TEXTS / 'versions_index.json'

# 语体 -> 索引里的文件字段名
LANG_FILE = {'fan': 'file', 'jian': 'file_simp', 'bai': 'file_bai'}
LANGS = ('fan', 'jian', 'bai')
LANG_NAME = {'fan': '繁体', 'jian': '简体', 'bai': '白话'}


class Corpus:
    def __init__(self, index_path=INDEX):
        self.index_path = Path(index_path)
        with open(self.index_path, encoding='utf-8') as f:
            self._idx = json.load(f)
        self._by_id = {v['id']: v for v in self._idx['versions']}
        self._ch = {
            vid: {c['num']: c for c in v.get('chapters', [])}
            for vid, v in self._by_id.items()
        }
        self._cache = {}

    # ---------------- 版本 ----------------
    def version_ids(self):
        return [v['id'] for v in self._idx['versions']]

    def version(self, vid):
        return self._by_id[vid]

    def name(self, vid):
        return self._by_id[vid].get('name', vid)

    # ---------------- 回次 ----------------
    def nums(self, vid):
        return sorted(self._ch[vid].keys())

    def chapters(self, vid):
        """按回次升序返回该版本的章目记录列表。"""
        return [self._ch[vid][n] for n in sorted(self._ch[vid].keys())]

    def chapter(self, vid, num):
        return self._ch[vid].get(num)

    def title(self, vid, num):
        c = self.chapter(vid, num)
        return c['title'] if c else ''

    # ---------------- 文本 ----------------
    def text(self, vid, num, lang='fan'):
        """取某版本某回某语体的原文；不存在则返回空串。"""
        key = (vid, num, lang)
        if key in self._cache:
            return self._cache[key]
        c = self.chapter(vid, num)
        s = ''
        if c:
            rel = c.get(LANG_FILE[lang])
            if rel:
                p = TEXTS / vid / rel
                if p.exists():
                    s = p.read_text(encoding='utf-8')
        self._cache[key] = s
        return s

    def char_count(self, vid, num, lang='fan', clean=False):
        """汉字数；clean=True 时先剥离冀勤注体例的注号。"""
        s = self.text(vid, num, lang)
        if clean:
            s = tu.strip_note_markers(s)
        return len(tu.cjk_only(s))

    def total_chars(self, vid, lang='fan'):
        return sum(self.char_count(vid, n, lang) for n in self.nums(vid))

    # ---------------- 对齐 ----------------
    def common_nums(self, vids, lo=1, hi=None):
        """多版本共有的回次（以 num 为锚，跳过引首 0）。"""
        s = None
        for v in vids:
            ns = set(self.nums(v))
            s = ns if s is None else (s & ns)
        s = s or set()
        return sorted(n for n in s if n >= lo and (hi is None or n <= hi))

    def align(self, vids, num, lang='fan'):
        """同一回次在各版本下的文本打包。"""
        return {v: self.text(v, num, lang) for v in vids}
