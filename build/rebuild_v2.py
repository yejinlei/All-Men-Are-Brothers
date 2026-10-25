#!/usr/bin/env python3
"""按各底本真实结构切分章节 — v2（稳健版）"""
import os, re, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS_DIR = os.path.join(ROOT, "docs/texts/versions")
RAW_DIR = os.path.join(ROOT, "raw")

# ========== 权威回目表 ==========

# 金圣叹70回本（贯华堂本）：楔子 + 第1-70回（金本惊恶梦结尾）
JIN70_TITLES = [
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
    "宋江兵打北京城 关胜议取梁山泊",
    "呼延灼夜月赚关胜 宋公明雪天擒索超",
    "托塔天王梦中显圣 浪里白跳水上报冤",
    "时迁火烧翠云楼 吴用智取大名府",
    "宋江赏马步三军 关胜降水火二将",
    "宋公明夜打曾头市 卢俊义活捉史文恭",
    "东平府误陷九纹龙 宋公明义释双枪将",
    "没羽箭飞石打英雄 宋公明弃粮擒壮士",
    "忠义堂石碣受天文 梁山泊英雄惊恶梦",
]

# 容与堂百回本权威回目（无田虎王庆，招安后征辽+征方腊）
RONG100_TITLES = [
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
    "宋江兵打北京城 关胜议取梁山泊",
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
    "燕青月夜遇道君 戴宗定计赚萧让",
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

# 袁无涯百二十回本权威回目（第91回起为田虎王庆段，与百回本不同）
# 前90回同容与堂百回本（71回招安段用词略异，但回目一致）
YUAN120_TITLES = RONG100_TITLES[:90] + [
    # 91-100 征田虎
    "宋公明兵渡黄河 卢俊义赚城黑夜",
    "振军威小李广神箭 打盖郡智多星密筹",
    "李逵梦闹天池 宋江兵分两路",
    "关胜义降三将 李逵莽陷众人",
    "宋公明忠感后土 乔道清术败宋兵",
    "幻魔君术窘五龙山 入云龙兵围百谷岭",
    "陈瓘谏官升安抚 琼英处女做先锋",
    "张清缘配琼英 吴用计鸩邬梨",
    "花和尚解脱缘缠井 混江龙水灌太原城",
    "张清琼英双建功 陈瓘宋江同奏捷",
    # 101-110 征王庆
    "谋坟地阴险产逆 蹈春阳妖艳生奸",
    "王庆因奸吃官司 龚端被打师军犯",
    "张管营因妾弟丧身 范节级为表兄医脸",
    "段家庄重招新女婿 房山寨双并旧强人",
    "宋公明避暑疗军兵 乔道清回风烧贼寇",
    "书生谈笑却强敌 水军汨没破坚城",
    "宋江大胜纪山军 朱武打破六花阵",
    "乔道清兴雾取城 小旋风藏炮击贼",
    "王庆渡江被捉 宋江剿寇成功",
    "燕青秋林渡射雁 宋江东京城献俘",
    # 111-120 征方腊（与百回本91-100回一致）
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

def cn_num(n):
    if n == 0: return ""
    digits = "零一二三四五六七八九"
    if n < 10: return digits[n]
    if n == 10: return "十"
    if n < 20: return "十" + digits[n-10]
    if n < 100:
        t = n // 10; o = n % 10
        return digits[t] + "十" + (digits[o] if o else "")
    if n == 100: return "一百"
    if n < 110: return "一百零" + digits[n-100]
    return str(n)

def split_sections(text):
    """按 ===== 行切分，返回 [(section_header_line, body_text)]"""
    lines = text.split("\n")
    sections = []
    cur_header = None
    cur_lines = []
    for ln in lines:
        if ln.startswith("=====") and ln.endswith("====="):
            if cur_header is not None:
                sections.append((cur_header, "\n".join(cur_lines).strip()))
            cur_header = ln
            cur_lines = []
        else:
            if cur_header is not None:
                cur_lines.append(ln)
    if cur_header is not None:
        sections.append((cur_header, "\n".join(cur_lines).strip()))
    return sections

def extract_prologue_and_chapters(raw_text, has_xuzi=False):
    """
    从raw文本提取：
    - prologue（引首或楔子）
    - N章正文
    has_xuzi=True 表示是金本结构（第一个section=楔子，后续70章）
    """
    secs = split_sections(raw_text)
    # secs[0] 是文件开头的说明（"水浒传（百回本·容与堂本..."），跳过
    # 从第一个有效章节开始
    start = 0
    for i, (h, b) in enumerate(secs):
        if "===== 引首 =====" in h or "===== 楔子" in h or "第" in h or "读第五才子书法" in h:
            start = i
            break
    
    # 对金本：找"读第五才子书法"和"楔子"
    prologue = ""
    intro_pi = ""
    chapters_body = []
    
    body_start = start
    if has_xuzi:
        # 金本
        for i in range(start, len(secs)):
            h, b = secs[i]
            if "读第五才子书法" in h:
                intro_pi = b
            elif "楔子" in h:
                prologue = b
                chapters_body = secs[i+1:]
                break
    else:
        # 百回/百二十回本：引首后是第1-N回
        for i in range(start, len(secs)):
            h, b = secs[i]
            if "引首" in h:
                prologue = b
                chapters_body = secs[i+1:]
                break
            else:
                # 无引首标记，直接从i开始
                chapters_body = secs[i:]
                break
    
    return intro_pi, prologue, chapters_body

def write_version(version_id, title_prefix, prologue_title, chapters_bodies, titles_table, intro_pi=""):
    """写入某个版本的 fan 目录"""
    ver_dir = os.path.join(VERSIONS_DIR, version_id)
    fan_dir = os.path.join(ver_dir, "fan")
    
    # 清空旧 fan 目录
    if os.path.exists(fan_dir):
        shutil.rmtree(fan_dir)
    os.makedirs(fan_dir, exist_ok=True)
    
    ch_meta = []
    
    # 写引首/楔子为 000.txt
    if prologue_title and chapters_bodies is not None:
        with open(os.path.join(fan_dir, "000.txt"), "w", encoding="utf-8") as f:
            f.write(prologue_title + "\n\n" + (chapters_bodies if isinstance(chapters_bodies, str) else ""))
    
    # 把chapters_bodies整理为list
    if isinstance(chapters_bodies, list):
        body_list = [b for (_, b) in chapters_bodies]
    else:
        body_list = []
    
    # 核心：正文section数可能和回目数不等（因为raw里有缺失=====标记或重复）
    # 策略：若body数 == titles数 → 一一对应
    #       若body数 > titles数 → 把多余合并到最后一章
    #       若body数 < titles数 → 说明marker丢失，需按内容切分，先警告
    expected = len(titles_table)
    actual = len(body_list)
    
    if actual == expected:
        # 完美匹配
        for i in range(expected):
            fname = f"{i+1:03d}.txt"
            title = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + body_list[i])
            ch_meta.append({"num": i+1, "title": title, "file": f"fan/{fname}"})
    elif actual > expected:
        # 多余的：把实际第expected个起合并到最后一章
        for i in range(expected-1):
            fname = f"{i+1:03d}.txt"
            title = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + body_list[i])
            ch_meta.append({"num": i+1, "title": title, "file": f"fan/{fname}"})
        # 最后一章：合并
        merged_body = "\n\n".join(body_list[expected-1:])
        fname = f"{expected:03d}.txt"
        title = f"第{cn_num(expected)}回 {titles_table[-1]}"
        with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
            f.write(title + "\n\n" + merged_body)
        ch_meta.append({"num": expected, "title": title, "file": f"fan/{fname}"})
        print(f"  [警告] {version_id}: raw有{actual}段，回目表{expected}条，合并到第{expected}回")
    else:
        # actual < expected：前actual章按序，剩下的标为"未详"（raw下载不全）
        print(f"  [警告] {version_id}: raw仅{actual}段，回目表{expected}条，后续回目正文缺失")
        for i in range(actual):
            fname = f"{i+1:03d}.txt"
            title = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + body_list[i])
            ch_meta.append({"num": i+1, "title": title, "file": f"fan/{fname}"})
        for i in range(actual, expected):
            fname = f"{i+1:03d}.txt"
            title = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fname), "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + "【正文暂缺，待补】")
            ch_meta.append({"num": i+1, "title": title, "file": f"fan/{fname}"})
    
    # 写 chapters.json
    with open(os.path.join(ver_dir, "chapters.json"), "w", encoding="utf-8") as f:
        json.dump(ch_meta, f, ensure_ascii=False, indent=2)
    
    # 写读第五才子书法
    if intro_pi:
        with open(os.path.join(ver_dir, "preface_jin.txt"), "w", encoding="utf-8") as f:
            f.write(intro_pi)
    
    return len(ch_meta)

