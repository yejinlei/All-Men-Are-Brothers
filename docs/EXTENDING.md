# 扩充指南 · 版本与批注

> 站点把「有哪些版本、有哪些批注家」集中到**一份注册表**里：
> **`docs/data/registry.json`**。
> 各页面（阅读器 / 异文对照 / 批注检索 / 首页）和构建脚本都在运行时读取它，
> 所以**新增一个版本或一家批注，只改这一处**，不需要再去翻 4 个 HTML 里的硬编码。
>
> 体检命令：`python3 build/register_version.py --check`

---

## 一、新增一个版本（5 步）

### 第 1 步：放语料

在 `docs/texts/versions/<新id>/` 下建目录，放三套语体与一份回目索引：

```
docs/texts/versions/<新id>/
├── fan/    ch000.txt, ch001.txt, …   ← 繁体
├── jian/   ch000.txt, ch001.txt, …   ← 简体
├── bai/    ch000.txt, ch001.txt, …   ← 白话
└── chapters.json                     ← 回目表
```

`chapters.json` 每条形如：

```json
{ "num": 1, "title": "第一回 张天师祈禳瘟疫 洪太尉误走妖魔",
  "file": "fan/ch001.txt", "file_simp": "jian/ch001.txt", "file_bai": "bai/ch001.txt" }
```

> 若用既有语料转繁简，可复用 `build/rebuild_editions.py`（OpenCC）与
> `build/rebuild_bai_v2.py`（白话重建，含韵文保护）。

### 第 2 步：登记

```bash
python3 build/register_version.py --add <新id> \
  --name "某某本（百回）" \
  --short 某某 \          # 阅读器按钮简称（≤4 字）
  --label 某某本 \        # 异文对照页列标题
  --range 0-100 \         # 覆盖回次区间（起-止）
  --system "繁本·百回" \
  --color "#5a7d3a" \
  --desc "明代某某刊本，……"
```

工具会自动校验目录是否存在、把 `order` 排好、并给出下一步提示。

### 第 3 步：同步语料索引

```bash
python3 build/register_version.py --sync-index
```

各页面用 `docs/texts/versions/versions_index.json` 判断「哪些版本确有语料、
各有多少回」，这一步把新版本补进该索引，并对齐展示名与回数。
**索引里已有的章节清单会原样保留，不会被覆盖**。

### 第 4 步：体检

```bash
python3 build/register_version.py --check
```

**错误（✗）必须清零**；提醒（!）按需处理。若提醒「已注册但索引中无对应条目」，
说明第 3 步还没跑。

### 第 5 步：让它可读

- 阅读器、异文对照、批注检索、首页四页**无需改动**，刷新即可看到新版本。
- 若要让新版本进入**批注检索的可挂载范围**，把它加进对应批注家的 `okVer`。
- 若该版本是本站首发收录、且想让它在**首页版本学时间线**上出现，
  给它加一个 `features` 数组（含要点），时间线会自动多出一张卡。

---

## 二、新增一家批注（3 步）

### 第 1 步：放数据

把批注数据放进 `docs/texts/versions/<id>_comments.json`（或 `_notes.json`）。

### 第 2 步：登记

```bash
python3 build/register_version.py --add-commentary <新id> \
  --tag 某某 \            # 批注按钮简称
  --who 某某氏 \          # 评注者名
  --ok-ver v100,jiqin \   # 可挂载的版本 id（逗号分隔）
  --color "#7a5195" \
  --kind zhongbo          # 数据解析方式，见下
```

登记后：

- **阅读器**（read.html）在该版本下会**自动挂载**这家批注（`okVer` 决定它出现在哪些版本，用户无需选择）；若该版本正文本体自带「」夹批，另需在 `inlineVer` 里登记版本 id；
- **批注检索页**的评点家筛选 chip 会自动多出一个；
- **首页内嵌阅读器**同样按版本自动汇总该批注家。

以上三处均**无需改动 HTML/CSS**。

### 第 3 步：数据格式

`--kind` 决定「正文怎么解析这家批注」。**已有 9 种 kind**（`jin / li / yuan / zhong /
wang / cheng / jiqin / yu / yan`），如果你的新批注数据格式与其中某一家相同，
直接复用该 kind 即可（例如按卷分组的评语可复用 `chengzhu` 的 `volumes` 结构）。

若格式确实不同，需要在两个文件里各加一个分支（**这是唯一需要改代码的情形**）：

