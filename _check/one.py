#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阅读器页面核对（Playwright 无头浏览器）。

用法：
    python3 _check/one.py read <port>      # 在 docs 根已起的静态服务器上，遍历各版本 × 繁/简/白
    python3 _check/one.py read <port> <vid>  # 只查某版本

核对内容：每个「版本 × 语体」组合是否渲染出正文、是否有 JS 报错、白话层是否存在。
"""
import sys
import json
import urllib.request

from playwright.sync_api import sync_playwright

LANGS = [("fan", "繁"), ("jian", "简"), ("bai", "白")]


def main():
    argv = sys.argv[1:]
    mode = argv[0] if argv else "read"
    port = int(argv[1]) if len(argv) > 1 else 8000
    only = argv[2] if len(argv) > 2 else None
    base = "http://localhost:%d" % port

    if mode != "read":
        print("未知模式：%s（当前仅支持 read）" % mode)
        return 2

    idx = json.load(urllib.request.urlopen(base + "/texts/versions/versions_index.json"))
    vids = [v["id"] for v in idx["versions"]]
    if only:
        vids = [v for v in vids if v == only]

    ok = 0
    problems = []
    errs = []

    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome", args=["--no-sandbox", "--disable-dev-shm-usage"])
        pg = br.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.on(
            "console",
            lambda m: errs.append("console.error: %s" % m.text) if m.type == "error" else None,
        )
        pg.goto(base + "/read.html", wait_until="load")
        pg.wait_for_timeout(1500)

        for vid in vids:
            btn = pg.query_selector('.ver-btn[data-vid="%s"]' % vid)
            if not btn:
                problems.append("%s: 页面无该版本按钮" % vid)
                continue
            btn.click()
            pg.wait_for_timeout(900)

            n = pg.eval_on_selector_all("#selChap option", "els=>els.length")
            if n and n > 1:
                pg.select_option("#selChap", index=min(1, n - 1))
                pg.wait_for_timeout(800)

            for lang, lab in LANGS:
                pg.click('.lang-btn[data-lang="%s"]' % lang)
                pg.wait_for_timeout(700)
                txt = pg.inner_text("#contentWrap") or ""
                title = pg.inner_text("#chapTitle") or ""
                bad = (
                    not txt.strip()
                    or "正在载入" in txt
                    or "暂未整理" in txt
                    or "章节列表为空" in txt
                )
                if bad:
                    problems.append("[%s] %s(%s) 回目「%s」渲染异常：%s" % (vid, lab, lang, title.strip(), txt.strip()[:40]))
                else:
                    ok += 1

        br.close()

    print("=== 渲染成功组合：%d 个 ===" % ok)
    if errs:
        print("=== JS 报错 %d 条 ===" % len(errs))
        for e in errs[:20]:
            print("   ", e[:160])
    if problems:
        print("=== 问题 %d 处 ===" % len(problems))
        for x in problems:
            print("   ", x)
    if not errs and not problems:
        print("=== 全部通过，无 JS 报错 ===")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