def parse_and_write(version_id, raw_file, titles_table, is_jin=False):
    with open(raw_file, "r", encoding="utf-8") as f:
        text = f.read()
    intro_pi, prologue, chapters_body = extract_prologue_and_chapters(text, has_xuzi=is_jin)
    
    if is_jin:
        n = write_version(version_id, "金圣叹评本", "楔子 张天师祈禳瘟疫 洪太尉误走妖魔",
                          chapters_body, titles_table, intro_pi=intro_pi,
                          prologue_body=prologue)
    else:
        n = write_version(version_id, "百回本", "引首",
                          chapters_body, titles_table, prologue_body=prologue)
    print(f"✅ {version_id}: {n} 回")
    return n

def write_version_with_prologue(version_id, prologue_title, chapters_bodies_list, titles_table, intro_pi="", prologue_body=""):
    ver_dir = os.path.join(VERSIONS_DIR, version_id)
    fan_dir = os.path.join(ver_dir, "fan")
    if os.path.exists(fan_dir):
        shutil.rmtree(fan_dir)
    os.makedirs(fan_dir, exist_ok=True)
    ch_meta = []
    # 000.txt = 楔子/引首
    if prologue_body:
        with open(os.path.join(fan_dir, "000.txt"), "w", encoding="utf-8") as f:
            f.write(prologue_title + "\n\n" + prologue_body)
    
    body_list = [b for _, b in chapters_bodies_list]
    expected = len(titles_table)
    actual = len(body_list)
    
    if actual >= expected:
        for i in range(expected-1):
            fn = f"{i+1:03d}.txt"
            t = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fn), "w", encoding="utf-8") as f:
                f.write(t + "\n\n" + body_list[i])
            ch_meta.append({"num": i+1, "title": t, "file": f"fan/{fn}"})
        # 最后一章合并多余
        merged = "\n\n".join(body_list[expected-1:actual])
        fn = f"{expected:03d}.txt"
        t = f"第{cn_num(expected)}回 {titles_table[-1]}"
        with open(os.path.join(fan_dir, fn), "w", encoding="utf-8") as f:
            f.write(t + "\n\n" + merged)
        ch_meta.append({"num": expected, "title": t, "file": f"fan/{fn}"})
        if actual > expected:
            print(f"  [合并] {actual-expected} 段合并到最后一章")
    else:
        for i in range(actual):
            fn = f"{i+1:03d}.txt"
            t = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fn), "w", encoding="utf-8") as f:
                f.write(t + "\n\n" + body_list[i])
            ch_meta.append({"num": i+1, "title": t, "file": f"fan/{fn}"})
        for i in range(actual, expected):
            fn = f"{i+1:03d}.txt"
            t = f"第{cn_num(i+1)}回 {titles_table[i]}"
            with open(os.path.join(fan_dir, fn), "w", encoding="utf-8") as f:
                f.write(t + "\n\n【正文待补】")
            ch_meta.append({"num": i+1, "title": t, "file": f"fan/{fn}"})
        print(f"  [警告] 缺{expected-actual}回正文")
    
    # 000 加入meta
    if prologue_body:
        ch_meta.insert(0, {"num": 0, "title": prologue_title, "file": "fan/000.txt"})
    
    with open(os.path.join(ver_dir, "chapters.json"), "w", encoding="utf-8") as f:
        json.dump(ch_meta, f, ensure_ascii=False, indent=2)
    
    if intro_pi:
        with open(os.path.join(ver_dir, "preface_jin.txt"), "w", encoding="utf-8") as f:
            f.write(intro_pi)
    
    return len(ch_meta)

