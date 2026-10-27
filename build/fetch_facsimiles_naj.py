#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 17 · 真实影像抓取：日本国立公文书馆（国立公文書館デジタルアーカイブ）
藏《李卓吾先生批評忠義水滸伝》（容与堂本）二十卷原刻本扫描。

设计要点（体积受控）：
- 走 curl 取图（该站对 urllib 的 TLS 指纹回 403，curl 正常）；
- IIIF 尺寸参数控图，长边默认 1200px；编码后超硬上限自动降质/降尺寸重压；
- 不入仓原分辨率叶（原叶 6200×4500、单叶数 MB），仅登记其 IIIF 直链供在线放大；
- 断点续传：已存在且体积达标的文件跳过。
输出：raw/facsimiles/rongyutang/（源）+ docs/img/facsimile/rongyutang/（站内小图）
依据该馆「二次利用」条款：公版古籍扫描可自由再利用，须标注来源。
"""
from __future__ import annotations
import argparse, io, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, 'raw', 'facsimiles', 'rongyutang')
WEB_DIR = os.path.join(ROOT, 'docs', 'img', 'facsimile', 'rongyutang')
META_DIR = os.path.join(ROOT, 'raw', 'facsimiles')
API = 'https://www.digital.archives.go.jp/api/iiif/{item}/manifest.json'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

VOLUMES = [
    ('4470170', 'vol01', 'all',   '卷之一'),
    ('4445240', 'vol19', [1, 2, 3, 4], '卷之十九'),
    ('4446087', 'vol20', [1, 2, 3, 4, 75, 76, 77, 78], '卷之二十'),
]

PAGE_CAP = 200_000   # 单文件硬上限 200KB
MAX_PX = 1200


def curl_bytes(url: str, timeout: int = 60, retries: int = 4, pace: float = 0.6) -> bytes:
    last = None
    for k in range(retries):
        try:
            time.sleep(pace)
            r = subprocess.run(
                ['curl', '-sSL', '--compressed', '--max-time', str(timeout),
                 '-A', UA, '-H', 'Accept: */*', url],
                capture_output=True)
            if r.returncode == 0 and r.stdout:
                return r.stdout
            last = RuntimeError(f'curl rc={r.returncode} out={len(r.stdout)}b')
        except Exception as e:  # noqa
            last = e
        time.sleep(4 * (k + 1))
    raise last


def get_manifest(item: str) -> dict:
    return json.loads(curl_bytes(API.format(item=item), timeout=90, retries=5, pace=0.3))


def encode(im: Image.Image, quality: int) -> bytes:
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)
    return out.getvalue()


def shrink(raw: bytes, max_px: int) -> tuple[bytes, tuple[int, int]]:
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    w, h = im.size
    scale = max_px / max(w, h)
    if scale < 1:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    for q in (82, 74, 66, 58):
        b = encode(im, q)
        if len(b) <= PAGE_CAP:
            return b, im.size
        if q == 58:
            w, h = im.size
            im2 = im.resize((int(w * 0.8), int(h * 0.8)), Image.LANCZOS)
            return encode(im2, 62), im2.size
    return encode(im, 60), im.size


def fetch_page(small_url: str, max_px: int) -> tuple[bytes, tuple[int, int]]:
    return shrink(curl_bytes(small_url), max_px)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-px', type=int, default=MAX_PX)
    ap.add_argument('--concurrency', type=int, default=3)
    ap.add_argument('--limit', type=int, default=0, help='本次最多抓取多少叶（0=全部）')
    args = ap.parse_args()

    for d in (RAW_DIR, WEB_DIR, META_DIR):
        os.makedirs(d, exist_ok=True)

    index = {
        '_note': '容与堂本《李卓吾先生批評忠義水滸伝》（日本国立公文書館藏 20 卷）原刻本扫描叶。'
                 '站内图按 IIIF 尺寸参数压缩，长边 %dpx、单文件 ≤ %dKB；orig_full 为原分辨率直链。'
                 % (args.max_px, PAGE_CAP // 1000),
        'source': '国立公文書館デジタルアーカイブ（National Archives of Japan）',
        'license': 'https://www.digital.archives.go.jp/secondary-use',
        'books': [],
    }

    tasks = []
    for item, vtag, spec, vlabel in VOLUMES:
        m = get_manifest(item)
        canvases = m['sequences'][0]['canvases']
        picks = list(range(len(canvases))) if spec == 'all' else [i - 1 for i in spec if 1 <= i <= len(canvases)]
        rec = {'item_id': item, 'volume': vtag, 'volume_label': vlabel, 'label': m.get('label'),
               'item_url': f'https://www.digital.archives.go.jp/item/{item}',
               'total_canvases': len(canvases), 'pages': []}
        for i in picks:
            leaf = i + 1
            fname = f'{vtag}_leaf{leaf:03d}.jpg'
            fp = os.path.join(WEB_DIR, fname)
            full_url = canvases[i]['images'][0]['resource']['@id']
            small_url = full_url.replace('/full/max/', f'/full/!{args.max_px},{args.max_px}/')
            ent = {'leaf': leaf, 'file': f'img/facsimile/rongyutang/{fname}',
                   'iiif_small': small_url, 'orig_full': full_url}
            if os.path.exists(fp) and os.path.getsize(fp) > 1000:
                ent['bytes'] = os.path.getsize(fp)
                try:
                    with Image.open(fp) as im:
                        ent['w'], ent['h'] = im.size
                except Exception:  # noqa
                    pass
                rec['pages'].append(ent)
            else:
                tasks.append((vtag, leaf, fname, small_url))
        index['books'].append(rec)

    if args.limit:
        tasks = tasks[:args.limit]
    print(f'todo pages: {len(tasks)}', flush=True)

    done = 0
    if tasks:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(fetch_page, su, args.max_px): (vtag, leaf, fn) for vtag, leaf, fn, su in tasks}
            for fut in as_completed(futs):
                vtag, leaf, fname = futs[fut]
                try:
                    b, size = fut.result()
                    for d in (RAW_DIR, WEB_DIR):
                        os.makedirs(d, exist_ok=True)
                        with open(os.path.join(d, fname), 'wb') as f:
                            f.write(b)
                    done += 1
                    if done % 5 == 0:
                        print(f'  ...{done}/{len(tasks)}', flush=True)
                except Exception as e:  # noqa
                    print(f'  FAIL {vtag} leaf{leaf}: {type(e).__name__}: {e}', file=sys.stderr, flush=True)

    # 重建完整索引（含本批 + 以往批次，均带 IIIF 直链与尺寸）
    for rec in index['books']:
        vtag = rec['volume']
        pages = []
        d = WEB_DIR
        files = sorted(f for f in os.listdir(d) if f.startswith(vtag + '_leaf') and f.endswith('.jpg')) if os.path.isdir(d) else []
        urlmap = {t[2]: t[3] for t in tasks}
        for f in files:
            fp = os.path.join(d, f)
            sz = os.path.getsize(fp)
            if sz <= 1000:
                continue
            leaf = int(f[len(vtag) + 5:-4])
            ent = {'leaf': leaf, 'file': f'img/facsimile/rongyutang/{f}', 'bytes': sz}
            try:
                with Image.open(fp) as im:
                    ent['w'], ent['h'] = im.size
            except Exception:  # noqa
                pass
            if f in urlmap:
                ent['iiif_small'] = urlmap[f]
            pages.append(ent)
        # 补 IIIF 直链（已有 index 记录中带链接的沿用）
        prev = {p['leaf']: p for p in rec.get('pages', [])}
        for ent in pages:
            if 'iiif_small' not in ent and ent['leaf'] in prev and 'iiif_small' in prev[ent['leaf']]:
                ent['iiif_small'] = prev[ent['leaf']]['iiif_small']
                ent['orig_full'] = prev[ent['leaf']].get('orig_full')
        rec['pages'] = sorted(pages, key=lambda p: p['leaf'])

    os.makedirs(META_DIR, exist_ok=True)
    with open(os.path.join(META_DIR, 'rongyutang_index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    total = sum(p['bytes'] for r in index['books'] for p in r['pages'])
    mx = max((p['bytes'] for r in index['books'] for p in r['pages']), default=0)
    n = sum(len(r['pages']) for r in index['books'])
    print(f'done {done} this batch; on-disk {n} pages; total {total/1048576:.2f} MB; '
          f'avg {total/max(1,n)/1024:.0f} KB; max {mx/1024:.0f} KB', flush=True)


if __name__ == '__main__':
    main()
