# -*- coding: utf-8 -*-
"""
从本体库 kg_abox.json 抽取「人物—人物」社会关系，生成前端轻量数据
docs/data/person_relations.json

输出结构：
{
  "types":   [{name,color,count}],           # 5 类人-人关系
  "persons": [{id,name,rank,nickname,star,faction,appear}],
  "edges":   [{source,target,type,chapter,weight,desc}]
}
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'data', 'kg_abox.json')
OUT = os.path.join(ROOT, 'docs', 'data', 'person_relations.json')

# 仅取 domain=Person 且 range=Person 的关系类型
TYPES = ['结拜为兄弟', '亲属', '师徒', '敌对', '上下级']
COLOR = {
    '结拜为兄弟': '#C4403A',
    '亲属': '#C87C8C',
    '师徒': '#6B8E4E',
    '敌对': '#444444',
    '上下级': '#9a9a9a',
}

d = json.load(open(SRC, encoding='utf-8'))
idmap = {h['id']: h['name'] for h in d['heroes'] if h.get('id')}

edges, deg = [], collections.Counter()
seen = set()
for r in d['relations']:
    if r['type'] not in TYPES:
        continue
    s = idmap.get(r['from'], r['from'])
    t = idmap.get(r['to'], r['to'])
    if s == t:
        continue
    key = (s, t, r['type'])
    if key in seen:          # 去重：同一对人物的同类关系只保留一条
        continue
    seen.add(key)
    edges.append({
        'source': s,
        'target': t,
        'type': r['type'],
        'chapter': r.get('chapter', ''),
        'weight': r.get('weight', 0),
        'desc': r.get('desc', ''),
    })
    deg[s] += 1
    deg[t] += 1

persons = []
for h in d['heroes']:
    n = h.get('name')
    if not n or n not in deg:
        continue
    persons.append({
        'id': h.get('id', ''),
        'name': n,
        'rank': h.get('rank') or 0,
        'nickname': h.get('nickname', ''),
        'star': h.get('star', ''),
        'faction': h.get('faction', ''),
        'appear': h.get('appear_chapter', ''),
        'degree': deg[n],
    })
persons.sort(key=lambda x: (x['rank'] or 999))

out = {
    'types': [{'name': t, 'color': COLOR[t],
               'count': sum(1 for e in edges if e['type'] == t)} for t in TYPES],
    'persons': persons,
    'edges': edges,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

print('已生成', OUT)
print('  人物:', len(persons), ' 关系:', len(edges))
for t in out['types']:
    print('   ', t['name'], t['count'])
print('  文件大小: %.1f KB' % (os.path.getsize(OUT) / 1024))
