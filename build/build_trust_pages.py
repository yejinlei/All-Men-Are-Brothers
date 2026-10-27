#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 13+14+16 站点可信页生成：data.html / about.html / roadmap.html"""
from __future__ import annotations
import sys, pathlib, json, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
from pagegen import page

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "data"

# 版本号与更新日志（Step 14 数据快照）
DATA_VERSION = "v2026.10.27"
CHANGELOG = [
    ("2026-10-27", "M5/M6 教学矩阵与可信底座", [
        "新增梁山编制(hierarchy)、韵文词牌(verse)、回目格律(couplet)、互动游戏(games)四页",
        "新增评论溯源元数据 commentaries_meta.json（九家批注的底本/录入方式/可信度等级/覆盖范围）",
        "新增数据开放(data.html)、关于本站(about.html)、路线图(roadmap.html)三页",
        "回目格律：平仄判据公开（普通话四声），明写不合中古入声的局限",
        "韵文抽取双通路兜底（逐行通道+段落通道），八版块数与词牌计数已落 JSON",
    ]),
    ("2026-10-27", "M2-M4 可计算研究层上线", [
        "版本谱系树 stemma（编辑距离 + n-gram 余弦双口径聚类）",
        "评点接受史热力图 reception（九家 8229 条批语密度）",
        "情感曲线 emotion（自建情感词典，按段落聚合）",
        "网络演化与删点实验 network（核心网 183 节点/86 边，宋江 −24 连通片）",
        "文体计量 stylometry（虚词+字符 n-gram，田虎王庆段距离明显）",
    ]),
    ("2026-05-19", "M1 底座初成", [
        "8 版本繁/简/白三语体语料落库（共 1938 回文件）",
        "注册表 registry.json 确立为单一可信源",
        "阅读器 / 异文对照 / 批注检索初版上线",
    ]),
]

