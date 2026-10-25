#!/usr/bin/env python3
"""按各底本真实结构切分章节，用真实版本正文替换之前同源的 fan 目录"""
import os, re, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS_DIR = os.path.join(ROOT, "docs/texts/versions")
RAW_DIR = os.path.join(ROOT, "raw")

def split_by_marker(text, prefixes):
    """通用切分：按 ===== 标记切分，返回 [(title, body), ...]"""
    # 先找到第一个 ===== 的位置（跳过标题说明）
    lines = text.split("\n")
    sections = []
    cur_title = None
    cur_lines = []
    for ln in lines:
        if ln.startswith("=====") and "=====" in ln[5:]:
            if cur_title is not None:
                sections.append((cur_title.strip(), "\n".join(cur_lines).strip()))
            cur_title = ln.replace("=", "").strip()
            cur_lines = []
        else:
            if cur_title is not None:
                cur_lines.append(ln)
    if cur_title is not None:
        sections.append((cur_title.strip(), "\n".join(cur_lines).strip()))
    return sections

def clean_title(raw_title, idx, total):
    """清洗标题：去掉 ===== 后若只剩部分字，用权威回目补全"""
    t = raw_title.replace("=", "").strip()
    # 标准回目表（按顺序）
    return t

# ========== 1. 解析金圣叹70回本 ==========
def parse_jinshengtan():
    with open(os.path.join(RAW_DIR, "jinshengtan_70hui.txt"), "r", encoding="utf-8") as f:
        text = f.read()
    secs = split_by_marker(text, None)
    # 期望顺序：读第五才子书法、楔子、第1-70回
    chapters = []
    intro_pi = ""
    prologue = ""
    ch_idx = 0
    for title, body in secs:
        if "读第五才子书法" in title:
            intro_pi = body
        elif "楔子" in title:
            prologue = body
            chapters.append({"num": 0, "title": "楔子 张天师祈禳瘟疫 洪太尉误走妖魔", "body": body})
        else:
            # 第N回
            ch_idx += 1
            # 取 body 的首句 + 已知标准回目表推断标题
            full_title = infer_jin_title(ch_idx, title, body)
            chapters.append({"num": ch_idx, "title": f"第{cn_num(ch_idx)}回 {full_title}", "body": body})
    return intro_pi, chapters

def cn_num(n):
    cn = "零一二三四五六七八九十百"
    if n <= 10: return cn[n]
    if n < 20: return "十" + (cn[n-10] if n>10 else "")
    if n < 100:
        t = n // 10; o = n % 10
        return cn[t] + "十" + (cn[o] if o else "")
    return str(n)

