#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 17 · 把「真本影像」层挂到 docs/data/facsimiles.json。

统一 real_images 结构（页面只按这一种结构渲染）：
  real_images = {
     title, sub, credit, note, available_here,
     groups: [ { group, label, note, images: [ {file, caption, orig} ] } ]
  }
- guohua 容与堂本：真本扫描（日本国立公文书馆 IIIF，站内小图；orig 指向原分辨率直链）
- zhongbo 钟伯敬本：真本绣像（书格 CDN 小图；orig 指向站内同图）
体积策略：站内单张 ≤ 200KB；原分辨率图一律不入仓，只登记外部直链。
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, 'docs', 'data', 'facsimiles.json')
NAJ_INDEX = os.path.join(ROOT, 'raw', 'facsimiles', 'rongyutang_index.json')
ZHONG_DIR = os.path.join(ROOT, 'docs', 'img', 'facsimile', 'zhong')

CAP_KB = 200


def build_rongyutang() -> dict:
    idx = json.load(open(NAJ_INDEX, encoding='utf-8'))
    groups = []
    total = 0
    for b in idx['books']:
        imgs = []
        for p in b['pages']:
            total += 1
            imgs.append({
                'file': p['file'],
                'caption': f"{b['volume_label']}·第{p['leaf']}叶",
                'orig': p.get('orig_full') or p['file'],
                'w': p.get('w'), 'h': p.get('h'), 'bytes': p.get('bytes'),
            })
        if imgs:
            groups.append({
                'group': b['volume'],
                'label': f"{b['volume_label']}（{b['label']}）",
                'note': f"共 {b['total_canvases']} 叶，本站入库 {len(imgs)} 叶"
                        + ('' if len(imgs) == b['total_canvases'] else '（抽样）'),
                'images': imgs,
            })
    return {
        'title': '原刻本扫描叶 · 真本影像',
        'sub': '李卓吾先生批評忠義水滸伝（容与堂本）· 日本国立公文書館藏 · '
               '卷之一全卷入库，卷十九/卷二十抽样',
        'credit': '国立公文書館デジタルアーカイブ（National Archives of Japan）藏本扫描，'
                  '公版古籍，依该馆「二次利用」条款在线使用',
        'note': '站内图为按 IIIF 尺寸参数压缩后的小图（长边 1200px、单张 ≤ %dKB）；'
                '点击任一叶打开原分辨率直链（外部、单叶数 MB，不入仓）。'
                '　<a href="read.html?vid=v100&ch=1">对照本站文字层（容百回本）→</a>' % CAP_KB,
        'available_here': total,
        'groups': groups,
    }


def build_zhongbo() -> dict:
    files = sorted(f for f in os.listdir(ZHONG_DIR) if f.lower().endswith('.jpg')) if os.path.isdir(ZHONG_DIR) else []
    imgs = []
    for f in files:
        fp = os.path.join(ZHONG_DIR, f)
        imgs.append({
            'file': f'img/facsimile/zhong/{f}',
            'caption': '绣像',
            'orig': f'img/facsimile/zhong/{f}',
            'bytes': os.path.getsize(fp),
        })
    return {
        'title': '书前绣像 · 真本影像',
        'sub': '钟伯敬先生批评水浒忠义传 · 明天启四知馆刊本 · 法国国家图书馆藏 CHINOIS 3992–3994',
        'credit': '书格（shuge.org）整理公开的法图藏原色扫描，公版影像',
        'note': '书前绣像共 39 幅，本站入库 %d 幅（站内小图）；其余及全部正文页请经下方「书格原色高清 PDF」'
                '下载整本（5.29 GB，法国图藏四知馆本 + 京都大学积庆堂本两种）。' % len(imgs),
        'available_here': len(imgs),
        'groups': [{'group': 'xiuxiang', 'label': '书前绣像（真本原色扫描）',
                    'note': '已入库 %d / 39 幅' % len(imgs), 'images': imgs}],
    }


def main():
    doc = json.load(open(JSON_PATH, encoding='utf-8'))
    builders = {'guohua': build_rongyutang, 'zhongbo': build_zhongbo}
    for f in doc['facsimiles']:
        if f['id'] in builders:
            f['real_images'] = builders[f['id']]()
            n = sum(len(g['images']) for g in f['real_images']['groups'])
            print(f"{f['id']}: {n} images, "
                  f"{sum(i.get('bytes', 0) for g in f['real_images']['groups'] for i in g['images'])/1048576:.2f} MB")
        else:
            f.pop('real_images', None)
    doc['method'] = ('三层结构：① 真本影像（原刻本扫描/绣像，站内小图，可点开原分辨率直链）；'
                     '② 版式示意（程序绘制，呈现行格/框线/栏式/牌记等特征）；'
                     '③ 外部高清源（公版影印 PDF 与馆藏在线浏览）。'
                     '体积策略：站内单张影像 ≤ %dKB，原分辨率图不入仓。' % CAP_KB)
    with open(JSON_PATH, 'w', encoding='utf-8') as fp:
        json.dump(doc, fp, ensure_ascii=False, indent=2)
    print('wrote', JSON_PATH, os.path.getsize(JSON_PATH), 'bytes')


if __name__ == '__main__':
    main()