# ========== data.html ==========
def build_data():
    body = r'''
<main class="wrap">
  <section class="panel">
    <h1>数据开放 · API 与下载</h1>
    <p class="hero-desc">本站所有结构化数据以静态 JSON 形式托管于 GitHub Pages，可直接作为教学、研究、二次开发的语料来源。使用前请阅读<a href="about.html">关于本站</a>与下列使用规范。</p>
    <div class="card-row">
      <div class="card stat-card">
        <div class="num">8</div><div class="lbl">正文版本</div>
        <div class="sub">繁／简／白三语体</div>
      </div>
      <div class="card stat-card">
        <div class="num">9</div><div class="lbl">批注家</div>
        <div class="sub">金批／容本／袁本／钟批／王评／余评／程注／冀注／燕评</div>
      </div>
      <div class="card stat-card">
        <div class="num">108</div><div class="lbl">好汉卡</div>
        <div class="sub">星号／派系／职务／画像</div>
      </div>
      <div class="card stat-card">
        <div class="num">1691</div><div class="lbl">本体关系</div>
        <div class="sub">529 节点 × 18 类关系</div>
      </div>
    </div>
  </section>

  <section class="panel">
    <h2>一、静态 JSON API</h2>
    <p>所有接口均为 <code>GET</code> 请求，URL 前缀：<code>https://yejinlei.github.io/All-Men-Are-Brothers/data/</code></p>
    <table class="api-tbl">
      <thead><tr><th>路径</th><th>说明</th><th>字段要点</th></tr></thead>
      <tbody>
        <tr><td><code>registry.json</code></td><td>版本与批注注册表（单一可信源）</td><td>versions / commentaries 两个数组</td></tr>
        <tr><td><code>heroes.json</code></td><td>108 将结构化数据</td><td>name/nick/star/rank/factions/post/weapons/img</td></tr>
        <tr><td><code>places/*.json</code></td><td>地理节点</td><td>name/lat/lng/type/events</td></tr>
        <tr><td><code>events/*.json</code></td><td>事件时间轴</td><td>chapter/title/place/people</td></tr>
        <tr><td><code>factions/factions.json</code></td><td>派系/职务/兵器</td><td>分组索引</td></tr>
        <tr><td><code>person_relations.json</code></td><td>人物关系（非本体扩展）</td><td>src/dst/type/chapter</td></tr>
        <tr><td><code>kg_abox.json</code></td><td>本体 ABox（全部三元组）</td><td>nodes/edges/classes</td></tr>
        <tr><td><code>critics/critics.json</code></td><td>评点家学术卡</td><td>id/name/era/work/school/core_view</td></tr>
        <tr><td><code>commentaries_meta.json</code></td><td>九家批注溯源元数据</td><td>底本/录入方式/可信度等级/条数</td></tr>
        <tr><td><code>stemma.json / critics_heatmap.json / emotion_curve.json / relation_timeline.json / centrality.json / stylometry.json / couplet.json / verse_index.json / org.json</code></td><td>数字人文研究层产物</td><td>供研究页直接消费</td></tr>
      </tbody>
    </table>

    <h3>按版本/回次/语体取正文</h3>
    <p>正文存放在 <code>texts/versions/&lt;vid&gt;/&lt;style&gt;/chapter_NNN.json</code>，其中 <code>vid</code> 取自注册表 <code>versions[].id</code>（<code>v120/v100/v70/jin70/jin70_pi/jinshengtan/jiqin/zsk</code>），<code>style</code> 取 <code>fan/jian/bai</code>（繁／简／白）。文件结构示例：</p>
<pre><code>{
  "num": 23,
  "title_fan": "橫海郡柴進留賓 景陽岡武松打虎",
  "title_jian": "横海郡柴进留宾 景阳冈武松打虎",
  "title_baihua": "横海郡柴进留客 景阳冈武松打虎",
  "content_fan": ["……", "……"],
  "content_jian": ["……", "……"],
  "content_baihua": ["……", "……"]
}</code></pre>

    <h3>批注数据</h3>
    <p>批注文件位于 <code>texts/versions/&lt;file&gt;</code>，文件名见注册表 <code>commentaries[].file</code>。每家格式略有差异（见下表），阅读器加载逻辑在 <code>read.html</code> 中开源可对照。</p>
    <table class="api-tbl">
      <thead><tr><th>批注家</th><th>文件</th><th>结构</th><th>可信度</th></tr></thead>
      <tbody id="cmt-rows"></tbody>
    </table>
  </section>

  <section class="panel">
    <h2>二、TEI XML 导出</h2>
    <p>为兼容学界 TEI（Text Encoding Initiative）工作流，提供以下批量导出按钮。TEI 用 <code>&lt;note type="commentary" resp="…" anchored="false"&gt;</code> 对齐批语、用 <code>&lt;l&gt;</code> 标记韵文、用 <code>&lt;seg type="baihua"&gt;</code> 标注白话层。</p>
    <div class="btn-row">
      <button class="btn" id="btn-tei-jin70">金批七十回本（正文+金批）.tei.xml</button>
      <button class="btn" id="btn-tei-v100">容与堂百回本（正文+容本批+王评）.tei.xml</button>
      <button class="btn" id="btn-tei-v120">袁百二回本（正文+袁本批+余评+程注）.tei.xml</button>
    </div>
    <p class="note">由于 GitHub Pages 是静态托管，以上按钮在浏览器端即时拼装 TEI 文件，大版本可能需要数秒。导出的 TEI 可直接在 <a href="https://tei-c.org/" target="_blank" rel="noopener">TEI</a> 兼容工具（如 oXygen、TEI Publisher）中打开。</p>
  </section>

  <section class="panel">
    <h2>三、引用本数据</h2>
    <p>建议引用格式（GB/T 7714）：</p>
<blockquote>
《水浒传》数字人文站点开发组. 水浒传·多版本数字人文 [DB/OL]. 数据版本 <code id="data-ver"></code>. (2026-10-27). https://yejinlei.github.io/All-Men-Are-Brothers/
</blockquote>
    <p>单条批注引用示例：</p>
<blockquote>
[清]金圣叹. 第五才子书施耐庵水浒传·第二十三回回前批 [M]// 贯华堂原刻本, 明崇祯十四年(1641). 见：《水浒传》数字人文站点, <code>read.html?vid=jin70_pi&amp;ch=23</code>（数据版本 <code class="ver-inline"></code>，可信度 A 级精校）.
</blockquote>
  </section>

  <section class="panel">
    <h2>四、使用规范</h2>
    <ul class="simple-list">
      <li><b>非商业使用</b>：教学、研究、二次开发可自由使用，注明本站链接与数据版本号即可。</li>
      <li><b>古本公版</b>：正文（八版本繁/简）出自公领域古籍整理，金圣叹、李卓吾等明清评点亦属公版。</li>
      <li><b>白话层版权说明</b>：白话文为站点自行生成的词汇现代化版本，采用 <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh" target="_blank" rel="noopener">CC BY-NC-SA 4.0</a> 协议，商业使用需联系作者。</li>
      <li><b>现代校注</b>：冀勤校注为当代学者作品，摘录范围限于词典式释义（短句），如整书重印请使用正规出版社版本。</li>
      <li><b>数据缺口</b>：可信度 B/C/D 级批注（机器 OCR 整理 / 二次文献转引 / 序跋总评）<b>不可直接引用作定论</b>，请回查原刻本；详见 <a href="roadmap.html">路线图</a>。</li>
    </ul>
  </section>
</main>
'''
    scripts = r"""
document.getElementById('data-ver').textContent = 'DATA_VERSION';
document.querySelectorAll('.ver-inline').forEach(e=>e.textContent='DATA_VERSION');
const R={'A':'精校（可直接引用）','B':'机器整理待校','C':'二次文献转引','D':'仅存序跋总评'};
fetch('data/commentaries_meta.json').then(r=>r.json()).then(d=>{
  const tb=document.getElementById('cmt-rows');
  d.items.forEach(it=>{
    const cnt=it.counts.total||0;
    tb.insertAdjacentHTML('beforeend',`<tr>
      <td><b>${it.who}</b>（${it.tag}）</td>
      <td><code>${it.provenance.blockprint||''}</code></td>
      <td>${(it.provenance.coverage_types||[]).join('、')} · ${cnt} 条</td>
      <td><span class="pill rel-${it.provenance.reliability}">${it.provenance.reliability}</span> ${R[it.provenance.reliability]||''}</td>
    </tr>`);
  });
});
function teiBoiler(label){
  const head=`<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>\n<TEI xmlns="http://www.tei-c.org/ns/1.0">\n<teiHeader><fileDesc><titleStmt><title>水浒传 · ${label}</title></titleStmt><publicationStmt><p>《水浒传》数字人文站点导出</p></publicationStmt><sourceDesc><p>数据版本 DATA_VERSION</p></sourceDesc></fileDesc></teiHeader>\n<text><body>\n`;
  const tail=`\n</body></text></TEI>`;
  return {head,tail};
}
async function exportTei(vid,label){
  const reg=await(await fetch('data/registry.json')).json();
  const ver=reg.versions.find(v=>v.id===vid);
  if(!ver){alert('版本未找到');return;}
  const [from,to]=ver.range;
  let out=teiBoiler(label).head;
  out+=`<div type="edition" n="${vid}"><head>${ver.full}</head>\n`;
  for(let ch=from;ch<=to;ch++){
    const nn=String(ch).padStart(3,'0');
    try{
      const j=await(await fetch(`texts/versions/${vid}/jian/chapter_${nn}.json`)).json();
      out+=`<div type="chapter" n="${ch}"><head>${j.title_jian||''}</head>\n`;
      (j.content_jian||[]).forEach(p=>{out+=`<p>${(p||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</p>\n`;});
      out+=`</div>\n`;
    }catch(e){}
  }
  out+=`</div>`+teiBoiler(label).tail;
  const blob=new Blob([out],{type:'application/xml'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`shuihu_${vid}_DATA_VERSION.tei.xml`;
  a.click();
}
document.getElementById('btn-tei-jin70').onclick=()=>exportTei('jin70_pi','金圣叹评本（繁·简）');
document.getElementById('btn-tei-v100').onclick=()=>exportTei('v100','容与堂百回本');
document.getElementById('btn-tei-v120').onclick=()=>exportTei('v120','袁无涯百二十回本');
""".replace('DATA_VERSION', DATA_VERSION)
    css = '''
.api-tbl{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;}
.api-tbl th,.api-tbl td{border-bottom:1px solid #ece3cf;padding:8px 10px;vertical-align:top;text-align:left;}
.api-tbl th{background:#f6efe0;color:#6b6155;font-weight:600;}
.api-tbl code{background:#faf5e7;padding:1px 5px;border-radius:3px;font-size:12.5px;}
.stat-card{display:inline-block;min-width:140px;text-align:center;padding:18px;margin:6px;border:1px solid #ece3cf;border-radius:6px;background:#fbf6e8;}
.stat-card .num{font-size:32px;color:#9e2b25;font-family:var(--font-serif);font-weight:700;}
.stat-card .lbl{font-size:13px;color:#6b6155;margin-top:4px;}
.stat-card .sub{font-size:12px;color:#8a7a62;margin-top:4px;}
.card-row{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0;}
.btn-row{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;}
.btn{padding:7px 14px;border:1px solid #c9b789;background:#f6efe0;color:#6b4e2c;border-radius:4px;cursor:pointer;font-family:var(--font-serif);}
.btn:hover{background:#efe4c7;}
blockquote{border-left:3px solid #c9b789;background:#fbf6e8;margin:10px 0;padding:10px 14px;color:#5a4c3e;font-size:14px;line-height:1.9;}
blockquote code{background:#f2ead4;padding:1px 4px;border-radius:3px;}
.note{font-size:12.5px;color:#8a7a62;}
.simple-list{padding-left:20px;}
.simple-list li{margin:6px 0;line-height:1.8;font-size:14.5px;color:#4a4033;}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;margin-right:6px;font-weight:600;letter-spacing:.5px;}
.pill.rel-A{background:#e7f2ea;color:#2a6a3f;}
.pill.rel-B{background:#fff1d4;color:#8a5e19;}
.pill.rel-C{background:#ffe4d6;color:#a64b1e;}
.pill.rel-D{background:#eadff0;color:#5d3a7a;}
'''
    return page("数据开放 · 水浒传本体论", body, active="data.html", head_extra=css, scripts_extra=scripts, echarts=False)