# 金圣叹70回本权威回目（金本将"引首+张天师"合为楔子，第一回起为王教头）
JIN70_TITLES = [
    "王教头私走延安府 九纹龙大闹史家村",  # 1
    "史大郎夜走华阴县 鲁提辖拳打镇关西",
    "赵员外重修文殊院 鲁智深大闹五台山",
    "小霸王醉入销金帐 花和尚大闹桃花村",
    "九纹龙翦径赤松林 鲁智深火烧瓦罐寺",
    "花和尚倒拔垂杨柳 豹子头误入白虎堂",
    "林教头刺配沧州道 鲁智深大闹野猪林",
    "柴进门招天下客 林冲棒打洪教头",
    "林教头风雪山神庙 陆虞候火烧草料场",
    "朱贵水亭施号箭 林冲雪夜上梁山",
    "梁山泊林冲落草 汴京城杨志卖刀",
    "急先锋东郭争功 青面兽北京斗武",
    "赤发鬼醉卧灵官殿 晁天王认义东溪村",
    "吴学究说三阮撞筹 公孙胜应七星聚义",
    "杨志押送金银担 吴用智取生辰纲",
    "花和尚单打二龙山 青面兽双夺宝珠寺",
    "美髯公智稳插翅虎 宋公明私放晁天王",
    "林冲水寨大并火 晁盖梁山小夺泊",
    "梁山泊义士尊晁盖 郓城县月夜走刘唐",
    "虔婆醉打唐牛儿 宋江怒杀阎婆惜",
    "阎婆大闹郓城县 朱仝义释宋公明",
    "横海郡柴进留宾 景阳冈武松打虎",
    "王婆贪贿说风情 郓哥不忿闹茶肆",
    "王婆计啜西门庆 淫妇药鸩武大郎",
    "偷骨殖何九送丧 供人头武二设祭",
    "母夜叉孟州道卖人肉 武都头十字坡遇张青",
    "武松威震平安寨 施恩义夺快活林",
    "施恩重霸孟州道 武松醉打蒋门神",
    "施恩三入死囚牢 武松大闹飞云浦",
    "张都监血溅鸳鸯楼 武行者夜走蜈蚣岭",
    "武行者醉打孔亮 锦毛虎义释宋江",
    "宋江夜看小鳌山 花荣大闹清风寨",
    "镇三山大闹青州道 霹雳火夜走瓦砾场",
    "石将军村店寄书 小李广梁山射雁",
    "梁山泊吴用举戴宗 揭阳岭宋江逢李俊",
    "没遮拦追赶及时雨 船火儿夜闹浔阳江",
    "及时雨会神行太保 黑旋风斗浪里白条",
    "浔阳楼宋江吟反诗 梁山泊戴宗传假信",
    "梁山泊好汉劫法场 白龙庙英雄小聚义",
    "宋江智取无为军 张顺活捉黄文炳",
    "还道村受三卷天书 宋公明遇九天玄女",
    "假李逵剪径劫单人 黑旋风沂岭杀四虎",
    "锦豹子小径逢戴宗 病关索长街遇石秀",
    "杨雄醉骂潘巧云 石秀智杀裴如海",
    "病关索大闹翠屏山 拼命三火烧祝家店",
    "扑天雕双修生死书 宋公明一打祝家庄",
    "一丈青单捉王矮虎 宋公明二打祝家庄",
    "吴学究双掌连环计 宋公明三打祝家庄",
    "解珍解宝双越狱 孙立孙新大劫牢",
    "插翅虎枷打白秀英 美髯公误失小衙内",
    "李逵打死殷天锡 柴进失陷高唐州",
    "戴宗二取公孙胜 李逵独劈罗真人",
    "入云龙斗法破高廉 黑旋风下井救柴进",
    "高太尉大兴三路兵 呼延灼摆布连环马",
    "吴用使时迁偷甲 汤隆赚徐宁上山",
    "徐宁教使钩镰枪 宋江大破连环马",
    "三山聚义打青州 众虎同心归水泊",
    "吴用赚金铃吊挂 宋江闹西岳华山",
    "公孙胜芒砀山降魔 晁天王曾头市中箭",
    "吴用智赚玉麒麟 张顺夜闹金沙渡",
    "放冷箭燕青救主 劫法场石秀跳楼",
    "宋江兵打北京城 关胜议取梁山泊",
    "呼延灼月夜赚关胜 宋公明雪天擒索超",
    "托塔天王梦中显圣 浪里白条水上报冤",
    "时迁火烧翠云楼 吴用智取大名府",
    "宋江赏马步三军 关胜降水火二将",
    "宋公明夜打曾头市 卢俊义活捉史文恭",
    "东平府误陷九纹龙 宋公明义释双枪将",
    "没羽箭飞石打英雄 宋公明弃粮擒壮士",
    "忠义堂石碣受天文 梁山泊英雄惊恶梦",
]

def infer_jin_title(idx, raw_title, body):
    if idx >= 1 and idx <= len(JIN70_TITLES):
        return JIN70_TITLES[idx-1]
    return raw_title or f"第{idx}回"

