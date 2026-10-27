"""Step 5 · 人物网络演化 + Step 6 · 删点实验

Step 5：为每条人-人关系补「首次成关系回目」（优先取 relation.chapter，缺则取两端人物出场回
        的较大者），供页面按回目滑杆逐步生长网络。
Step 6：以度/介数/接近中心性刻画影响力，并做「删点实验」——依次移除关键人物，重算
        连通分量、最大分量占比、平均路径长度与聚类系数，回答「梁山离了谁就散架」。

产出：docs/data/relation_timeline.json、docs/data/centrality.json、docs/fig/centrality.{png,svg}
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import plotstyle  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'docs', 'data', 'person_relations.json')
OUT_T = os.path.join(REPO, 'docs', 'data', 'relation_timeline.json')
OUT_C = os.path.join(REPO, 'docs', 'data', 'centrality.json')

# 删点实验关注的关键人物（社会学/叙事学意义上的枢纽 + 高连接度者）
KEY = ['宋江', '吴用', '卢俊义', '李逵', '武松', '林冲', '鲁智深', '公孙胜', '花荣', '戴宗', '关胜', '柴进']


def hui_of(text, default=None):
    m = re.search(r'第\s*(\d+)\s*回', text or '')
    return int(m.group(1)) if m else default


def main():
    d = json.load(open(SRC, encoding='utf-8'))
    persons = d['persons']
    edges = d['edges']
    types = d['types']

    node_first = {}
    for p in persons:
        node_first[p['name']] = hui_of(p.get('appear', ''), None)

    nodes = [{'id': p['name'], 'name': p['name'], 'rank': p.get('rank'),
              'nickname': p.get('nickname', ''), 'star': p.get('star', ''),
              'faction': p.get('faction', ''), 'first_hui': node_first.get(p['name'])}
             for p in persons]

    out_edges = []
    for e in edges:
        fh = hui_of(e.get('chapter', ''))
        if fh is None:
            a = node_first.get(e['source']); b = node_first.get(e['target'])
            cand = [x for x in (a, b) if x]
            fh = max(cand) if cand else None
        out_edges.append({'source': e['source'], 'target': e['target'],
                          'type': e['type'], 'first_hui': fh,
                          'desc': (e.get('desc', '') or '')[:80]})

    max_hui = 120
    tl = {
        'generated': str(date.today()),
        'note': '边的「首次成关系回目」优先取 relation.chapter；缺则该取两端人物出场回的较大者（估算）。'
                '节点出场回取自人物表 appear 字段。滑杆按回目累积点亮。',
        'types': types,
        'nodes': nodes,
        'edges': out_edges,
        'max_hui': max_hui,
    }
    json.dump(tl, open(OUT_T, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------- Step 6 中心性 ----------------
    # 完整图（含职级从属）用于统计；中心性/删点实验在「核心关系网」上做——
    # 职级从属关系近乎全部以宋江为上级，会形成单星结构，掩盖人物间真实关系。
    G = nx.Graph()
    for p in persons:
        G.add_node(p['name'])
    seen = set()
    for e in edges:
        key = tuple(sorted((e['source'], e['target'])))
        if key in seen:
            continue
        seen.add(key)
        G.add_edge(e['source'], e['target'], type=e['type'])
    n_pairs = len(seen)

    C = nx.Graph()
    for p in persons:
        C.add_node(p['name'])
    for e in edges:
        if e['type'] == '上下级':
            continue
        if not C.has_edge(e['source'], e['target']):
            C.add_edge(e['source'], e['target'], type=e['type'])

    deg = dict(C.degree())
    bet = nx.betweenness_centrality(C)
    clo = nx.closeness_centrality(C)

    def top(dct, k=15):
        return [{'name': n, 'value': round(v, 4)} for n, v in
                sorted(dct.items(), key=lambda kv: -kv[1])[:k]]

    base_comp = nx.number_connected_components(C)
    base_giant = max((len(c) for c in nx.connected_components(C)), default=0)
    Gg = C.subgraph(max(nx.connected_components(C), key=len)).copy()
    base_pl = nx.average_shortest_path_length(Gg) if Gg.number_of_nodes() > 1 else 0.0
    base_clu = nx.average_clustering(C)

    key_present = [p for p in KEY if p in C]
    experiments = []
    for name in key_present:
        H = C.copy()
        H.remove_node(name)
        comps = list(nx.connected_components(H))
        giant = max((len(c) for c in comps), default=0)
        Hg = H.subgraph(max(comps, key=len)).copy() if comps else H
        pl = nx.average_shortest_path_length(Hg) if Hg.number_of_nodes() > 1 else 0.0
        clu = nx.average_clustering(H) if H.number_of_nodes() else 0.0
        experiments.append({
            'name': name,
            'components': len(comps),
            'giant_ratio': round(giant / (C.number_of_nodes() - 1), 4) if C.number_of_nodes() > 1 else 0,
            'giant_size': giant,
            'avg_path': round(pl, 4),
            'clustering': round(clu, 4),
            'd_components': len(comps) - base_comp,
            'd_giant': giant - base_giant,
        })
    experiments.sort(key=lambda r: (r['d_giant'], -r['components']))

    out = {
        'generated': str(date.today()),
        'method': '中心性与删点实验在「核心关系网」（剔除职级从属）上进行：职级从属关系近乎全部'
                  '以宋江为上级，会形成单星结构、掩盖人物间真实关系。完整关系网见 relation_timeline.json。',
        'n_nodes': C.number_of_nodes(), 'n_edges': C.number_of_edges(),
        'full_graph': {'n_nodes': G.number_of_nodes(), 'n_edges': G.number_of_edges(),
                       'n_relations': len(edges), 'n_unique_pairs': n_pairs},
        'baseline': {'components': base_comp, 'giant_size': base_giant,
                     'giant_ratio': round(base_giant / C.number_of_nodes(), 4),
                     'avg_path': round(base_pl, 4), 'clustering': round(base_clu, 4)},
        'top_degree': top(deg), 'top_betweenness': top(bet), 'top_closeness': top(clo),
        'experiments': experiments,
        'fig': 'fig/centrality.png',
    }
    json.dump(out, open(OUT_C, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 出图：度中心性 top15 条形 ----
    plotstyle.setup()
    names = [r['name'] for r in out['top_degree']]
    vals = [r['value'] for r in out['top_degree']]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(range(len(names))[::-1], vals, color=plotstyle.C['vermilion'], alpha=0.85)
    ax.set_yticks(range(len(names))[::-1])
    ax.set_yticklabels(names)
    ax.set_xlabel('度中心性（直接关系数）')
    ax.set_title('人物度中心性 Top15', fontsize=14)
    fig.tight_layout()
    plotstyle.save(fig, 'centrality')

    print('节点', out['n_nodes'], '边', out['n_edges'], '| 基线分量', base_comp, '巨片', base_giant)
    print('Top5 度:', [(r['name'], r['value']) for r in out['top_degree'][:5]])
    print('删点影响(按巨片变化):', [(r['name'], r['d_giant'], r['components']) for r in experiments[:6]])
    print('wrote', OUT_T, '/', OUT_C)


if __name__ == '__main__':
    main()
