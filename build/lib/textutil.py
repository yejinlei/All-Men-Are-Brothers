"""文本工具：简繁转换 / 分词 / 标点剥离 / 字符 n-gram / 停用词。

供 build/ 下各分析脚本复用。任一外部依赖缺失时自动降级（不抛异常）。
"""
from __future__ import annotations

import re

# ---------------- 简繁转换（OpenCC） ----------------
try:
    from opencc import OpenCC
    _T2S = OpenCC('t2s')
    _S2T = OpenCC('s2t')
    HAS_OPENCC = True
except Exception:  # pragma: no cover
    HAS_OPENCC = False

# ---------------- 分词（jieba） ----------------
try:
    import jieba
    jieba.setLogLevel(20)
    HAS_JIEBA = True
except Exception:  # pragma: no cover
    HAS_JIEBA = False


def t2s(s: str) -> str:
    """繁体 -> 简体。缺 OpenCC 时原样返回。"""
    return _T2S.convert(s) if HAS_OPENCC else s


def s2t(s: str) -> str:
    """简体 -> 繁体。缺 OpenCC 时原样返回。"""
    return _S2T.convert(s) if HAS_OPENCC else s


# 汉字区间（含扩展 A 与兼容区）
_CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
# 标点 / 空白（中英文混排）
_PUNCT = re.compile(
    r'[\s\u3000，。、；：？！“”‘’（）《》〈〉【】〔〕…—－～·,.!?;:'
    r'()\[\]{}<>/\\|`~@#$%^&*_+=—\-]+'
)


def is_cjk(ch: str) -> bool:
    return bool(_CJK.match(ch))


def cjk_only(s: str) -> str:
    """只保留汉字（分析用，去掉标点空白与拉丁字符）。"""
    return ''.join(ch for ch in s if _CJK.match(ch))


def strip_punct(s: str) -> str:
    return _PUNCT.sub('', s)


def strip_note_markers(s: str) -> str:
    """剥离冀勤注体例的正文内嵌注号，如『文本(12)』或『文本（12）』。"""
    return re.sub(r'[（(]\s*\d{1,4}\s*[)）]', '', s)


def tokens(s: str):
    """分词（jieba 不可用时退回逐字）。"""
    if HAS_JIEBA:
        return [w.strip() for w in jieba.cut(s) if w.strip()]
    return list(cjk_only(s))


def char_ngrams(s: str, n: int = 2, step: int = 1):
    """字符 n-gram；先统一简体并只取汉字。返回 list。"""
    s = cjk_only(t2s(s))
    if len(s) < n:
        return []
    return [s[i:i + n] for i in range(0, len(s) - n + 1, step)]


def norm_text(s: str, to_simp: bool = True, drop_note: bool = True) -> str:
    """归一化：可选的注号剥离 -> 可选简繁统一 -> 只留汉字。用于跨版本比对。"""
    if drop_note:
        s = strip_note_markers(s)
    if to_simp:
        s = t2s(s)
    return cjk_only(s)


# 常用停用词（虚词 / 高频功能词），文体计量与词频统计用
STOPWORDS = set("""
的 了 和 与 及 又 也 就 都 而 乃 其 之 於 于 所 为 以 因 由 是 不 在 有 无 這 这 那
里 上 下 来 去 说 道 只 个 他 们 我 你 等 诸 却 亦 便 即 若 如 者 乎 哉 也 夫 盖 但
虽 然 后 今 且 可 已 矣 焉 耳 一 二 三 两 得 地 着 过 把 被 将 见 再 还 更 很 太 使
令 教 吃 遭 受 否 呢 吧 啊 呀 哦 嗯 兮 喏 咱 俺 洒家 小人 郎君 娘子 恁 嘞 咧 哟
""".split())
