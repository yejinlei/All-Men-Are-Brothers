# 水浒传 · 本体论数字人文研究 (All Men Are Brothers)

> Outlaws of the Marsh — An Ontological Digital Humanities Study

基于版本学与本体论（Ontology）方法，对《水浒传》七大版本系统进行结构化知识建模。
参考 [The Story of the Stone](https://yejinlei.github.io/The-Story-of-the-Stone) 本体论构建范式。

## 版本收录

| 版本 | 回数 | 字数 | 特色 |
|---|---|---|---|
| 百二十回水浒全传（袁无涯本） | 120回 | 92万×3 | 繁本最完整，含征田虎王庆 |
| 百回容与堂本 | 100回 | 79万×3 | 繁本祖本 |
| 七十回金圣叹评本 | 70回 | 57万×3 | 贯华堂腰斩本 |
| 金圣叹繁体底本（Gutenberg） | 70回 | 54万×3 | 公领域繁体原文 |
| 征四寇简本后段 | 38回 | 26万×3 | 简本系统 |
| **冀勤校注本**（2012） | 100回 | 86万×3 | **6817条校注**，容与堂底本 |
| **金圣叹批评本**（带批） | 71回 | 金批齐全 | **回前总批＋句中夹批** |

所有版本均提供 **繁体 / 简体 / 白话** 三版对照阅读。

## 本体论建模

- **108将本体**：星号、绰号、职司、兵器、出身、逼上山类型、派系、结局
- **空间地理本体**：42个关键地点（梁山泊、五台山、野猪林、曾头市、乌龙岭等）
- **叙事结构本体**：32个核心事件时间线，叙事张力曲线图
- **人物关系图谱**：Canvas力导向图（宋江为核心）
- **本体推演规则**：五大命运模式（官逼民反/战败归降/主动投奔/技术人才/被赚上山）、忠义悖论、佛道解脱vs忠义殒命

## 本地预览

```bash
cd docs
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## GitHub Pages

访问：https://yejinlei.github.io/All-Men-Are-Brothers/

## 目录结构

```
├── docs/                    # GitHub Pages 站点根目录
│   ├── index.html           # 单页应用入口
│   ├── css/style.css        # 宣纸风格样式
│   └── texts/versions/      # 7个版本的章节JSON（繁/简/白三版）
├── raw/                     # 原始文本
├── data/                    # 解析后的结构化JSON
├── build/                   # 构建脚本
└── 03_本体论规范/            # OWL本体TTL定义
```
