#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""影像体积护栏：确保站内单张影像不超过上限（默认 200KB），并汇报目录总体积。

用法: python3 build/check_asset_size.py [--kb 200] [--dir docs/img/facsimile]
退出码非 0 表示有文件超限。
"""
import argparse, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')


def human(n):
    return f'{n/1048576:.2f} MB' if n >= 1048576 else f'{n/1024:.0f} KB'


def shrink_in_place(fp: str, cap: int) -> int:
    """把超限的 JPEG 就地降质重压到上限内；返回新体积。"""
    from PIL import Image
    im = Image.open(fp).convert('RGB')
    for q in (80, 72, 64, 56, 48, 40):
        tmp = fp + '.tmp'
        im.save(tmp, 'JPEG', quality=q, optimize=True, progressive=True)
        if os.path.getsize(tmp) <= cap:
            os.replace(tmp, fp)
            return os.path.getsize(fp)
        os.remove(tmp)
    w, h = im.size
    im2 = im.resize((int(w * 0.85), int(h * 0.85)), Image.LANCZOS)
    im2.save(fp, 'JPEG', quality=62, optimize=True, progressive=True)
    return os.path.getsize(fp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kb', type=int, default=200)
    ap.add_argument('--dir', default='docs/img/facsimile')
    ap.add_argument('--fix', action='store_true', help='就地压缩超限影像')
    args = ap.parse_args()
    base = os.path.join(ROOT, args.dir)
    cap = args.kb * 1024
    total, n, bad = 0, 0, []
    for dp, _, fs in os.walk(base):
        for f in fs:
            if not f.lower().endswith(EXTS):
                continue
            fp = os.path.join(dp, f)
            sz = os.path.getsize(fp)
            if sz > cap and args.fix and f.lower().endswith(('.jpg', '.jpeg')):
                new = shrink_in_place(fp, cap)
                print(f'  压缩 {os.path.relpath(fp, ROOT)}: {human(sz)} → {human(new)}')
                sz = new
            total += sz; n += 1
            if sz > cap:
                bad.append((sz, os.path.relpath(fp, ROOT)))
    print(f'扫描 {args.dir}: {n} 个影像文件，合计 {human(total)}，单张上限 {args.kb} KB')
    if bad:
        print('超限文件：')
        for sz, p in sorted(bad, reverse=True):
            print(f'  {human(sz):>9}  {p}')
        return 1
    mx = max((os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(base) for f in fs
              if f.lower().endswith(EXTS)), default=0)
    print(f'全部合规；最大单张 {human(mx)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
