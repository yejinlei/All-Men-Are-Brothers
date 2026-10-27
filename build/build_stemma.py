"""Step 2 · 版本谱系树（Stemma）

对齐策略（关键）：
  各版本回次号与正文并不总是一致：
    · 金批繁本 jin70：其回次号比他本**偏移 +1**（第 0 号文件为「楔子」，之后为第一回…）；
    · 金批简本/古本七十 等：正文与回次号一致（仅回目文字有版本差异）。
  故统一换算到「故事回次 story」再比对：num = story + OFFSET[vid]。

距离双口径：
  · 特征 n-gram 余弦（2/3-gram），整段拼接后计算；
  · 字符级编辑距离，**逐逐回对齐**后取平均（规避整册长度不同导致的抽样错位）。
聚类：平均连接（UPGMA，scipy linkage）。

产出：docs/data/stemma.json、docs/fig/stemma.{png,svg}、docs/fig/stemma_heat.{png,svg}
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from datetime import date
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import corpus, plotstyle, textutil as tu  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.cluster.hierarchy import dendrogram, linkage  # noqa: E402
from scipy.spatial.distance import squareform  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'docs', 'data', 'stemma.json')
REG = os.path.join(REPO, 'docs', 'data', 'registry.json')

# 回次号 -> 故事回次 的偏移（num = story + OFFSET）
# 金批繁本 jin70：第 0 号文件（楔子）即故事第 1 回，故 story = num + 1，OFFSET = -1
OFFSET = {'jin70': -1}
CHAP_CAP = 1500  # 编辑距离：每回取前 1500 字比对


def story_range(vid, reg_range):
    lo = max(1, reg_range[0])
    return (lo, reg_range[1])


def num_for(vid, story):
    return story + OFFSET.get(vid, 0)


def chap_text(c, vid, story):
    n = num_for(vid, story)
    if c.chapter(vid, n) is None:
        return ''
    return tu.norm_text(c.text(vid, n, 'fan'))


def pair_overlap(r1, r2):
    lo, hi = max(r1[0], r2[0]), min(r1[1], r2[1])
    return (lo, hi) if lo <= hi else None


def ngram_cos_dist(a, b, ns=(2, 3)):
    ds = []
    for n in ns:
        va = Counter(tu.char_ngrams(a, n))
        vb = Counter(tu.char_ngrams(b, n))
        keys = set(va) | set(vb)
        dot = sum(va[k] * vb[k] for k in keys)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        ds.append(1.0 - (dot / (na * nb) if na and nb else 0.0))
    return sum(ds) / len(ds)


def edit_dist_story(c, vid_a, vid_b, story_lo, story_hi):
    """逐回（按故事回次对齐）计算编辑距离后取平均。"""
    rs = []
    for s in range(story_lo, story_hi + 1):
        a = chap_text(c, vid_a, s)[:CHAP_CAP]
        b = chap_text(c, vid_b, s)[:CHAP_CAP]
        if not a or not b:
            continue
        rs.append(1.0 - SequenceMatcher(None, a, b).ratio())
    return sum(rs) / len(rs) if rs else 1.0


def from_linkage(Z, labels):
    n = len(labels)
    nodes = {i: {'name': labels[i], 'children': [], 'h': 0.0, 'size': 1} for i in range(n)}
    for k in range(len(Z)):
        a, b, dist, cnt = Z[k]
        a, b = int(a), int(b)
        nodes[n + k] = {'name': '', 'children': [nodes[a], nodes[b]],
                        'h': round(float(dist), 4), 'size': int(cnt)}
    return nodes[2 * n - 2]


def cut_clusters(node, level):
    if not node['children']:
        return [node]
    if node['h'] > level:
        res = []
        for c in node['children']:
            res += cut_clusters(c, level)
        return res
    return [node]


def leaves_of(node):
    if not node['children']:
        return [node['name']]
    res = []
    for c in node['children']:
        res += leaves_of(c)
    return res


def main():
    c = corpus.Corpus()
    reg = json.load(open(REG, encoding='utf-8'))
    short = {v['id']: v['short'] for v in reg['versions']}
    system = {v['id']: v.get('system', '') for v in reg['versions']}
    ranges = {v['id']: story_range(v['id'], v['range']) for v in reg['versions'] if v.get('range')}

    vids = c.version_ids()
    labels = [short[v] for v in vids]
    n = len(vids)

    Dn = [[0.0] * n for _ in range(n)]
    De = [[0.0] * n for _ in range(n)]
    overlaps = {}
    for i in range(n):
        for j in range(i + 1, n):
            ov = pair_overlap(ranges[vids[i]], ranges[vids[j]])
            overlaps[f'{vids[i]}|{vids[j]}'] = list(ov) if ov else None
            if not ov:
                Dn[i][j] = Dn[j][i] = 1.0
                De[i][j] = De[j][i] = 1.0
                continue
            ta = ''.join(chap_text(c, vids[i], s) for s in range(ov[0], ov[1] + 1))
            tb = ''.join(chap_text(c, vids[j], s) for s in range(ov[0], ov[1] + 1))
            Dn[i][j] = Dn[j][i] = round(ngram_cos_dist(ta, tb), 4)
            De[i][j] = De[j][i] = round(edit_dist_story(c, vids[i], vids[j], ov[0], ov[1]), 4)

    Davg = [[round((Dn[i][j] + De[i][j]) / 2, 4) for j in range(n)] for i in range(n)]

    xs, ys = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if overlaps[f'{vids[i]}|{vids[j]}']:
                xs.append(Dn[i][j]); ys.append(De[i][j])
    corr = float(np.corrcoef(xs, ys)[0, 1]) if len(xs) > 1 else 0.0

    Z = linkage(squareform(np.array(Davg), checks=False), method='average')
    tree = from_linkage(Z, labels)
    maxh = float(max(row[2] for row in Z))
    level = 0.5 * maxh
    clusters = cut_clusters(tree, level)

    cache = {}

    def chap_vec(vid, story):
        k = (vid, story)
        if k not in cache:
            cache[k] = Counter(tu.char_ngrams(chap_text(c, vid, story), 2))
        return cache[k]

    def chap_dist(v1, v2, story):
        a, b = chap_vec(v1, story), chap_vec(v2, story)
        keys = set(a) | set(b)
        dot = sum(a[k] * b[k] for k in keys)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return 1.0 - (dot / (na * nb) if na and nb else 0.0)

    def ref_title(story):
        return c.title('v120', story) or c.title('v100', story) or ('第%d回' % story)

    cluster_out = []
    for node in clusters:
        members = leaves_of(node)
        ids = [vids[labels.index(m)] for m in members]
        s_lo = max(ranges[i][0] for i in ids)
        s_hi = min(ranges[i][1] for i in ids)
        rows = []
        if len(ids) >= 2 and s_lo <= s_hi:
            for s in range(s_lo, s_hi + 1):
                if any(not chap_text(c, i, s) for i in ids):
                    continue
                ds = [chap_dist(ids[x], ids[y], s)
                      for x in range(len(ids)) for y in range(x + 1, len(ids))]
                rows.append((sum(ds) / len(ds), s))
        rows.sort(reverse=True)
        tight = round(sum(r[0] for r in rows) / len(rows), 4) if rows else 0.0
        evidence = [{'num': s, 'title': ref_title(s)[:34], 'dist': round(d, 3)} for d, s in rows[:8]]
        cluster_out.append({'name': ' / '.join(sorted({system[i] for i in ids})),
                            'members': members, 'tightness': tight, 'evidence': evidence})

    off = sorted({Davg[i][j] for i in range(n) for j in range(i + 1, n)})
    thr = float(np.quantile(np.array(off), 0.30))
    edges = [{'source': labels[i], 'target': labels[j], 'dist': Davg[i][j]}
             for i in range(n) for j in range(i + 1, n) if Davg[i][j] <= thr]

    def g(a, b):
        return Davg[vids.index(a)][vids.index(b)]

    def vd(cond, yes, no):
        return yes if cond else no

    findings = [
        {'q': '袁本(v120) 与 容本(v100) 1–100 回', 'value': g('v120', 'v100'),
         'verdict': vd(g('v120', 'v100') < 0.06, '近似同源', '主要回次同源')},
        {'q': '金本系统内部（v70 / jin70_pi / jinshengtan）',
         'value': max(g('v70', 'jin70_pi'), g('v70', 'jinshengtan'), g('jin70_pi', 'jinshengtan')),
         'verdict': '极近，同一系统'},
        {'q': '金批繁本(jin70) 与 古本七十(v70)', 'value': g('jin70', 'v70'),
         'verdict': vd(g('jin70', 'v70') < 0.15, '同属七十回金本系统', '系统不同')},
        {'q': 'zsk 与 v120 的 82–120 回', 'value': g('zsk', 'v120'),
         'verdict': vd(g('zsk', 'v120') < 0.05, '文字同源（现存语料为繁本文字）', '存在差异')},
        {'q': '金本系统 与 繁本系统 分离', 'value': g('v70', 'v100'),
         'verdict': vd(g('v70', 'v100') > 0.12, '分为两系', '差异不大')},
    ]

    out = {
        'generated': str(date.today()),
        'method': '统一换算到「故事回次」后比对（纠正金批繁本回次偏移）；'
                  '特征 n-gram 余弦(2/3-gram) + 逐回字符级编辑距离双口径互校；平均连接(UPGMA)聚类。',
        'offsets': OFFSET,
        'versions': [{'id': v, 'short': short[v], 'system': system.get(v, ''),
                      'range': ranges.get(v)} for v in vids],
        'labels': labels,
        'matrix': {'ngram': {vids[i]: {vids[j]: Dn[i][j] for j in range(n)} for i in range(n)},
                   'edit': {vids[i]: {vids[j]: De[i][j] for j in range(n)} for i in range(n)},
                   'avg': {vids[i]: {vids[j]: Davg[i][j] for j in range(n)} for i in range(n)}},
        'overlaps': overlaps,
        'tree': tree,
        'cluster_level': round(level, 4),
        'clusters': cluster_out,
        'network_threshold': round(thr, 4),
        'network_edges': edges,
        'findings': findings,
        'corr_edit_ngram': round(corr, 3),
        'fig': 'fig/stemma.png',
        'fig_heat': 'fig/stemma_heat.png',
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    plotstyle.setup()
    fig, ax = plt.subplots(figsize=(9, 5))
    dendrogram(Z, labels=labels, ax=ax, color_threshold=level,
               above_threshold_color=plotstyle.C['muted'])
    ax.set_title('《水浒传》版本谱系树（平均连接聚类 · 距离越小越近）', fontsize=14)
    ax.set_ylabel('版本间距离')
    ax.grid(False)
    fig.tight_layout()
    plotstyle.save(fig, 'stemma')

    fig2, ax2 = plt.subplots(figsize=(6.8, 5.8))
    M = np.array(Davg)
    im = ax2.imshow(M, cmap='YlOrRd', interpolation='nearest')
    ax2.set_xticks(range(n)); ax2.set_yticks(range(n))
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.set_yticklabels(labels)
    for i in range(n):
        for j in range(n):
            ax2.text(j, i, f'{M[i][j]:.2f}', ha='center', va='center',
                     fontsize=7.5, color=plotstyle.C['ink'])
    ax2.set_title('版本距离矩阵（n-gram 与编辑距离均值）', fontsize=13)
    fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04, label='距离')
    fig2.tight_layout()
    plotstyle.save(fig2, 'stemma_heat')

    print('版本数', n, '| edit-ngram 相关', round(corr, 3))
    print('切分高度', round(level, 3), '->', len(cluster_out), '簇')
    for cl in cluster_out:
        print('  簇:', cl['members'], '| 紧致度', cl['tightness'])
    for f in findings:
        print('  ·', f['q'], '=', f['value'], '=>', f['verdict'])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
