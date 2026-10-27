"""统一样式：中文字体、配色、图形输出（同时存 PNG 与 SVG 两份）。

字体在本环境用 Noto Sans CJK SC / Noto Serif CJK SC（已随系统安装）。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIGDIR = REPO / 'docs' / 'fig'

FONT_SANS = 'Noto Sans CJK SC'
FONT_SERIF = 'Noto Serif CJK SC'

# 站点配色（与 docs/css/style.css 的 :root 变量一致）
C = {
    'vermilion': '#c0392b', 'deep': '#8b1a1a', 'gold': '#b8860b',
    'jade': '#2f5d50', 'indigo': '#2d3a6e',
    'paper': '#f5f0e6', 'paperwarm': '#ede4cf', 'border': '#d9cdb0',
    'ink': '#1a1a1a', 'inklight': '#3a3a3a', 'muted': '#6b6b6b',
}

# 版本 / 评点家通用调色板
PALETTE = ['#c0392b', '#2e5a88', '#8a6d3b', '#5a7d3a', '#7a5195',
           '#a9622d', '#2f6f6f', '#8b1a1a', '#2f5d50', '#2d3a6e']


def setup():
    """设定 rcParams：中文字体 / 米色底 / 墨色字。"""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': [FONT_SANS, FONT_SERIF],
        'axes.unicode_minus': False,
        'figure.facecolor': C['paper'],
        'axes.facecolor': C['paper'],
        'savefig.facecolor': C['paper'],
        'axes.edgecolor': C['muted'],
        'axes.labelcolor': C['ink'],
        'text.color': C['ink'],
        'xtick.color': C['inklight'],
        'ytick.color': C['inklight'],
        'axes.titlesize': 15,
        'font.size': 11,
        'figure.dpi': 120,
        'axes.grid': True,
        'grid.color': C['border'],
        'grid.alpha': 0.5,
    })


def save(fig, name: str, dpi: int = 160):
    """把图存为 docs/fig/<name>.png 与 .svg，返回落盘路径列表。"""
    FIGDIR.mkdir(parents=True, exist_ok=True)
    out = []
    for ext in ('png', 'svg'):
        p = FIGDIR / (name + '.' + ext)
        fig.savefig(p, dpi=dpi, bbox_inches='tight')
        out.append(str(p))
    plt.close(fig)
    return out
