# -*- coding: utf-8 -*-
"""版本 / 批注注册表读取与完整性校验（计算底座 · 可扩充性支撑）

这是站点「可扩充性」的 Python 侧入口：所有构建脚本都从这里取版本清单，
新增一个版本只需改 docs/data/registry.json（+ 补语料目录），无需改任何脚本。

用法::

    import sys; sys.path.insert(0, 'build')
    from lib.registry import Registry
    reg = Registry()                     # 自动定位仓库根
    reg.version_ids()                    # ['v120','v100',...]
    reg.version('v120')['short']         # '袁百二'
    reg.commentaries()                   # 批注家元数据（按 order）
    errors, warns, stats = reg.check()   # 完整性校验
"""
from __future__ import annotations

import json
import os

_REQUIRED_V_KEYS = ("id", "short", "label", "name", "range")
_REQUIRED_C_KEYS = ("id", "tag", "who", "file", "okVer")


class Registry:
    """注册表访问器。root 缺省为仓库根（本文件位于 <root>/build/lib/）。"""

    def __init__(self, root: str | None = None):
        if root is None:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.root = root
        self.docs = os.path.join(root, "docs")
        self.path = os.path.join(self.docs, "data", "registry.json")
        with open(self.path, encoding="utf-8") as f:
            self._d = json.load(f)

    # ---------- 基本读取 ----------
    @property
    def schema_version(self) -> int:
        return int(self._d.get("schema_version", 0))

    def versions(self) -> list[dict]:
        """全部版本元数据，按 order 升序。"""
        return sorted(self._d.get("versions", []), key=lambda v: v.get("order", 99))

    def version(self, vid: str) -> dict | None:
        for v in self.versions():
            if v.get("id") == vid:
                return v
        return None

    def version_ids(self) -> list[str]:
        return [v["id"] for v in self.versions()]

    def commentaries(self) -> list[dict]:
        """全部批注家元数据，按 order 升序。"""
        return sorted(self._d.get("commentaries", []), key=lambda c: c.get("order", 99))

    def comment(self, cid: str) -> dict | None:
        for c in self.commentaries():
            if c.get("id") == cid:
                return c
        return None

    def comment_ids(self) -> list[str]:
        return [c["id"] for c in self.commentaries()]

    def versions_index(self) -> dict:
        """docs/texts/versions/versions_index.json（章节索引，另行维护）。"""
        with open(os.path.join(self.docs, "texts", "versions", "versions_index.json"),
                  encoding="utf-8") as f:
            return json.load(f)

    # ---------- 路径 ----------
    def ver_dir(self, vid: str) -> str:
        return os.path.join(self.docs, "texts", "versions", vid)

    def comment_file(self, cid: str) -> str:
        c = self.comment(cid)
        return os.path.join("docs", "texts", "versions", c["file"]) if c else ""

    # ---------- 完整性校验 ----------
    def check(self) -> tuple[list[str], list[str], dict]:
        """返回 (errors, warnings, stats)。

        errors  ：会导致站点出错的问题（缺目录、缺文件、id 重复、okVer 悬空等）
        warnings：不影响运行但应知晓的问题（未注册目录、注册表与索引不一致等）
        stats   ：统计信息
        """
        errors: list[str] = []
        warns: list[str] = []
        stats: dict = {}

        # --- 注册表自身 ---
        if self.schema_version < 1:
            errors.append("registry.json 缺 schema_version")

        vids = self.version_ids()
        if len(vids) != len(set(vids)):
            errors.append("versions 中 id 重复")
        cids = self.comment_ids()
        if len(cids) != len(set(cids)):
            errors.append("commentaries 中 id 重复")

        # --- 版本 ---
        n_files = 0
        vi = None
        try:
            vi = self.versions_index()
            idx_ids = {v["id"] for v in vi.get("versions", [])}
        except Exception as e:  # noqa: BLE001
            idx_ids = set()
            warns.append(f"无法读取 versions_index.json：{e}")

        for v in self.versions():
            vid = v["id"]
            for k in _REQUIRED_V_KEYS:
                if k not in v:
                    errors.append(f"版本 {vid} 缺字段 {k}")
            d = self.ver_dir(vid)
            if not os.path.isdir(d):
                errors.append(f"版本 {vid} 语料目录不存在：docs/texts/versions/{vid}/")
                continue
            for sub in ("fan", "jian", "bai"):
                sd = os.path.join(d, sub)
                if not os.path.isdir(sd):
                    errors.append(f"版本 {vid} 缺语体目录 {sub}/")
                else:
                    n_files += len([f for f in os.listdir(sd) if f.endswith(".txt")])
            if not os.path.isfile(os.path.join(d, "chapters.json")):
                warns.append(f"版本 {vid} 缺 chapters.json（阅读器将回退到 versions_index.json）")
            if idx_ids and vid not in idx_ids:
                warns.append(f"版本 {vid} 已注册，但 versions_index.json 中无对应条目"
                             f"（可运行 python3 build/register_version.py --sync-index 自动补上）")

        # --- 未注册目录（正向可扩充性的体检项） ---
        vroot = os.path.join(self.docs, "texts", "versions")
        if os.path.isdir(vroot):
            for name in sorted(os.listdir(vroot)):
                p = os.path.join(vroot, name)
                if os.path.isdir(p) and name not in vids:
                    warns.append(f"目录 texts/versions/{name}/ 存在但未在注册表中登记（新增版本时请补登记）")

        # --- 批注家 ---
        for c in self.commentaries():
            cid = c["id"]
            for k in _REQUIRED_C_KEYS:
                if k not in c:
                    errors.append(f"批注家 {cid} 缺字段 {k}")
            fp = os.path.join(self.docs, "texts", "versions", c.get("file", ""))
            if not os.path.isfile(fp):
                errors.append(f"批注家 {cid} 数据文件不存在：texts/versions/{c.get('file')}")
            for ov in c.get("okVer", []):
                if ov not in vids:
                    errors.append(f"批注家 {cid} 的 okVer 指向未注册版本：{ov}")

        # 未登记的批注数据文件
        if os.path.isdir(vroot):
            known = {c.get("file") for c in self.commentaries()}
            for name in sorted(os.listdir(vroot)):
                if name.endswith(("_comments.json", "_notes.json")) and name not in known:
                    warns.append(f"批注数据文件 {name} 存在但未在注册表中登记")

        # --- 数据文件路径体检 ---
        # json 里若出现 "../xxx" 这类越界相对路径，浏览器会把它解析到站点根之外，
        # 表现为图片/资源静默 404（曾发生：头像 portrait 字段写成 ../img/heroes/x.jpg）。
        import re as _re
        data_root = os.path.join(self.docs, "data")
        for dirpath, _dirs, files in os.walk(data_root):
            for fn in files:
                if not fn.endswith(".json"):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding="utf-8") as f:
                        txt = f.read()
                except Exception:  # noqa: BLE001
                    continue
                hits = _re.findall(r'"((?:\.\./)+[^"]*)"', txt)
                if hits:
                    rel = os.path.relpath(fp, self.docs)
                    warns.append(f"数据文件 {rel} 含越界相对路径 {len(hits)} 处"
                                 f"（如 {hits[0]}）→ 会请求到站点根之外而 404，请改为站内相对路径")

        stats = {
            "versions": len(vids),
            "commentaries": len(cids),
            "text_files": n_files,
            "errors": len(errors),
            "warnings": len(warns),
        }
        return errors, warns, stats
