"""页面骨架生成：输出与站点既有页面一致的头 + 导航（含『数字研究』下拉）。
新增研究页面时改这里的 RESEARCH 列表即可，其余页面无需逐一手改。
"""
from __future__ import annotations

# 全站主导航（与 docs/*.html 现有 15 项一致）
NAV = [
    ('index.html', '首页'),
    ('index.html#versions', '版本学'),
    ('index.html#heroes', '108将'),
    ('themes.html', '主题研究'),
    ('kg.html', '知识图谱'),
    ('index.html#graph', '关系图谱'),
    ('index.html#places', '空间地理'),
    ('index.html#events', '叙事结构'),
    ('index.html#weapons', '兵器职官'),
    ('index.html#critics', '评点学术'),
    ('index.html#derivatives', '续书衍生'),
    ('index.html#ontology', '本体推演'),
    ('read.html', '版本阅读'),
    ('diff.html', '异文对照'),
    ('search.html', '批注检索'),
]

# 『数字研究』下拉：计算人文产出页
RESEARCH = [
    ('stemma.html', '版本谱系树'),
    ('reception.html', '评点接受史'),
    ('emotion.html', '情感曲线'),
    ('network.html', '网络演化'),
    ('stylometry.html', '文体计量'),
]

RESEARCH_LABEL = '数字研究'


def nav_html(active: str = '') -> str:
    parts = ['<nav class="nav-links">']
    for href, label in NAV:
        cls = ' class="active"' if href == active else ''
        parts.append('  <a href="' + href + '"' + cls + '>' + label + '</a>')
    parts.append('  <span class="nav-dd">')
    dd_cls = 'nav-dd-toggle active' if active in [h for h, _ in RESEARCH] else 'nav-dd-toggle'
    parts.append('    <span class="' + dd_cls + '" tabindex="0" role="button">'
                 + RESEARCH_LABEL + ' <b>▾</b></span>')
    parts.append('    <span class="nav-dd-menu">')
    for href, label in RESEARCH:
        cls = ' class="active"' if href == active else ''
        parts.append('      <a href="' + href + '"' + cls + '>' + label + '</a>')
    parts.append('    </span>')
    parts.append('  </span>')
    parts.append('</nav>')
    return '\n'.join(parts)


def page(title, body, active='', head_extra='', scripts_extra='', echarts=True):
    """拼装完整 HTML 字符串。"""
    head = [
        '<!DOCTYPE html>',
        '<html lang="zh-CN">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">',
        '<title>' + title + '</title>',
        '<link rel="stylesheet" href="css/style.css">',
    ]
    if echarts:
        head.append('<script src="vendor/echarts.min.js"></script>')
    head += [
        '<script src="js/registry.js"></script>',
        '<style>',
        head_extra,
        '</style>',
        '</head>',
        '<body>',
        '<header class="topbar">',
        '  <div class="logo"><span class="seal">水</span><span>水浒传本体论</span></div>',
        nav_html(active),
        '</header>',
    ]
    tail = ['<script>', scripts_extra, '</script>', '</body>', '</html>']
    return '\n'.join(head + [body] + tail)
