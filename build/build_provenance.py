#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 12 · 批注溯源卡（可信基础设施）

读取 docs/data/registry.json 与九家批注原始文件，为每一家汇总：
  - 底本 / 刊刻年代 / 现藏或电子底本来源
  - 录入方式（人工录入 / 古籍库 OCR 整理 / 公版电子文本校订 / 二次文献辑录）
  - 可信度等级（A 精校 / B 机器整理待校 / C 二次文献转引 / D 仅存序跋总评）
  - 已覆盖条目数、覆盖回目范围
  - 使用边界（哪些回缺、哪些是总评/夹批/注）
  - 校订记录（最近修订时间）

产出 docs/data/commentaries_meta.json，不改动原批注文件；
阅读器与检索页可在悬停胶囊时展示「来源卡」。
"""
from __future__ import annotations
import json, os, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
VERS = ROOT / "docs" / "texts" / "versions"

# 九家批注的人工溯源信息（来源学记录，单条唯一可信源）
PROVENANCE = {
    "jinpi": {
        "blockprint": "明崇祯十四年（1641）贯华堂原刻本《第五才子书施耐庵水浒传》",
        "holding": "国家图书馆、上海图书馆分藏；通行整理本以中华书局 1975 年影印贯华堂本为底本",
        "digital_source": "Project Gutenberg #23863 繁体公领域七十回本（jin70_pi 繁/jinshengtan 简双份），夹批〔〕内嵌正文",
        "entry_method": "公版电子文本＋人工校订；回前总批依中华书局整理本过录",
        "reliability": "A",
        "reliability_desc": "精校——金批七十回回前总评全录，夹批随正文嵌入，条数统计可与原书互校",
        "coverage_types": ["回前总批", "句间夹批"],
        "limits": "未独立收录眉批（眉批多与夹批位置重叠，合并处理）；七十回系统，不含征四寇",
        "first_added": "2026-05",
        "last_revised": "2026-10-27",
    },
    "lizhuo": {
        "blockprint": "明万历三十八年（1610）杭州容与堂刊《李卓吾先生批评忠义水浒传》一百回",
        "holding": "日本内阁文库藏本；国内有中华书局、上海古籍影印本",
        "digital_source": "容与堂本回末总评；李贽《忠义水浒传叙》；怀林《批评水浒传述语》《梁山泊一百单八人优劣》等附录；学界公开发表之辑录",
        "entry_method": "二次文献辑录＋回末总评人工录入；眉批/夹批暂未逐条逐位置落库",
        "reliability": "C",
        "reliability_desc": "二次文献转引——目前仅完整收录卷首叙、述语及 26 回回末总评（与批评家卡片 41 条吻合），正文眉夹批待影像到位后众包校勘",
        "coverage_types": ["卷首叙", "述语附录", "回末总评"],
        "limits": "眉批/夹批未入；百回本系统，不含征田虎王庆",
        "first_added": "2026-05",
        "last_revised": "2026-10-27",
    },
    "yuanwy": {
        "blockprint": "明万历四十二年（1614）袁无涯书种堂刊《李卓吾评忠义水浒全传》一百二十回",
        "holding": "日本内阁文库、北京图书馆分藏；北京大学出版社、中华书局有影印本",
        "digital_source": "袁本《出像评点忠义水浒全书发凡》、学界已刊布的回末总评与眉批引述；非完整 OCR",
        "entry_method": "发凡/总评人工录入，眉批据学者对校引述转引",
        "reliability": "C",
        "reliability_desc": "二次文献转引——目前仅收卷首发凡 2 则与若干代表性回评，未做逐回眉批/夹批",
        "coverage_types": ["发凡", "回末总评（部分）"],
        "limits": "眉批/侧批未入；全传 120 回系统",
        "first_added": "2026-05",
        "last_revised": "2026-10-27",
    },
    "zhongbo": {
        "blockprint": "明天启四—五年（1624-25）四知馆/积庆堂刊《钟伯敬先生批评水浒忠义传》一百卷一百回",
        "holding": "法国国家图书馆（Chinois 9571-9580）、CADAL 等有扫描件",
        "digital_source": "识典古籍 CADAL02015977 号机器 OCR 整理本",
        "entry_method": "古籍平台机器 OCR 整理＋人工核校回评标题与卷首《人品评》",
        "reliability": "B",
        "reliability_desc": "机器整理待校——卷首《水浒传人品评》9 则已录，正文眉批/侧批受 OCR 准确率限制，目前仅展示回末总评 11 则，眉批待影像到位后众包校书",
        "coverage_types": ["卷首人品评", "回末总评（部分）"],
        "limits": "眉批/侧批未逐条入；百回系统，不含田虎王庆",
        "first_added": "2026-06",
        "last_revised": "2026-10-27",
    },
    "wangping": {
        "blockprint": "清顺治十四年（1657）醉耕堂刊《评论出像水浒传》七十回（王仕云·望如评）",
        "holding": "北京大学图书馆、国家图书馆藏本",
        "digital_source": "识典古籍 HY1540《水滸傳》（评论出像水浒传）机器 OCR 整理本，回次依「圣叹外书第 N 回」推定",
        "entry_method": "古籍平台机器 OCR 整理＋回次人工对齐贯华堂 70 回",
        "reliability": "B",
        "reliability_desc": "机器整理待校——57 则回末总评已按回对齐，OCR 讹字待人工二校；未收录图像眉批",
        "coverage_types": ["回末总评"],
        "limits": "无眉批/夹批；七十回系统",
        "first_added": "2026-06",
        "last_revised": "2026-10-27",
    },
    "yuxiangdou": {
        "blockprint": "明万历二十二年（1594）双峰堂刊《京本增补校正全像忠义水浒志传评林》二十五卷",
        "holding": "日本日光山轮王寺慈眼堂藏本（1956 年文学古籍刊行社影印）",
        "digital_source": "卷首《题水浒传叙》《水浒辨》《水浒传目录》；正文评点据影印本与学界整理本辑录",
        "entry_method": "卷首叙文人工录入；正文「评曰」「批云」评语依影印本过录",
        "reliability": "B",
        "reliability_desc": "原刻本过录但仅做初校——卷首三篇叙/辨/评林姓氏全录，正文「评曰」段已落位 192 条，简本系统独有文字需与繁本系统分卷处理",
        "coverage_types": ["卷首叙", "正文评曰批语"],
        "limits": "评林本为简本系统，其「评曰」夹注位置按回次挂载到八版本通用回次，可能与繁本文字位置不完全对齐；图像眉批暂缺",
        "first_added": "2026-06",
        "last_revised": "2026-10-27",
    },
    "chengzhu": {
        "blockprint": "清程穆衡撰《水浒传注略》（手稿本，分二卷）",
        "holding": "南京图书馆藏清抄本；收入《水浒传资料汇编》（马蹄疾编，中华书局 1980；朱一玄《水浒传资料汇编》2002）",
        "digital_source": "据《水浒传资料汇编》排印本条目逐条辑出，注条按关键词定位到所在回次",
        "entry_method": "二次文献辑录＋回次人工标注",
        "reliability": "C",
        "reliability_desc": "二次文献转引——375 条名物/地理/制度训注已收，部分条目的回次定位依关键词近似，可能有前后一两回偏差",
        "coverage_types": ["名物训注", "地理制度考"],
        "limits": "无文学评点；原文生僻字排印本有讹；部分条目跨回出现",
        "first_added": "2026-06",
        "last_revised": "2026-10-27",
    },
    "jiqin": {
        "blockprint": "以明容与堂百回本为底本，参校天都外臣序本、袁无涯本；题「施耐庵、罗贯中著，冀勤校注」",
        "holding": "中华书局/人民文学出版社通行校注本（非古本）",
        "digital_source": "冀勤校注本页下注（(1)(2)...号注），数字版据公开发行的电子整理本转写",
        "entry_method": "电子整理本转写＋人工核校注号顺序",
        "reliability": "A",
        "reliability_desc": "精校——6741 条页下注（语词、典故、制度、版本异文）已按注号挂回 jiqin 版本正文，覆盖率高；属于现代校注，非古评点",
        "coverage_types": ["页下校注", "异文出校", "语词训释"],
        "limits": "为现代学者校注，非明清评点本；统计时须剥离注号避免影响字数/风格指标（本平台文体计量已自动剥离）",
        "first_added": "2026-05",
        "last_revised": "2026-10-27",
    },
    "yannanshang": {
        "blockprint": "清光绪三十四年（1908）燕南尚生著《新评水浒传》（《新评水浒》，系晚清维新派评点）",
        "holding": "首都图书馆、上海图书馆藏本；收入马蹄疾、朱一玄《水浒传资料汇编》",
        "digital_source": "据《水浒传资料汇编》与近代文论选本辑录卷首自序、总评、读法",
        "entry_method": "二次文献辑录",
        "reliability": "D",
        "reliability_desc": "仅存序跋总评——晚清维新派视角，重思想评论，无逐回眉夹批；目前录 13 条代表性总评与读法",
        "coverage_types": ["自序", "读法", "总评"],
        "limits": "无逐回批；条目数少，仅作评点接受史补充样本",
        "first_added": "2026-06",
        "last_revised": "2026-10-27",
    },
}

def _flatten_strings(x, out=None):
    """递归统计所有非空字符串条目（每条视作一个注释单元）。
    jinpi 结构特殊走 count_jinpi；其余以字典/列表遍历估算。"""
    if out is None: out = [0]
    if isinstance(x, str):
        if x.strip(): out[0] += 1
    elif isinstance(x, list):
        for v in x: _flatten_strings(v, out)
    elif isinstance(x, dict):
        # jiqin 形态：{ch:{note_id: note_text}}，所有数字键下的字符串都算注文
        for k, v in x.items():
            if isinstance(k, str) and k.isdigit() and isinstance(v, dict):
                for nv in v.values():
                    if isinstance(nv, str) and nv.strip(): out[0] += 1
            else:
                _flatten_strings(v, out)
    return out[0]

def count_jinpi(path):
    d = json.load(open(path, encoding="utf-8"))
    stats = {}
    total_preface = 0
    total_inline = 0
    chapters = set()
    for vid, chs in d.items():
        for ch_num, payload in chs.items():
            chapters.add(int(ch_num))
            if payload.get("preface"):
                total_preface += 1
            total_inline += int(payload.get("inline_count") or 0)
    return {
        "total_preface": total_preface,
        "total_inline": total_inline,
        "total": total_preface + total_inline,
        "chapter_count": len(chapters),
        "chapter_range": [min(chapters), max(chapters)] if chapters else [],
    }

def count_generic(path):
    """通用：对 chengzhu（volumes/items）/ yuxiangdou（volumes）/ yannanshang（pian/xu/huowen/shiming/chapters）/
       lizhuo/yuanwy/zhongbo/wangping（chapters）/ jiqin（{ch:{nid: text}}）"""
    d = json.load(open(path, encoding="utf-8"))
    # 排除元信息键
    SKIP = {"id","name","name_en","dynasty","color","description","source","era","work","school",
            "core_view","desc","influence","blockprint","digital_source","holding","coverage","bian",
            "range","system","date","status","note","file","cls","kind","chipCls","tag","who","okVer",
            "order","vol","type","chapter","title","full","short","label"}
    def walk(x):
        n = 0
        if isinstance(x, str):
            return 1 if x.strip() else 0
        if isinstance(x, list):
            for v in x: n += walk(v)
            return n
        if isinstance(x, dict):
            for k, v in x.items():
                if k in SKIP: continue
                # 单条注释对象：含 text 字段即算一条
                if isinstance(v, dict) and "text" in v and isinstance(v["text"], str):
                    n += 1
                    continue
                n += walk(v)
            return n
        return 0
    # 计算章节覆盖
    ch_set = set()
    def collect_ch(x):
        if isinstance(x, dict):
            for k,v in x.items():
                if k in ("chapter","num"):
                    m = re.findall(r"\d+", str(v))
                    if m: ch_set.add(int(m[-1]))
                collect_ch(v)
        elif isinstance(x, list):
            for v in x: collect_ch(v)
    collect_ch(d)
    return {
        "total": walk(d),
        "chapter_count": len(ch_set),
        "chapter_range": [min(ch_set), max(ch_set)] if ch_set else [],
    }

def main():
    reg = json.load(open(DATA / "registry.json", encoding="utf-8"))
    out = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "schema_version": 1,
           "reliability_legend": {
               "A": "精校：人工核校，可直接引用",
               "B": "机器整理待校：原刻本/OCR底本已就位，需二校",
               "C": "二次文献转引：据通行整理本过录，页码非原刻",
               "D": "仅存序跋总评：代表性文本，不覆盖逐回",
           },
           "items": []}

    for c in reg.get("commentaries", []):
        cid = c["id"]
        fpath = VERS / c["file"]
        counts = {"exists": fpath.exists()}
        if fpath.exists():
            if cid == "jinpi":
                counts.update(count_jinpi(fpath))
            elif cid == "jiqin":
                # jiqin: {ch_str:{note_id:note_text}}
                d = json.load(open(fpath, encoding="utf-8"))
                total = 0; chs = set()
                for k,v in d.items():
                    if isinstance(k,str) and k.isdigit() and isinstance(v,dict):
                        chs.add(int(k))
                        total += sum(1 for nv in v.values() if isinstance(nv,str) and nv.strip())
                counts.update({"total": total, "chapter_count": len(chs),
                               "chapter_range":[min(chs),max(chs)] if chs else []})
            else:
                counts.update(count_generic(fpath))
        prov = PROVENANCE.get(cid, {})
        out["items"].append({
            "id": cid,
            "tag": c["tag"],
            "who": c["who"],
            "color": c.get("color"),
            "okVer": c.get("okVer", []),
            "note": c.get("note", ""),
            "counts": counts,
            "provenance": prov,
        })

    (DATA / "commentaries_meta.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    # 简短汇报
    print("commentaries_meta.json written.")
    total = 0
    for it in out["items"]:
        cnt = it["counts"]
        t = cnt.get("total",0) or 0
        total += t
        print(f"  {it['tag']:4s}  {it['who']:8s}  等级={it['provenance'].get('reliability','?')}  "
              f"条数≈{t}  回={cnt.get('chapter_range','-')}")
    print(f"  合计 ≈ {total}（检索页展示 8229 条；金批夹批条数已以 inline_count 计，冀注按注条数计）")

if __name__ == "__main__":
    main()