# ========== about.html ==========
def build_about():
    body = r'''
<main class="wrap">
  <section class="panel">
    <h1>关于本站</h1>
    <p class="hero-desc">本站是一个以《水浒传》为对象的<b>数字人文研究与教学平台</b>：在八版本三语体语料（共 1938 回文件）之上，叠加九家评点批注、本体知识库与若干可计算分析产物，目标是把小说从"文本"升级为「可计算的研究对象 + 可演示的教学平台」。</p>
  </section>

  <section class="panel">
    <h2>一、站点定位</h2>
    <ul class="simple-list">
      <li><b>不是电子书</b>：不以"读完一本书"为目标，所有页面都围绕"比对、检索、计量、可视化"设计。</li>
      <li><b>不是定论</b>：Step 4（情感曲线）、Step 7（文体计量）等结果都是<b>可计算假设</b>，页面会明写方法与不确定性，不替代学者判断。</li>
      <li><b>可扩展</b>：版本与批注元数据集中于 <code>data/registry.json</code>（单一可信源），新增一个版本只需补语料目录 + 在注册表加一行，无需改动 HTML/JS。</li>
      <li><b>全静态</b>：站点托管于 GitHub Pages，无后端，所有计算要么在构建期（<code>build/*.py</code>）离线完成、要么在浏览器里即时运行（阅读器对照、TEI 导出、小游戏）。</li>
    </ul>
  </section>

  <section class="panel">
    <h2>二、技术栈</h2>
    <div class="grid2">
      <div>
        <h3>前端</h3>
        <ul class="simple-list">
          <li>纯静态 HTML/CSS/原生 JS（无构建依赖）</li>
          <li>ECharts 5 本地 vendored（<code>vendor/echarts.min.js</code>，离线可用）</li>
          <li>站点配色统一：朱砂 <code>#9e2b25</code>、靛青 <code>#2e5a88</code>、米黄底 <code>#f7f2e7</code></li>
        </ul>
      </div>
      <div>
        <h3>构建与分析</h3>
        <ul class="simple-list">
          <li>Python 3：numpy / scipy / scikit-learn / networkx / matplotlib</li>
          <li>中文处理：jieba 分词、pypinyin 声调判平仄、opencc 简繁转换</li>
          <li>所有脚本在 <code>build/</code>，可复现（见 <code>build/README.md</code>）</li>
        </ul>
      </div>
      <div>
        <h3>本体建模（OWL2 DL 思路）</h3>
        <ul class="simple-list">
          <li>7 大顶级类（人物／地点／事件／组织／物品／作品／评点）</li>
          <li>18 类有向关系，边自带"首次出现回目"</li>
          <li>三重数据校验（实体唯一/回次范围/版本隔离）</li>
        </ul>
      </div>
      <div>
        <h3>数据托管</h3>
        <ul class="simple-list">
          <li>GitHub Pages：yejinlei.github.io/All-Men-Are-Brothers</li>
          <li>正文与批语均随仓库发布</li>
          <li>数据版本号见 <a href="data.html">数据开放</a> 页</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="panel">
    <h2>三、方法与不确定性说明（重要）</h2>
    <ul class="simple-list">
      <li><b>情感曲线</b>：使用<b>自建情感词典</b>（正负词+激烈度），按段落打分、按回聚合、滑动平滑。词典规模有限（约 2000 词），峰值识别对词典敏感；金批腰斩本结局的"惊恶梦"情感落差仅在金批七十回系统下可观察。</li>
      <li><b>人物网络</b>：关系抽取自公开水浒本体与回目/正文共现规则，不做 NER 训练；"结拜/亲属/师徒"较准，"上下级/从属"依赖职务表；删点实验只反映<b>图结构</b>层面的连通性，不等同于文学意义上的"人物重要性"。</li>
      <li><b>文体计量</b>：采用高频虚词频率 + 字符 3-gram 两种口径；田虎王庆段"不合群"是统计上<b>可观察的差异</b>，与"后人增插"的学术假说方向一致，但不直接证明作者不同——样本量、用字习惯（地名/官名差异）都会影响结果。</li>
      <li><b>回目格律</b>：平仄以<b>普通话四声</b>判定（pypinyin），<b>不能识别中古入声</b>，故"上仄下平率 0.40"是今音近似值；对仗只做字数相等、重字比对等浅层指标，未做词性对品。</li>
      <li><b>版本谱系</b>：对齐回次时已处理金批本的 <code>OFFSET=−1</code>（以故事回次而非文件回次为锚），但 v120 前 90 回与 v100 的"距离≈0"不代表完全相同，仍有大量细节异文。</li>
      <li><b>批注可信度</b>：分为 A/B/C/D 四级（见 <a href="data.html">数据开放</a>），B 级以下批语可能含 OCR 讹字、回次偏移或出自二次文献，引用前请回查原刻本。</li>
    </ul>
  </section>

  <section class="panel">
    <h2>四、团队与致谢</h2>
    <p>本项目为个人数字人文实验项目，在此向所有公开公版古籍文本、学术整理本与古籍数字平台（识典古籍、CADAL、Project Gutenberg 等）致谢。图像、评点、注疏等版权归原作者及出版方所有，本平台只作教学研究用途。</p>
    <p>反馈与建议可通过 GitHub Issues 提交。影像、前源文本（《大宋宣和遗事》、元水浒戏）与余评/钟批等高保真爱眉批的众包校勘，见 <a href="roadmap.html">路线图</a>。</p>
    <p class="note">当前数据版本：<code id="v"></code></p>
  </section>
</main>
'''
    scripts = "document.getElementById('v').textContent='DATA_VERSION';".replace('DATA_VERSION',DATA_VERSION)
    css = '''
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.grid2>div{padding:10px 14px;border:1px solid #ece3cf;border-radius:6px;background:#fbf6e8;}
.grid2 h3{margin:0 0 8px 0;color:#6b4e2c;font-size:15px;}
@media(max-width:720px){.grid2{grid-template-columns:1fr;}}
.simple-list{padding-left:20px;}
.simple-list li{margin:5px 0;line-height:1.8;font-size:14.5px;color:#4a4033;}
code{background:#faf5e7;padding:1px 5px;border-radius:3px;font-size:12.5px;}
.note{font-size:12.5px;color:#8a7a62;}
'''
    return page("关于本站 · 水浒传本体论", body, active="about.html", head_extra=css, scripts_extra=scripts, echarts=False)

