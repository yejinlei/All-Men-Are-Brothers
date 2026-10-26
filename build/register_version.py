#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""版本注册与完整性校验工具 ——「加一个版本只改一处」的落地工具。

站点所有页面（阅读器 / 异文对照 / 批注检索 / 首页）与构建脚本都从
docs/data/registry.json 读取版本与批注清单。新增一个版本的标准流程：

    # 1) 把语料放进 docs/texts/versions/<新id>/{fan,jian,bai}/ 与 chapters.json
    # 2) 登记（会自动校验并排好 order）
    python3 build/register_version.py --add myver \\
        --name "某某本" --short 某某 --label 某某本 --range 0-100 \\
        --system "繁本·百回" --color "#5a7d3a" --desc "明代某某刊本"
    # 3) 同步语料索引（让首页/阅读器/对照页都认到新版本）
    python3 build/register_version.py --sync-index
    # 4) 体检
    python3 build/register_version.py --check

用法一览::

    --check                 全量完整性校验（errors / warnings / 统计）
    --list                  列出版本与批注家
    --discover              扫描未登记的语料目录与批注文件
    --add <id> [...]        登记一个新版本
    --add-commentary <id> […]  登记一家新批注
    --sync-index            把注册表同步进语料索引 versions_index.json
                            （补上缺失条目、对齐展示名与回数；已有章节清单原样保留）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.registry import Registry  # noqa: E402