def main():
    # ---- 1. 金圣叹70回本 (贯华堂) ----
    with open(os.path.join(RAW_DIR, "jinshengtan_70hui.txt"), "r", encoding="utf-8") as f:
        jin_text = f.read()
    intro_pi, prologue, chs_body = extract_prologue_and_chapters(jin_text, has_xuzi=True)
    write_version_with_prologue("jinshengtan", "楔子 张天师祈禳瘟疫 洪太尉误走妖魔",
                                chs_body, JIN70_TITLES, intro_pi=intro_pi, prologue_body=prologue)
    print(f"✅ jinshengtan(贯华堂金本): 楔子+{len(JIN70_TITLES)}回")
    
    # ---- 2. 容与堂百回本 (v100) ----
    with open(os.path.join(RAW_DIR, "rongyutang_100hui.txt"), "r", encoding="utf-8") as f:
        rong_text = f.read()
    intro_pi, prologue, chs_body = extract_prologue_and_chapters(rong_text, has_xuzi=False)
    write_version_with_prologue("v100", "引首", chs_body, RONG100_TITLES, prologue_body=prologue)
    print(f"✅ v100(容与堂百回本): 引首+{len(RONG100_TITLES)}回")
    
    # ---- 3. 袁无涯百二十回本 (v120) ----
    with open(os.path.join(RAW_DIR, "yuanwuya_120hui.txt"), "r", encoding="utf-8") as f:
        yuan_text = f.read()
    intro_pi, prologue, chs_body = extract_prologue_and_chapters(yuan_text, has_xuzi=False)
    write_version_with_prologue("v120", "引首", chs_body, YUAN120_TITLES, prologue_body=prologue)
    print(f"✅ v120(袁无涯百二十回本): 引首+{len(YUAN120_TITLES)}回")
    
    # ---- 4. 金本体系的另外三个版本（v70/jin70/jin70_pi）复制 jinshengtan ----
    for vid in ["v70", "jin70", "jin70_pi"]:
        src_fan = os.path.join(VERSIONS_DIR, "jinshengtan", "fan")
        src_ch = os.path.join(VERSIONS_DIR, "jinshengtan", "chapters.json")
        dst_fan = os.path.join(VERSIONS_DIR, vid, "fan")
        dst_ch = os.path.join(VERSIONS_DIR, vid, "chapters.json")
        if os.path.exists(dst_fan): shutil.rmtree(dst_fan)
        shutil.copytree(src_fan, dst_fan)
        shutil.copy2(src_ch, dst_ch)
        print(f"✅ {vid}: 复用贯华堂金本")
    
    print("\n所有版本 fan 目录重建完成。")

if __name__ == "__main__":
    main()