| 文件 | 位置 | 作用 |
|---|---|---|
| `docs/read.html` | `EXTRACT` / `applyOneCmt` 的取数分支 | 阅读器页的批注渲染 |
| `docs/js/app.js` | `extraItems(kind, data, chap)` | 首页内嵌阅读器的批注渲染 |

---

## 三、registry.json 字段说明

### versions 条目

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✓ | 唯一标识，同时是语料目录名 |
| `short` | ✓ | 阅读器版本按钮上的简称（建议 ≤4 字） |
| `label` | ✓ | 异文对照页的列标题 |
| `name` | ✓ | 版本全名（下拉、提示用） |
| `range` | ✓ | 覆盖回次区间 `[起, 止]`，对照页据此判断「本回缺」 |
| `order` | | 展示顺序，缺省排到最后 |
| `shortDiff` | | 对照页版本 chip 的简称（更短，如「袁」） |
| `cls` | | 附加样式类（`jade` / `gold` / 空） |
| `color` | | 主题色（对照页列点、时间线标题） |
| `system` | | 版本系统（繁本·百回 / 简本 / 七十回本 …） |
| `date` | | 版本年代 |
| `features` | | 要点数组，**有它才进首页时间线** |
| `desc` | | 一句话简介（按钮 title 提示） |
| `status` | | `ready`（语料就绪，进各页面）/ `planned`（占位，暂不入语料索引） |

### commentaries 条目

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✓ | 唯一标识，批注块样式类为 `cmt-<id>` |
| `tag` | ✓ | 批注简称（金批 / 容本 / 余评 …），显示于批注块角标 |
| `who` | ✓ | 评注者 |
| `file` | ✓ | 数据文件名（位于 `texts/versions/`） |
| `okVer` | ✓ | 可挂载的版本 id 列表 |
| `color` | | 主色（按钮激活态自动取用） |
| `chipCls` | | 检索页 chip 配色类（`red` / `gold` / `indigo` / `jade` / 空） |
| `cls` | | 阅读器批注块样式类，缺省 `cmt-<id>` |
| `kind` | | 取数方式标识，见上节 |
| `order` | | 顺序 |
| `note` | | 备注（溯源说明、收录范围） |

---

## 四、发布前的固定动作

```bash
# 1) 同步语料索引（新增/改名版本后必跑）
python3 build/register_version.py --sync-index

# 2) 体检（错误必须为 0）
python3 build/register_version.py --check

# 3) 前端语法
node --check docs/js/registry.js && node --check docs/js/app.js

# 4) 扫一遍是否有新增的未登记内容
python3 build/register_version.py --discover

# 5) 提交
git add -A && git commit -m "feat(version): 新增 <id>"
git push origin main
```

---

## 五、常见问题

**Q：只加语料不加注册表会怎样？**
A：`--check` 会给出提醒（"目录存在但未登记"），页面则看不到新版本。跑一次
`--discover` 就能发现漏登记。

**Q：登记了新版本，页面怎么还不显示？**
A：多半漏了 `--sync-index`。各页面用 `versions_index.json` 判断「哪些版本确有语料」，
只登记不建索引，版本就不会出现（`--check` 会提醒"已注册但索引中无对应条目"）。
另外 `status` 为 `planned` 的占位版本按设计不进索引。

**Q：`--sync-index` 会不会覆盖我手工整理的章节清单？**
A：不会。它只补缺失条目、对齐展示名与描述、补回数；已有的 `chapters` /
`chapters_count` 一律原样保留。注册表里已删除、但索引里仍有数据的条目会保留并提示。

**Q：新增版本后，异文对照页要改默认列吗？**
A：不用。默认列是固定三列，用户可在页面上勾选任意（最多 4 列）。若想让新版本
成为默认列，改 `diff.html` 里的 `state.activeVers` 初始值即可（一处）。

**Q：阅读器上为什么不提供批注家下拉/按钮？**
A：批注与版本绑定——某版本本就对应特定的评点系统（金批本带金圣叹批、容与堂本带李卓吾评）。
选定版本后，其 `okVer` 涵盖的批注家即**自动挂载**，无需用户逐一选择；阅读器只保留一个
「隐藏批注」总开关。要改变某版本显示的批注家，改注册表里对应条目的 `okVer` 即可。

**Q：批注层配色能自动吗？**
A：能。批注块的角标与文字配色均读取注册表里的 `color`，新增批注家无需写 CSS；
若想要更精细的专用配色，再补一条 `.cmt-block.cmt-<id>{…}` 规则即可（可选）。

**Q：批注家改名或调整可挂载版本？**
A：直接改注册表里对应条目的 `who` / `okVer`，三处页面同步生效。
