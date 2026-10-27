"""Step 7 · 文体计量（检验学术悬念）

把 120 回本按叙事段落切块（聚义 / 招安 / 征辽 / 征田虎 / 征王庆 / 征方腊），
用「功能词频率 + 字符 2-gram 分布」刻画各段文体，回答一个老问题：
  —— 征田虎、王庆两段（一般认为非原本、系后人增补）在文体上是否确实偏离前 71 回？

方法：特征向量 -> 余弦相似度矩阵 -> 平均连接聚类 -> 滑动窗口归类。
产出：docs/data/stylometry.json、docs/fig/stylometry.{png,svg}
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import corpus, plotstyle, textutil as tu  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.cluster.hierarchy import dendrogram, linkage  # noqa: E402
from scipy.spatial.distance import squareform  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'docs', 'data', 'stylometry.json')

BASE_VER = 'v120'
# 叙事段落（按 120 回本通行划分）
SECTIONS = [
    ('梁山聚义', 1, 71),
    ('受招安', 72, 82),
    ('征辽', 83, 89),
    ('征田虎', 90, 100),
    ('征王庆', 101, 110),
    ('征方腊', 111, 120),
]
FUNC_WORDS = list('之 乎 者 也 而 其 以 於 于 為 为 與 与 及 則 则 乃 且 若 所 焉 矣 哉 夫 但 卻 却 便 即 又 也 都 只 等 得 了 著 着 把 被 將 将 是 不 在 有 無 无 我 你 他 們 们 這 这 那 來 来 去 說 说 道 個 个 兩 两'.split())
NGRAM_TOP = 300
WIN = 8


def main():
    c = corpus.Corpus()
    nums = [n for n in c.nums(BASE_VER) if n >= 1]

    def text_of(lo, hi, lang='fan'):
        return ''.join(tu.norm_text(c.text(BASE_VER, n, lang)) for n in nums if lo <= n <= hi)

    # ---- 段落特征 ----
    sec_texts = [(name, lo, hi, text_of(lo, hi)) for name, lo, hi in SECTIONS]

    alltext = ''.join(t for *_, t in sec_texts)
    ng = Counter(tu.char_ngrams(alltext, 2))
    top_ng = [w for w, _ in ng.most_common(NGRAM_TOP)]

    def vec(text):
        n = len(text) or 1
        fw = np.array([text.count(w) / n for w in FUNC_WORDS])
        cv = Counter(tu.char_ngrams(text, 2))
        gn = np.array([cv.get(w, 0) / n for w in top_ng])
        return np.concatenate([fw, gn])

    mat = np.array([vec(t) for *_, t in sec_texts])

    def cos(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(a @ b / (na * nb)) if na and nb else 0.0

    sim = [[round(cos(mat[i], mat[j]), 4) for j in range(len(mat))] for i in range(len(mat))]
    dist = [[round(1 - sim[i][j], 4) for j in range(len(mat))] for i in range(len(mat))]
    names = [s[0] for s in sec_texts]

    Zl = linkage(squareform(np.array(dist), checks=False), method='average')
    tree = {'name': '', 'h': 0.0, 'children': []}
    nodes = {i: {'name': names[i], 'h': 0.0, 'children': []} for i in range(len(names))}
    for k in range(len(Zl)):
        a, b, dd, cnt = Zl[k]
        nodes[len(names) + k] = {'name': '', 'h': round(float(dd), 4),
                                 'children': [nodes[int(a)], nodes[int(b)]]}
    tree = nodes[2 * len(names) - 2]

    # ---- 滑动窗口归类（窗口 8 回，步长 1）----
    centro = mat / np.linalg.norm(mat, axis=1, keepdims=True)
    rolling = []
    for s in range(1, max(nums) - WIN + 2):
        seg = ''.join(tu.norm_text(c.text(BASE_VER, n, 'fan')) for n in range(s, s + WIN) if n in nums)
        v = vec(seg)
        nv = np.linalg.norm(v)
        if not nv:
            continue
        vn = v / nv
        sims = [float(vn @ centro[i]) for i in range(len(names))]
        best = int(np.argmax(sims))
        rolling.append({'start': s, 'end': s + WIN - 1, 'section': best,
                        'sim': round(sims[best], 4), 'margin': round(sorted(sims)[-1] - sorted(sims)[-2], 4)})

    # ---- 田虎/王庆段与聚义段的文体距离（核心悬念）----
    i_ju = names.index('梁山聚义')
    focus = {}
    for nm in ['征辽', '征田虎', '征王庆', '征方腊']:
        i = names.index(nm)
        focus[nm] = round(1 - cos(mat[i_ju], mat[i]), 4)

    out = {
        'generated': str(date.today()),
        'method': '功能词频率(%d) + 高频字符 2-gram 分布(%d) 合成特征向量，L1 归一后取余弦；'
                  '平均连接聚类；滑动窗口(宽%d回)按最近段落质心归类。' % (len(FUNC_WORDS), NGRAM_TOP, WIN),
        'caveat': '文体计量给出的是「可计算假设」，非定论：段落划分、特征选择与样本长度都会影响结果；'
                  '征田虎/王庆之争仍须以版本与文献证据为准。',
        'base_version': BASE_VER,
        'sections': [{'name': n, 'from': lo, 'to': hi, 'chars': len(t)} for n, lo, hi, t in sec_texts],
        'func_words': FUNC_WORDS,
        'top_ngrams': top_ng[:60],
        'sim': sim, 'dist': dist, 'tree': tree,
        'rolling': rolling,
        'focus_dist_from_juyi': focus,
        'fig': 'fig/stylometry.png',
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 出图 ----
    plotstyle.setup()
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    ax = axes[0]
    M = np.array(sim)
    im = ax.imshow(M, cmap='YlGnBu', vmin=min(0.9, M.min()), vmax=1.0, interpolation='nearest')
    ax.set_xticks(range(len(names))); ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=40, ha='right'); ax.set_yticklabels(names)
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f'{M[i][j]:.2f}', ha='center', va='center', fontsize=7)
    ax.set_title('段落文体相似度矩阵', fontsize=13)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='余弦相似度')

    ax2 = axes[1]
    ymap = {i: i for i in range(len(names))}
    xs = [r['start'] for r in rolling]
    ys = [r['section'] for r in rolling]
    ax2.scatter(xs, ys, c=[plotstyle.PALETTE[y % len(plotstyle.PALETTE)] for y in ys], s=18)
    ax2.set_yticks(range(len(names))); ax2.set_yticklabels(names)
    ax2.set_xlabel('窗口起始回目（宽 %d 回）' % WIN)
    ax2.set_title('滑动窗口归属（文体落点）', fontsize=13)
    fig.tight_layout()
    plotstyle.save(fig, 'stylometry')

    print('段落:', names)
    print('与「梁山聚义」的文体距离:', focus)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
