"""Step 3 · 评点接受史热力图

把九家批注的时间跨度（明万历 → 清初 → 当代）画成「哪一回最受关注」：
横轴回目 0–120，纵轴评点家按年代排序，色深 = 批语密度（可切「条数 / 字数」两种口径）。

产出：docs/data/critics_heatmap.json、docs/fig/reception.{png,svg}
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import critics, plotstyle  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'docs', 'data', 'critics_heatmap.json')

MAX_HUI = 120
# 评点家年代（用于纵轴排序）：id -> (年份, 朝代)
ERA = {
    'lizhuo': (1610, '明万历'),
    'yuxiangdou': (1611, '明万历'),
    'yuanwy': (1614, '明万历'),
    'zhongbo': (1625, '明末'),
    'jinpi': (1641, '明崇祯'),
    'wangping': (1660, '清初'),
    'chengzhu': (1750, '清乾隆'),
    'yannanshang': (1908, '清末'),
    'jiqin': (2014, '当代'),
}


def main():
    recs = critics.load_all()
    cnt = critics.count_by_hui(recs)
    chs = critics.chars_by_hui(recs)

    reg = json.load(open(os.path.join(REPO, 'docs', 'data', 'registry.json'), encoding='utf-8'))
    meta = {c['id']: c for c in reg['commentaries']}
    order = sorted(meta.keys(), key=lambda cid: ERA.get(cid, (9999, ''))[0])

    def row(d, cid):
        return [int(d.get(cid, {}).get(h, 0)) for h in range(0, MAX_HUI + 1)]

    matrix = {cid: row(cnt, cid) for cid in order}
    matrix_chars = {cid: row(chs, cid) for cid in order}

    out = {
        'generated': str(date.today()),
        'note': '纵轴按评点家年代排序；横轴回目 0（卷首/引首）–120。值 = 该回批语条数（或字数）。'
                '解析口径同站点批注检索页，总量应与检索页载入条数一致。',
        'max_hui': MAX_HUI,
        'critics': [{'id': cid, 'tag': meta[cid].get('tag', ''), 'who': meta[cid].get('who', ''),
                     'color': meta[cid].get('color', '#666'),
                     'year': ERA.get(cid, (0, ''))[0], 'era': ERA.get(cid, (0, ''))[1],
                     'total': int(sum(matrix[cid])), 'chars': int(sum(matrix_chars[cid])),
                     'has_vol_head': matrix[cid][0] > 0} for cid in order],
        'matrix_count': matrix,
        'matrix_chars': matrix_chars,
        'grand_total': int(sum(sum(v) for v in matrix.values())),
        'fig': 'fig/reception.png',
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 出图：条数热力图（行归一化，突出各家关注分布）----
    plotstyle.setup()
    M = np.array([matrix[c] for c in order], dtype=float)
    labels_y = ['%s·%s' % (meta[c].get('tag', ''), ERA.get(c, (0, ''))[1]) for c in order]
    fig, ax = plt.subplots(figsize=(12, 4.6))
    Mn = M / (M.max(axis=1, keepdims=True) + 1e-9)   # 行归一化，便于比较分布
    im = ax.imshow(Mn, aspect='auto', cmap='YlOrRd', interpolation='nearest')
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(labels_y)
    xt = list(range(0, MAX_HUI + 1, 10))
    ax.set_xticks(xt)
    ax.set_xticklabels([str(x) for x in xt])
    ax.set_xlabel('回目（0 = 卷首／引首）')
    ax.set_title('评点接受史热力图（行归一化 · 色深=该回批语相对密度）', fontsize=14)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.024, pad=0.02, label='相对密度')
    fig.tight_layout()
    plotstyle.save(fig, 'reception')

    print('九家总条数', out['grand_total'])
    for c in out['critics']:
        print('  %-6s %-8s %s  条数=%-5d 字数=%-6d' % (c['tag'], c['who'], c['era'], c['total'], c['chars']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
