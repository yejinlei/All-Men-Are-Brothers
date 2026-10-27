# build/ 说明 · 分析工具箱与语料装载器

本目录是站点的**离线构建与分析工具**，与前端页面（`docs/`）分离。
分析脚本只读 `docs/texts/versions/`、`docs/data/`，产出写回 `docs/data/`、`docs/fig/`。

## 目录

```
build/
├── lib/                 通用模块（Step 1 分析工具箱）
│   ├── corpus.py        语料装载器：按版本/回次/语体读取，跨版本以『回次 num』对齐
│   ├── textutil.py      简繁转换(OpenCC)/分词(jieba)/标点剥离/字符 n-gram/停用词
│   ├── critics.py       批语装载器：九家批注统一解析（口径同检索页 search.html）
│   ├── sentiment.py     自建情感词典 + 极性/烈度打分（情节情感曲线用）
│   ├── plotstyle.py     统一中文字体/配色，图形同出 PNG + SVG
│   ├── pagegen.py       页面骨架生成（统一导航，含『数字研究』下拉）
│   └── registry.py      版本/批注注册表读写（单一可信源）
├── register_version.py  版本注册与体检（--add / --sync-index / --check）
├── build_*.py           各步骤的分析脚本（见下）
└── requirements.txt     第三方依赖
```

## 调用约定

在 `build/` 下运行的脚本，统一先加入本目录到 `sys.path`：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import corpus, textutil as tu, critics, sentiment, plotstyle, pagegen
```

### 语料装载器

```python
c = corpus.Corpus()
c.version_ids()                      # ['v120','v100',...]
c.nums('v100')                       # 该版本全部回次
c.text('v100', 23, 'fan')            # 第 23 回繁体原文
c.char_count('v100', 23, 'jian', clean=True)   # 汉字数（clean 剥离冀勤注号）
c.common_nums(['v120','v100'])       # 两版本共有回次
```

**跨版本一律以「回次 num」为锚对齐，不用数组下标**（各版本引首/回数不同）。

### 文本工具

```python
tu.t2s('張天師'), tu.s2t('张天师')
tu.cjk_only('話說大宋，仁宗天子。')     # 只留汉字
tu.norm_text(txt)                     # 剥注号 + 统一简体 + 只留汉字（比对用）
tu.char_ngrams(txt, n=2)
tu.STOPWORDS
```

### 样式与出图

```python
plotstyle.setup()
fig, ax = plt.subplots(figsize=(10, 5))
...
plotstyle.save(fig, 'stemma')        # -> docs/fig/stemma.png + stemma.svg
```

中文字体固定为 `Noto Sans CJK SC` / `Noto Serif CJK SC`（系统已装），确保中文不乱码。

### 批语装载器

```python
recs = critics.load_all()            # [{cid,who,tag,color,ver,hui,type,keyword,text}, ...]
critics.count_by_hui(recs)           # {cid: {回次: 条数}}
critics.chars_by_hui(recs)           # {cid: {回次: 字数}}
```

解析口径与站点检索页 `docs/search.html` 完全一致（同一段文本按段落拆条），
统计结果可与检索页「载入 8229 条」对上。

## 分析脚本一览

各脚本互相独立，可按需单独重跑；均在 `build/` 目录下执行，产出写回 `docs/data/`、`docs/fig/`。

| 脚本 | 对应步骤 | 产出 |
|---|---|---|
| `build_stemma.py` | Step 2 版本谱系树 | `docs/data/stemma.json`、`docs/fig/stemma.{png,svg}` |
| `build_reception.py` | Step 3 评点接受史热力图 | `docs/data/critics_heatmap.json`、`docs/fig/reception.{png,svg}` |
| `build_emotion.py` | Step 4 情节情感曲线 | `docs/data/emotion_curve.json`、`docs/fig/emotion.{png,svg}` |
| `build_network.py` | Step 5＋6 网络演化 / 删点实验 | `docs/data/relation_timeline.json`、`docs/data/centrality.json`、`docs/fig/centrality.{png,svg}` |
| `build_stylometry.py` | Step 7 作者归属实验 | `docs/data/stylometry.json`、`docs/fig/stylometry.{png,svg}` |
| `rebuild_bai_v2.py` | 白话层重建 | `docs/texts/versions/*/bai/*.txt` |

```bash
cd build
python3 build_stemma.py && python3 build_reception.py && python3 build_emotion.py \
  && python3 build_network.py && python3 build_stylometry.py
```

> 每个脚本跑完会打印关键指标（如谱系树的两口径相关系数、热力图总量、峰值回次），
> 可与页面上的数字逐一对上；页面只读 JSON，重跑脚本即可更新页面。

## 验收自测

```bash
cd build && python3 -c "
import sys,os; sys.path.insert(0,os.getcwd())
from lib import corpus, critics
c = corpus.Corpus()
print('版本数', len(c.version_ids()))
print('v100 第23回 汉字数', c.char_count('v100',23,'fan'))
print('九家批语总条数', len(critics.load_all()))
"
```

## 依赖

见 `requirements.txt`。缺 `jieba`/`opencc` 时相关模块自动降级（分词退回逐字、
简繁退回原文），n-gram 类分析不依赖分词仍可运行。

## 影像（Step 17）专用脚本

```bash
# 1) 抓取容与堂本真本扫描叶（日本国立公文书馆 IIIF，站内小图）
python3 build/fetch_facsimiles_naj.py --max-px 1200 --concurrency 3   # 断点续传，可分批 --limit N
# 2) 把真本影像挂到 docs/data/facsimiles.json（统一 real_images 结构）
python3 build/attach_real_facsimiles.py
# 3) 体积护栏：单张影像上限 200KB，--fix 就地重压超限影像
python3 build/check_asset_size.py            # 只检查、超限则退出码 1
python3 build/check_asset_size.py --fix      # 就地压缩到上限内
```

**体积策略（硬约束）**：站内单张影像 **长边 1200px、≤ 200KB**；原分辨率叶（单叶数 MB）
与数百 MB–数 GB 的整本影印 PDF **不入仓**，只在 JSON 里登记外部直链（`orig_full` /
`downloads`）。新增影像务必过一遍 `check_asset_size.py`。

> 抓取注意：该馆对 Python 默认 TLS 指纹会回 403，故 `fetch_facsimiles_naj.py` 走 `curl` 取图；
> 并发过高会触发限速，脚本已内置节流与退避，建议 `--concurrency 3`。
