"""Step 8　梁山组织架构：把 108 将按 星号（天罡/地煞）· 派系 · 职务分组 整理成结构化编制表。

只读 docs/data/heroes/heroes.json，产出 docs/data/org.json 供 docs/hierarchy.html 渲染。
"""
from __future__ import annotations
import sys, os, json, datetime
from collections import OrderedDict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import pagegen  # noqa: F401  (仅确保同目录可导入，保持一致)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
SRC = os.path.join(DOCS, 'data', 'heroes', 'heroes.json')
IMG_DIR = os.path.join(DOCS, 'img', 'heroes')
OUT = os.path.join(DOCS, 'data', 'org.json')

# 姓名→画像文件名的特例（数据未登记 image 字段、且拼音规则不适用者）
IMG_ALIAS = {'单廷圭': 'shantingui'}


def portrait(rec, files):
    """画像路径：先取登记字段，再按姓名拼音推断（含特例），只返回真实存在的文件。"""
    cands = []
    if rec.get('image'):
        cands.append(os.path.basename(rec['image']))
    if rec.get('name') in IMG_ALIAS:
        cands.append(IMG_ALIAS[rec['name']] + '.jpg')
    try:
        from pypinyin import lazy_pinyin
        cands.append(''.join(lazy_pinyin(rec['name'])) + '.jpg')
    except Exception:
        pass
    for c in cands:
        if c in files:
            return 'img/heroes/' + c
    return ''



def main():
    raw = json.load(open(SRC, encoding='utf-8'))
    heroes = raw['heroes'] if isinstance(raw, dict) else raw
    heroes = sorted(heroes, key=lambda r: r['rank'])
    files = set(os.listdir(IMG_DIR)) if os.path.isdir(IMG_DIR) else set()

    members = []
    for r in heroes:
        tier = '天罡' if r['rank'] <= 36 else '地煞'
        members.append(OrderedDict([
            ('rank', r['rank']), ('star', r['star']), ('nickname', r['nickname']),
            ('name', r['name']), ('tier', tier), ('position', r.get('position', '')),
            ('faction', r.get('faction', '')), ('group', r.get('group', '')),
            ('weapon', r.get('weapon', '')), ('origin', r.get('origin', '')),
            ('appear', r.get('appear')), ('end', r.get('end', '')),
            ('desc', r.get('desc', '')),
            ('img', portrait(r, files)),
        ]))

    tian = [m for m in members if m['tier'] == '天罡']
    di = [m for m in members if m['tier'] == '地煞']

    def tally(key):
        buckets = OrderedDict()
        for m in members:
            buckets.setdefault(m[key] or '未分', []).append(m)
        out = []
        for k, ms in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            tc = Counter(x['tier'] for x in ms)
            out.append(OrderedDict([
                ('name', k), ('count', len(ms)),
                ('tiangang', tc.get('天罡', 0)), ('disha', tc.get('地煞', 0)),
                ('members', [x['rank'] for x in ms]),
            ]))
        return out

    payload = OrderedDict([
        ('generated', datetime.date.today().isoformat()),
        ('source', 'data/heroes/heroes.json'),
        ('note', '星号与座次取自原著石碣排座；派系按上山来源归类，职务分组按原著「分调众将」职守归并。'),
        ('total', len(members)),
        ('tiangang', len(tian)),
        ('disha', len(di)),
        ('n_factions', len({m['faction'] for m in members})),
        ('n_groups', len({m['group'] for m in members})),
        ('tiers', [
            OrderedDict([('key', 'tiangang'), ('name', '天罡星三十六员'), ('count', len(tian)),
                         ('members', [m['rank'] for m in tian])]),
            OrderedDict([('key', 'disha'), ('name', '地煞星七十二员'), ('count', len(di)),
                         ('members', [m['rank'] for m in di])]),
        ]),
        ('factions', tally('faction')),
        ('groups', tally('group')),
        ('members', members),
    ])

    json.dump(payload, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('写出', os.path.relpath(OUT, ROOT))
    print('总人数 %d（天罡 %d / 地煞 %d）｜派系 %d 类｜职务分组 %d 类'
          % (payload['total'], payload['tiangang'], payload['disha'], payload['n_factions'], payload['n_groups']))
    print('派系分布:', '，'.join('%s%d' % (f['name'], f['count']) for f in payload['factions']))
    print('职务分组:', '，'.join('%s%d' % (g['name'], g['count']) for g in payload['groups']))
    print('文件大小 %.1f KB' % (os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()
