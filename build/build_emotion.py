"""Step 4 · 情节情感曲线（全书心电图）

自建情感词典 -> 逐回打分 -> 滑动平滑 -> 峰值标注（打虎、风雪山神庙、江州劫法场、招安、
魂聚蓼儿洼等）。以繁／简原文为基准（不用白话层，避免生成噪声）。

产出：docs/data/emotion_curve.json、docs/fig/emotion.{png,svg}
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import corpus, plotstyle, sentiment, textutil as tu  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'docs', 'data', 'emotion_curve.json')

PICK = ['v120', 'v100', 'v70']
WIN = 3  # 滑动平滑窗口

# 公认情节高潮（按 120 回本回次标注），用于核对曲线峰值
EVENTS = {
    10: '林教头风雪山神庙',
    16: '智取生辰纲',
    23: '景阳冈武松打虎',
    26: '武松斗杀西门庆',
    31: '血溅鸳鸯楼',
    40: '江州劫法场',
    46: '三打祝家庄',
    65: '智取大名府',
    82: '全伙受招安',
    98: '征方腊惨烈',
    100: '鲁智深坐化·宋江之死（百回本结）',
    120: '宋公明神聚蓼儿洼',
}


def smooth(xs, w=WIN):
    out = []
    for i in range(len(xs)):
        a = max(0, i - w + 1)
        seg = xs[a:i + 1]
        out.append(sum(seg) / len(seg))
    return out


def main():
    c = corpus.Corpus()
    reg = json.load(open(os.path.join(REPO, 'docs', 'data', 'registry.json'), encoding='utf-8'))
    meta = {v['id']: v for v in reg['versions']}

    versions = {}
    for vid in PICK:
        nums = [n for n in c.nums(vid) if n >= 1]
        pts = []
        for n in nums:
            s = sentiment.score(tu.strip_note_markers(c.text(vid, n, 'fan')))
            pts.append({'num': n, 'pol': s['polarity'], 'aro': s['arousal'],
                        'nchar': s['nchar'], 'pos': s['pos'], 'neg': s['neg']})
        sm = smooth([p['pol'] for p in pts])
        sma = smooth([p['aro'] for p in pts])
        versions[vid] = {
            'name': meta[vid].get('name', vid),
            'short': meta[vid].get('short', vid),
            'color': meta[vid].get('color', '#666'),
            'points': [[p['num'], p['pol'], p['aro'], p['nchar']] for p in pts],
            'smoothed': [[pts[i]['num'], round(sm[i], 4)] for i in range(len(pts))],
            'smoothed_aro': [[pts[i]['num'], round(sma[i], 3)] for i in range(len(pts))],
            'mean_pol': round(sum(p['pol'] for p in pts) / len(pts), 4),
        }

    # 自动峰值（平滑曲线上的局部极大 + 突出度）
    base = versions['v120']
    smap = dict((int(a), b) for a, b in base['smoothed'])
    nums = sorted(smap)
    peaks = []
    for i in range(1, len(nums) - 1):
        n = nums[i]
        if smap[n] >= smap[nums[i - 1]] and smap[n] >= smap[nums[i + 1]]:
            prom = smap[n] - (smap[nums[i - 1]] + smap[nums[i + 1]]) / 2
            if prom > 0.02 and smap[n] > 0.15:
                peaks.append({'num': n, 'pol': round(smap[n], 3), 'prom': round(prom, 3)})
    peaks.sort(key=lambda p: -p['prom'])
    peaks = sorted(peaks[:12], key=lambda p: p['num'])

    events = []
    for n, label in sorted(EVENTS.items()):
        row = {'hui': n, 'label': label, 'values': {}}
        for vid, v in versions.items():
            m = {int(a): b for a, b in v['smoothed']}
            if n in m:
                row['values'][vid] = round(m[n], 3)
        events.append(row)

    out = {
        'generated': str(date.today()),
        'note': '以繁／简原文（不用白话层）逐回打分；polarity=(pos-neg)/(pos+neg+1)，'
                'arousal=激烈度词密度(每千字)；曲线经 %d 回滑动平滑。此为可计算指标，非定论。' % WIN,
        'lexicon_sizes': {'pos': len(sentiment.POS), 'neg': len(sentiment.NEG), 'arousal': len(sentiment.ARO)},
        'versions': versions,
        'peaks': peaks,
        'events': events,
        'fig': 'fig/emotion.png',
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 出图 ----
    plotstyle.setup()
    fig, ax = plt.subplots(figsize=(12, 4.8))
    for vid, v in versions.items():
        xs = [a for a, b in v['smoothed']]
        ys = [b for a, b in v['smoothed']]
        ax.plot(xs, ys, color=v['color'], lw=1.6, label='%s（%s）' % (v['short'], v['name'][:12]))
    for p in peaks:
        ax.axvline(p['num'], color=plotstyle.C['gold'], alpha=0.25, lw=1)
    ax.axhline(0, color=plotstyle.C['muted'], lw=0.8, ls='--')
    ax.set_xlabel('回目')
    ax.set_ylabel('情感极性（平滑）')
    ax.set_title('《水浒传》情节情感曲线（全书心电图）', fontsize=14)
    ax.legend(loc='lower left', fontsize=9)
    fig.tight_layout()
    plotstyle.save(fig, 'emotion')

    print('情感曲线版本:', list(versions))
    print('自动峰值:', [(p['num'], p['pol']) for p in peaks])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