def _save(reg: Registry, data: dict) -> None:
    with open(reg.path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def cmd_check(reg: Registry) -> int:
    errors, warns, stats = reg.check()
    print("=" * 62)
    print("  版本注册表完整性体检")
    print("=" * 62)
    print(f"  版本 {stats['versions']} 个 · 批注家 {stats['commentaries']} 家 · 语料文件 {stats['text_files']} 个")
    print(f"  错误 {stats['errors']} 条 · 提醒 {stats['warnings']} 条")
    print("-" * 62)
    if errors:
        print("  【错误】（必须修复，否则页面会出错）")
        for e in errors:
            print("   ✗ " + e)
    if warns:
        print("  【提醒】（不影响运行，建议知晓）")
        for w in warns:
            print("   ! " + w)
    if not errors and not warns:
        print("  一切正常 ✓")
    print("=" * 62)
    return 1 if errors else 0


def cmd_list(reg: Registry) -> int:
    print("版本（versions）：")
    for v in reg.versions():
        print(f"  {v.get('order', '?'):>2}. {v['id']:<12} {v.get('short', ''):<6} "
              f"{v.get('label', ''):<8} {v.get('name', '')}  range={v.get('range')}")
    print("\n批注家（commentaries）：")
    for c in reg.commentaries():
        print(f"  {c.get('order', '?'):>2}. {c['id']:<12} {c.get('tag', ''):<5} "
              f"{c.get('who', ''):<8} okVer={','.join(c.get('okVer', []))}")
    return 0


def cmd_discover(reg: Registry) -> int:
    vroot = os.path.join(reg.docs, "texts", "versions")
    vids = set(reg.version_ids())
    known_files = {c.get("file") for c in reg.commentaries()}
    found = False
    for name in sorted(os.listdir(vroot)):
        p = os.path.join(vroot, name)
        if os.path.isdir(p) and name not in vids:
            n = sum(len([f for f in os.listdir(os.path.join(p, s)) if f.endswith('.txt')])
                    for s in ("fan", "jian", "bai") if os.path.isdir(os.path.join(p, s)))
            print(f"  [未登记版本] {name}/  （{n} 个语体文本）")
            found = True
        elif os.path.isfile(p) and name.endswith(("_comments.json", "_notes.json")) and name not in known_files:
            print(f"  [未登记批注] {name}")
            found = True
    if not found:
        print("  未发现未登记的语料目录或批注文件 ✓")
    return 0


def cmd_add(reg: Registry, a: argparse.Namespace) -> int:
    data = json.load(open(reg.path, encoding="utf-8"))
    if any(v.get("id") == a.id for v in data.get("versions", [])):
        print(f"✗ 版本 {a.id} 已存在，未改动。如需修改请直接编辑 registry.json。")
        return 1
    if not os.path.isdir(reg.ver_dir(a.id)):
        print(f"✗ 语料目录不存在：docs/texts/versions/{a.id}/  —— 请先放入语料再登记。")
        return 1
    rng = [int(x) for x in a.range.split("-")] if a.range else [0, 999]
    if len(rng) != 2 or rng[0] > rng[1]:
        print("✗ --range 形如 0-120（起-止）")
        return 1
    entry = {
        "id": a.id,
        "order": int(a.order) if a.order else (len(data.get("versions", [])) + 1),
        "short": a.short or a.name[:3],
        "shortDiff": a.short_diff or (a.short or a.name)[:1],
        "label": a.label or a.name,
        "name": a.name,
        "full": a.full or a.name,
        "cls": a.cls or "",
        "color": a.color or "#8a6d3b",
        "range": rng,
        "system": a.system or "",
        "date": a.date or "",
        "status": "ready",
        "desc": a.desc or "",
    }
    data.setdefault("versions", []).append(entry)
    data["versions"] = sorted(data["versions"], key=lambda v: v.get("order", 99))
    _save(reg, data)
    print(f"✓ 已登记版本 {a.id}（order={entry['order']}, range={rng}）")
    print("  下一步：python3 build/register_version.py --check")
    return 0


def cmd_add_commentary(reg: Registry, a: argparse.Namespace) -> int:
    data = json.load(open(reg.path, encoding="utf-8"))
    if any(c.get("id") == a.id for c in data.get("commentaries", [])):
        print(f"✗ 批注家 {a.id} 已存在，未改动。")
        return 1
    fname = a.file or (a.id + "_comments.json")
    if not os.path.isfile(os.path.join(reg.docs, "texts", "versions", fname)):
        print(f"✗ 批注数据文件不存在：texts/versions/{fname}  —— 请先放入数据再登记。")
        return 1
    ok = [x for x in (a.ok_ver or "").split(",") if x]
    unknown = [x for x in ok if x not in set(reg.version_ids())]
    if unknown:
        print(f"✗ okVer 含未注册版本：{unknown}")
        return 1
    entry = {
        "id": a.id,
        "order": int(a.order) if a.order else (len(data.get("commentaries", [])) + 1),
        "tag": a.tag or a.id,
        "who": a.who or a.id,
        "cls": a.cls or ("cmt-" + a.id),
        "chipCls": a.chip_cls or "",
        "color": a.color or "#8a6d3b",
        "file": fname,
        "kind": a.kind or a.id,
        "okVer": ok,
        "note": a.note or "",
    }
    data.setdefault("commentaries", []).append(entry)
    data["commentaries"] = sorted(data["commentaries"], key=lambda c: c.get("order", 99))
    _save(reg, data)
    print(f"✓ 已登记批注家 {a.id}（order={entry['order']}, okVer={ok}）")
    print("  提示：阅读器按钮配色自动取自 color，无需改 CSS；如需专用配色可再补 .cmt-btn.active.cm-<id> 规则。")
    return 0


def cmd_sync_index(reg: Registry) -> int:
    """把注册表同步进 docs/texts/versions/versions_index.json。

    - status='planned' 的占位版本不入索引；
    - 缺条目的版本补建（回数由 range 推算，若已有 chapters.json 则读入章节清单）；
    - 已存在条目的展示名对齐注册表 full、描述对齐 desc，回数等构建字段原样保留；
    - 注册表中已无、但索引里仍有数据的条目保留在末尾并提示（不静默丢数据）。
    """
    idx_path = os.path.join(reg.docs, "texts", "versions", "versions_index.json")
    with open(idx_path, encoding="utf-8") as f:
        vi = json.load(f)
    old = {v.get("id"): v for v in vi.get("versions", [])}

    out, added, renamed, kept = [], [], [], []
    for v in reg.versions():
        vid = v["id"]
        if v.get("status") == "planned":
            continue
        rng = v.get("range") if isinstance(v.get("range"), list) else [0, 0]
        cnt = rng[1] - rng[0] + 1
        cur = old.get(vid)
        if cur is None:
            cur = {"id": vid, "chapters": [], "chapters_count": cnt}
            chp = os.path.join(reg.ver_dir(vid), "chapters.json")
            if os.path.isfile(chp):
                with open(chp, encoding="utf-8") as f:
                    raw = json.load(f)
                chs = raw.get("chapters", raw) if isinstance(raw, dict) else raw
                if isinstance(chs, list):
                    cur["chapters"] = chs
                    cur["chapters_count"] = len(chs)
            added.append(vid)
        name = v.get("full") or v.get("name") or vid
        if cur.get("name") != name:
            renamed.append((vid, cur.get("name"), name))
            cur["name"] = name
        if v.get("desc"):
            cur["desc"] = v["desc"]
        if not cur.get("count"):
            cur["count"] = cnt
        if not cur.get("chapters_count"):
            cur["chapters_count"] = cur["count"]
        out.append(cur)

    known = {x.get("id") for x in out}
    for vid, cur in old.items():
        if vid not in known:
            out.append(cur)
            kept.append(vid)

    vi["versions"] = out
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(vi, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("=" * 62)
    print("  语料索引同步 → texts/versions/versions_index.json")
    print("=" * 62)
    print(f"  索引版本 {len(out)} 个（新增 {len(added)} · 展示名对齐 {len(renamed)}）")
    if added:
        print("   + 新增条目：" + "、".join(added))
    for vid, o, n in renamed:
        print(f"   ~ {vid} 展示名：{o} → {n}")
    if kept:
        print("   ! 注册表已无、索引仍保留：" + "、".join(kept))
    print("  下一步：python3 build/register_version.py --check")
    print("=" * 62)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="版本注册与完整性校验")
    ap.add_argument("--root", default=None, help="仓库根目录（缺省自动定位）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="全量完整性校验")
    g.add_argument("--list", action="store_true", help="列出版本与批注家")
    g.add_argument("--discover", action="store_true", help="扫描未登记的语料/批注")
    g.add_argument("--add", metavar="ID", help="登记新版本")
    g.add_argument("--add-commentary", metavar="ID", help="登记新批注家")
    g.add_argument("--sync-index", action="store_true", help="把注册表同步进语料索引 versions_index.json")
    # --add 参数
    ap.add_argument("--name"); ap.add_argument("--short"); ap.add_argument("--short-diff")
    ap.add_argument("--label"); ap.add_argument("--full"); ap.add_argument("--cls")
    ap.add_argument("--color"); ap.add_argument("--range"); ap.add_argument("--system")
    ap.add_argument("--date"); ap.add_argument("--desc"); ap.add_argument("--order")
    # --add-commentary 参数
    ap.add_argument("--tag"); ap.add_argument("--who"); ap.add_argument("--file")
    ap.add_argument("--chip-cls"); ap.add_argument("--kind"); ap.add_argument("--ok-ver")
    ap.add_argument("--note")
    a = ap.parse_args()

    reg = Registry(a.root)
    if a.check:
        return cmd_check(reg)
    if a.list:
        return cmd_list(reg)
    if a.discover:
        return cmd_discover(reg)
    if a.sync_index:
        return cmd_sync_index(reg)
    if a.add:
        a.id = a.add
        if not a.name:
            print("✗ --add 至少需要 --name")
            return 1
        return cmd_add(reg, a)
    if a.add_commentary:
        a.id = a.add_commentary
        if not (a.who and a.tag):
            print("✗ --add-commentary 至少需要 --who 与 --tag")
            return 1
        return cmd_add_commentary(reg, a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
