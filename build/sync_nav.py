#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/*.html 所有页面的 <nav class="nav-links">...</nav> 替换为 pagegen.nav_html() 最新版本。
默认按文件名推断 active：页面对应自身 href 为 active，其余回到 index。
"""
from __future__ import annotations
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
from pagegen import NAV, RESEARCH, nav_html

DOCS = pathlib.Path(__file__).resolve().parents[1] / "docs"

# 文件名 → active key（非页面自身的特殊映射用不到；默认页面文件=active）
def active_for(fn: str) -> str:
    # 首页锚点页都当作 index 激活
    if fn in ("index.html",):
        return "index.html"
    # 其他页面以自身文件名作为 active
    return fn

NAV_RE = re.compile(r'<nav class="nav-links"[^>]*>.*?</nav>', re.S)

def sync_one(path: pathlib.Path):
    html = path.read_text(encoding="utf-8")
    active = active_for(path.name)
    m = NAV_RE.search(html)
    if not m:
        print(f"[skip] {path.name}: no <nav class=nav-links> found")
        return False
    # 保留原标签上的 id（如有）
    open_tag = m.group(0).split(">", 1)[0] + ">"
    new_nav = open_tag + "\n" + nav_html(active).split(">",1)[1]  # 替换为新导航内部
    # 更稳妥：直接用 pagegen 输出的 nav（不含 open tag），保留原 open tag
    new_block = open_tag + nav_html(active).split(">",1)[1]
    new_html = html[:m.start()] + new_block + html[m.end():]
    if new_html == html:
        return False
    path.write_text(new_html, encoding="utf-8")
    return True

def main():
    changed = []
    for p in sorted(DOCS.glob("*.html")):
        if sync_one(p):
            changed.append(p.name)
    print(f"synced {len(changed)} pages: {changed}")

if __name__ == "__main__":
    main()