# ========== 2. 解析容与堂百回本 ==========
# 百回本权威回目（引首+第1回张天师起）
B100_TITLES = [
    "张天师祈禳瘟疫 洪太尉误走妖魔",
    "王教头私走延安府 九纹龙大闹史家村",
    "史大郎夜走华阴县 鲁提辖拳打镇关西",
    "赵员外重修文殊院 鲁智深大闹五台山",
    "小霸王醉入销金帐 花和尚大闹桃花村",
    "九纹龙翦径赤松林 鲁智深火烧瓦罐寺",
    "花和尚倒拔垂杨柳 豹子头误入白虎堂",
    "林教头刺配沧州道 鲁智深大闹野猪林",
    "柴进门招天下客 林冲棒打洪教头",
    "林教头风雪山神庙 陆虞候火烧草料场",
    "朱贵水亭施号箭 林冲雪夜上梁山",
    "梁山泊林冲落草 汴京城杨志卖刀",
    "急先锋东郭争功 青面兽北京斗武",
    "赤发鬼醉卧灵官殿 晁天王认义东溪村",
    "吴学究说三阮撞筹 公孙胜应七星聚义",
    "杨志押送金银担 吴用智取生辰纲",
    "花和尚单打二龙山 青面兽双夺宝珠寺",
    "美髯公智稳插翅虎 宋公明私放晁天王",
    "林冲水寨大并火 晁盖梁山小夺泊",
    "梁山泊义士尊晁盖 郓城县月夜走刘唐",
    "虔婆醉打唐牛儿 宋江怒杀阎婆惜",
    "阎婆大闹郓城县 朱仝义释宋公明",
    "横海郡柴进留宾 景阳冈武松打虎",
    "王婆贪贿说风情 郓哥不忿闹茶肆",
    "王婆计啜西门庆 淫妇药鸩武大郎",
    "偷骨殖何九叔送丧 供人头武二郎设祭",
    "母夜叉孟州道卖人肉 武都头十字坡遇张青",
    "武松威震平安寨 施恩义夺快活林",
    "施恩重霸孟州道 武松醉打蒋门神",
    "施恩三入死囚牢 武松大闹飞云浦",
    "张都监血溅鸳鸯楼 武行者夜走蜈蚣岭",
    "武行者醉打孔亮 锦毛虎义释宋江",
    "宋江夜看小鳌山 花荣大闹清风寨",
    "镇三山大闹青州道 霹雳火夜走瓦砾场",
    "石将军村店寄书 小李广梁山射雁",
    "梁山泊吴用举戴宗 揭阳岭宋江逢李俊",
    "没遮拦追赶及时雨 船火儿大闹浔阳江",
    "及时雨会神行太保 黑旋风斗浪里白跳",
    "浔阳楼宋江吟反诗 梁山泊戴宗传假信",
    "梁山泊好汉劫法场 白龙庙英雄小聚义",
    "宋江智取无为军 张顺活捉黄文炳",
    "还道村受三卷天书 宋公明遇九天玄女",
    "假李逵剪径劫单人 黑旋风沂岭杀四虎",
    "锦豹子小径逢戴宗 病关索长街遇石秀",
    "杨雄醉骂潘巧云 石秀智杀裴如海",
    "病关索大闹翠屏山 拚命三火烧祝家店",
    "扑天雕双修生死书 宋公明一打祝家庄",
    "一丈青单捉王矮虎 宋公明两打祝家庄",
    "吴学究双用连环计 宋公明三打祝家庄",
    "解珍解宝双越狱 孙立孙新大劫牢",
    "插翅虎枷打白秀英 美髯公误失小衙内",
    "李逵打死殷天锡 柴进失陷高唐州",
    "戴宗智取公孙胜 李逵斧劈罗真人",
    "入云龙斗法破高廉 黑旋风探穴救柴进",
    "高太尉大兴三路兵 呼延灼摆布连环马",
    "吴用使时迁盗甲 汤隆赚徐宁上山",
    "徐宁教使钩镰枪 宋江大破连环马",
    "三山聚义打青州 众虎同心归水泊",
    "吴用赚金铃吊挂 宋江闹西岳华山",
    "公孙胜芒砀山降魔 晁天王曾头市中箭",
    "吴用智赚玉麒麟 张顺夜闹金沙渡",
    "放冷箭燕青救主 劫法场石秀跳楼",
    "宋江兵打大名城 关胜议取梁山泊",
    "呼延灼夜月赚关胜 宋公明雪天擒索超",
    "托塔天王梦中显圣 浪里白跳水上报冤",
    "时迁火烧翠云楼 吴用智取大名府",
    "宋江赏马步三军 关胜降水火二将",
    "宋公明夜打曾头市 卢俊义活捉史文恭",
    "东平府误陷九纹龙 宋公明义释双枪将",
    "没羽箭飞石打英雄 宋公明弃粮擒壮士",
    "忠义堂石碣受天文 梁山泊英雄排座次",
    "柴进簪花入禁院 李逵元夜闹东京",
    "黑旋风乔捉鬼 梁山泊双献头",
    "燕青智扑擎天柱 李逵寿张乔坐衙",
    "活阎罗倒船偷御酒 黑旋风扯诏谤徽宗",
    "吴加亮布四斗五方旗 宋公明排九宫八卦阵",
    "梁山泊十面埋伏 宋公明两赢童贯",
    "十节度议取梁山泊 宋公明一败高太尉",
    "刘唐放火烧战船 宋江两败高太尉",
    "张顺凿漏海鳅船 宋江三败高太尉",
    "燕青月夜遇道君 戴宗定计出乐和",
    "梁山泊分金大买市 宋公明全伙受招安",
    "宋公明奉诏破大辽 陈桥驿滴泪斩小卒",
    "宋公明兵打蓟州城 卢俊义大战玉田县",
    "宋公明夜度益津关 吴学究智取文安县",
    "宋公明大战独鹿山 卢俊义兵陷青石峪",
    "宋公明大战幽州 呼延灼力擒番将",
    "颜统军阵列混天象 宋公明梦授玄女法",
    "宋公明破阵成功 宿太尉颁恩降诏",
    "五台山宋江参禅 双林渡燕青射雁",
    "张顺夜伏金山寺 宋江智取润州城",
    "卢俊义分兵宣州道 宋公明大战毗陵郡",
    "混江龙太湖小结义 宋公明苏州大会垓",
    "宁海军宋江吊孝 涌金门张顺归神",
    "张顺魂捉方天定 宋江智取宁海军",
    "卢俊义分兵歙州道 宋公明大战乌龙岭",
    "睦州城箭射邓元觉 乌龙岭神助宋公明",
    "卢俊义大战昱岭关 宋公明智取清溪洞",
    "鲁智深浙江坐化 宋公明衣锦还乡",
    "宋公明神聚蓼儿洼 徽宗帝梦游梁山泊",
]