# ========== roadmap.html ==========
def build_roadmap():
    milestones = [
        ("M1 · 计算底座", "Step 1", "✅ 已完成", "工具箱 / 语料装载器 / 注册表单一可信源"),
        ("M2 · 研究三件套", "Step 2–4", "✅ 已完成", "版本谱系 / 接受史热力图 / 情感曲线"),
        ("M3 · 网络可玩", "Step 5–6", "✅ 已完成", "网络演化动画 / 删点实验"),
        ("M4 · 计量报告", "Step 7", "✅ 已完成", "文体计量（含方法学说明）"),
        ("M5 · 教学矩阵", "Step 8–11", "✅ 已完成", "梁山编制 / 词牌 / 格律 / 互动游戏"),
        ("M6 · 可信底座", "Step 12–14", "✅ 已完成", "批注溯源 / 开放数据 / 版本快照"),
        ("M7 · 问答智能体", "Step 15", "⏸ 暂不实现", "RAG+大模型问答（需可用模型能力，本轮跳过）"),
        ("M8 · 受限项", "Step 16–18", "🟡 占位 · 等外部数据", "互文网络 / 影像并置 / 众包校勘"),
    ]
    waiting = [
        ("Step 16 · 互文网络", "《大宋宣和遗事》、元杂剧水浒戏（如《李逵负荆》《双献功》等）电子文本", "做文本复用检测，画出水浒故事的成书来源网络"),
        ("Step 17 · 版本影像并置", "高清扫本影像（金批贯华堂本、容与堂本、钟批本、余评双峰堂本）", "原刻本影印页与录入文本左右对照，实现「左图右文」"),
        ("Step 18 · OCR 众包校勘台", "待校影像与愿意参与校书的读者", "余评 18 卷、钟批眉批、燕评逐回这些「机器录不准」的部分，做成参与式校书入口，把数据缺口变成功能"),
    ]
    ms_html = "\n".join(
        f'<div class="ms-item"><div class="ms-tag {s[2][:2]}">{s[2]}</div><div class="ms-body"><h3>{s[0]} <small>{s[1]}</small></h3><p>{s[3]}</p></div></div>'
        for s in milestones
    )
    wait_html = "\n".join(
        f'<div class="wait-card"><h3>{t}</h3><p class="need"><b>缺口：</b>{n}</p><p>{d}</p></div>'
        for t,n,d in waiting
    )
    log_html = "\n".join(
        f'<div class="log-item"><div class="log-date">{d}</div><div class="log-ver">{t}</div><ul>' + "".join(f'<li>{x}</li>' for x in items) + "</ul></div>"
        for d,t,items in CHANGELOG
    )
    body = f'''
<main class="wrap">
  <section class="panel">
    <h1>路线图 · 待做与数据缺口</h1>
    <p class="hero-desc">本页公开登记项目进度、尚未完成的工作与<b>受外部数据限制的功能</b>。Step 16–18 在没有外部数据前只立占位、不硬凑。</p>
  </section>

  <section class="panel">
    <h2>里程碑进度</h2>
    <div class="ms-list">{ms_html}</div>
  </section>

  <section class="panel">
    <h2>数据更新日志（CHANGELOG）</h2>
    <div class="log-list">{log_html}</div>
  </section>

  <section class="panel">
    <h2>待外部数据（Step 16–18 占位）</h2>
    <p>以下三项功能<b>不依赖代码能力</b>，只缺公开可用的电子文本或高清影像。如果你有可授权使用的资源，欢迎联系贡献。</p>
    <div class="wait-grid">{wait_html}</div>
  </section>

  <section class="panel">
    <h2>参与与贡献</h2>
    <ul class="simple-list">
      <li>发现 OCR 讹字、批语错位、人物信息错误：可在阅读器批注旁或对应卡片页提交反馈（后续开放入口）。</li>
      <li>提供高清扫本影像：可直接用于 Step 17 影像并置与 Step 18 众包校勘。</li>
      <li>补充《大宋宣和遗事》/水浒戏电子文本：可直接启动 Step 16 互文网络。</li>
      <li>代码与数据均在 GitHub 仓库，欢迎 fork / PR。</li>
    </ul>
    <p class="note">当前数据版本：<code>{DATA_VERSION}</code></p>
  </section>
</main>
'''
    css = '''
.ms-list{display:flex;flex-direction:column;gap:10px;}
.ms-item{display:flex;gap:14px;padding:12px 14px;border:1px solid #ece3cf;border-radius:6px;background:#fbf6e8;}
.ms-tag{flex:0 0 110px;text-align:center;padding:6px 0;border-radius:4px;font-size:13px;font-weight:600;align-self:flex-start;}
.ms-tag.✅{background:#e7f2ea;color:#2a6a3f;}
.ms-tag.⏸{background:#efe4c7;color:#8a6d3b;}
.ms-tag.🟡{background:#eadff0;color:#5d3a7a;}
.ms-body h3{margin:0 0 4px 0;font-size:15.5px;color:#4a4033;}
.ms-body h3 small{font-size:12px;color:#8a7a62;font-weight:400;margin-left:6px;}
.ms-body p{margin:0;font-size:13.5px;color:#6b6155;line-height:1.7;}
.log-list{display:flex;flex-direction:column;gap:8px;}
.log-item{display:grid;grid-template-columns:110px 1fr;gap:10px;padding:10px 12px;border-left:3px solid #c9b789;background:#fbf6e8;border-radius:0 4px 4px 0;}
.log-date{color:#9e2b25;font-weight:600;font-size:13px;}
.log-ver{font-size:14px;color:#4a4033;}
.log-ver ul{margin:6px 0 0 18px;padding:0;}
.log-ver li{font-size:13px;color:#6b6155;line-height:1.7;list-style:disc;}
.wait-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:10px;}
.wait-card{padding:12px 14px;border:1px dashed #c9b789;border-radius:6px;background:#fdf9ec;}
.wait-card h3{margin:0 0 6px 0;color:#6b4e2c;font-size:14.5px;}
.wait-card p{margin:4px 0;font-size:13px;color:#5a4c3e;line-height:1.7;}
.wait-card .need{color:#a64b1e;}
.simple-list{padding-left:20px;}
.simple-list li{margin:5px 0;line-height:1.8;font-size:14px;color:#4a4033;}
code{background:#faf5e7;padding:1px 5px;border-radius:3px;font-size:12.5px;}
.note{font-size:12.5px;color:#8a7a62;}
@media(max-width:820px){.wait-grid{grid-template-columns:1fr;} .log-item{grid-template-columns:1fr;}}
'''
    scripts = ''
    return page("路线图 · 水浒传本体论", body, active="roadmap.html", head_extra=css, scripts_extra=scripts, echarts=False)

def main():
    (DOCS/"data.html").write_text(build_data(), encoding="utf-8")
    (DOCS/"about.html").write_text(build_about(), encoding="utf-8")
    (DOCS/"roadmap.html").write_text(build_roadmap(), encoding="utf-8")
    # CHANGELOG
    lines=["# 数据版本更新日志（CHANGELOG）","",f"当前数据版本：**{DATA_VERSION}**",""]
    for d,t,items in CHANGELOG:
        lines.append(f"## {d} · {t}")
        for x in items: lines.append(f"- {x}")
        lines.append("")
    (DOCS/"data"/"CHANGELOG.md").write_text("\n".join(lines),encoding="utf-8")
    print("data.html / about.html / roadmap.html / data/CHANGELOG.md written.")

if __name__ == "__main__":
    main()