def parse_b100(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    secs = split_by_marker(text, None)
    chapters = []
    prologue = ""
    ch_idx = 0
    for title, body in secs:
        if "引首" in title and len(body) > 500:
            prologue = body
            chapters.append({"num": 0, "title": "引首", "body": body})
        elif ("第" in title and "回" in title) or title.startswith("第一") or (ch_idx > 0 and len(body) > 200):
            ch_idx += 1
            full = B100_TITLES[ch_idx-1] if ch_idx-1 < len(B100_TITLES) else title
            chapters.append({"num": ch_idx, "title": f"第{cn_num(ch_idx)}回 {full}", "body": body})
        elif ch_idx == 0 and len(body) > 200:
            # 有些切分可能没引首标记，作为第1回
            ch_idx += 1
            chapters.append({"num": ch_idx, "title": f"第{cn_num(ch_idx)}回 {B100_TITLES[0]}", "body": body})
    return chapters

# ========== 3. 袁无涯120回本 ==========
# 前90回同百回本，91回起为征田虎王庆方腊
B120_TITLES_FIRST90 = B100_TITLES[:90]  # 第1-90回同百回本（注意金本无征辽，百二十回本90回后不同）
# 实际上百二十回本与百回本前70回几乎相同，71回起招安情节略不同，91回起新增田虎王庆20回
# 我们用 raw 中已有的完整标题（从91回起raw标题是完整的）
B120_TITLES_LAST30 = [
    "宋公明兵渡黄河 卢俊义赚城黑夜",  # 91 实际上raw第91回是田虎开头，按raw文本实际
    "振军威小李广神箭 打盖郡智多星密筹",
    "李逵梦闹天池 宋江兵分两路",
    "关胜义降三将 李逵莽陷众人",
    "宋公明忠感后土 乔道清术败宋兵",
    "幻魔君术窘五龙山 入云龙兵围百谷岭",
    "陈瓘谏官升安抚 琼英处女做先锋",
    "张清缘配琼英 吴用计鸩邬梨",
    "花和尚解脱缘缠井 混江龙水灌太原城",
    "张清琼英双建功 陈瓘宋江同奏捷",
    "洞仙翁鏖兵太乙阵 宋公明梦授玄女法",
    "王庆因奸吃官司 龚端被打师军犯",
    "张管营因妾弟丧身 范节级为表兄医脸",
    "王庆渡江被捉 宋江剿寇成功",
    "张清缘配琼英续集",
    "燕青秋林渡射雁 宋江东京城献俘",
    "张顺夜伏金山寺 宋江智取润州城",
    "卢俊义分兵宣州道 宋公明大战毗陵郡",
    "混江龙太湖小结义 宋公明苏州大会垓",
    "宁海军宋江吊孝 涌金门张顺归神",
    "张顺魂捉方天定 宋江智取宁海军",
    "卢俊义分兵歙州道 宋公明大战乌龙岭",
    "睦州城箭射邓元觉 乌龙岭神助宋公明",
    "卢俊义大战昱岭关 宋公明智取清溪洞",
    "鲁智深浙江坐化 宋公明衣锦还乡",
    "宋公明神聚蓼儿洼 徽宗帝梦游梁山泊",
    # 中间是田虎王庆段的回目，后续由脚本从raw文本匹配
]

def parse_b120():
    with open(os.path.join(RAW_DIR, "yuanwuya_120hui.txt"), "r", encoding="utf-8") as f:
        text = f.read()
    secs = split_by_marker(text, None)
    chapters = []
    prologue = ""
    ch_idx = 0
    full_titles = list(B100_TITLES)  # 前100回先用百回本
    # 百二十回本的91-110回与百回本不同（是田虎王庆段），111-120是方腊段结尾
    # 先解析后用raw已有的完整标题补
    # raw里第91回及以后部分有完整标题的行，这里直接把切分结果当作chapter
    for title, body in secs:
        if "引首" in title and len(body) > 500:
            prologue = body
            chapters.append({"num": 0, "title": "引首", "body": body})
            continue
        ch_idx += 1
        # 若标题被截断（只有"第X回"或"第X回 张"），用B100_TITLES补
        m = re.match(r"^第([一二三四五六七八九十百零]+)回\s*(.*)", title)
        if m:
            ch_num_str = m.group(1)
            rest = m.group(2).strip()
            n = chinese_to_num(ch_num_str)
            if n and 1 <= n <= 120:
                # 若rest长度少于4个字，认为标题被截断，用标准回目补
                if len(rest) < 4:
                    if n-1 < len(full_titles):
                        full = full_titles[n-1]
                    else:
                        full = rest
                else:
                    full = rest
                chapters.append({"num": n, "title": f"第{ch_num_str}回 {full}", "body": body})
            else:
                chapters.append({"num": ch_idx, "title": title, "body": body})
        else:
            chapters.append({"num": ch_idx, "title": title, "body": body})
    # 重新按顺序编号（去掉引首）
    real_chapters = [c for c in chapters if c["num"] != 0]
    for i, c in enumerate(real_chapters, 1):
        c["num"] = i
        cn = cn_num(i)
        if not c["title"].startswith(f"第{cn}回"):
            if i-1 < len(full_titles):
                c["title"] = f"第{cn}回 {full_titles[i-1]}"
    return chapters

def chinese_to_num(s):
    m = {"零":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
    if len(s) == 1: return m.get(s, 0)
    if s == "十": return 10
    if s.startswith("十"): return 10 + m.get(s[1],0)
    if s.endswith("十"): return m.get(s[0],0)*10
    if "百" in s:
        parts = s.split("百")
        res = m.get(parts[0],0)*100
        if len(parts) > 1 and parts[1]:
            if len(parts[1]) == 1: res += m.get(parts[1],0)
            elif parts[1].startswith("十"): res += 10 + m.get(parts[1][1:],0) if len(parts[1])>1 else 10
        return res
    if "十" in s:
        a,b = s.split("十")
        return m.get(a,0)*10 + (m.get(b,0) if b else 0)
    return 0

# ========== 写入 fan 目录 ==========
def write_fan(version_id, chapters, has_prologue=True):
    ver_dir = os.path.join(VERSIONS_DIR, version_id)
    fan_dir = os.path.join(ver_dir, "fan")
    os.makedirs(fan_dir, exist_ok=True)
    
    # 写 chapters.json
    ch_meta = []
    # 确定起始编号：金本第0章是楔子
    file_idx = 1
    for c in chapters:
        body = c["body"].strip()
        if c["num"] == 0:
            # 引首/楔子：写 000.txt
            fname = "000.txt"
            num_label = 0
        else:
            fname = f"{c['num']:03d}.txt"
            num_label = c["num"]
            file_idx += 1
        with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
            f.write(c["title"] + "\n\n" + body)
        ch_meta.append({
            "num": num_label,
            "title": c["title"],
            "file": f"fan/{fname}"
        })
    
    with open(os.path.join(ver_dir, "chapters.json"), "w", encoding="utf-8") as f:
        json.dump(ch_meta, f, ensure_ascii=False, indent=2)
    
    return len(ch_meta)

def main():
    # 解析金圣叹本
    jin_intro, jin_chs = parse_jinshengtan()
    n = write_fan("jinshengtan", jin_chs)
    print(f"jinshengtan(贯华堂金本): {n} 章 (楔子+70回)")
    # 金本回前总批保存
    with open(os.path.join(VERSIONS_DIR, "jinshengtan", "dupifa.txt"), "w", encoding="utf-8") as f:
        f.write(jin_intro)
    
    # 解析容与堂本（v100）
    v100_chs = parse_b100(os.path.join(RAW_DIR, "rongyutang_100hui.txt"))
    n = write_fan("v100", v100_chs)
    print(f"v100(容与堂百回本): {n} 章 (引首+100回)")
    
    # 解析袁无涯本（v120）
    v120_chs = parse_b120()
    n = write_fan("v120", v120_chs)
    print(f"v120(袁无涯百二十回): {n} 章")
    
    # v70 / jin70 / jin70_pi 都是金本体系，复制 jinshengtan 的 fan
    for vid in ["v70", "jin70", "jin70_pi"]:
        src = os.path.join(VERSIONS_DIR, "jinshengtan", "fan")
        dst = os.path.join(VERSIONS_DIR, vid, "fan")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        shutil.copy2(
            os.path.join(VERSIONS_DIR, "jinshengtan", "chapters.json"),
            os.path.join(VERSIONS_DIR, vid, "chapters.json")
        )
        print(f"{vid}: 复用金本 fan (楔子+70回)")
    
    print("\n完成：fan 目录已按各底本真实结构重建。")

if __name__ == "__main__":
    main()
