#!/usr/bin/env python3
"""修复zsk版本：完整切分zhengsikou.txt，处理重复标记"""
import os, json, shutil
from opencc import OpenCC
cc = OpenCC("t2s")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = os.path.join(ROOT, "docs/texts/versions/zsk")
RAW = os.path.join(ROOT, "raw/zhengsikou.txt")

ZSK_TITLES = [
    "梁山泊分金大买市 宋公明全伙受招安","宋公明奉诏破大辽 陈桥驿滴泪斩小卒",
    "宋公明兵打蓟州城 卢俊义大战玉田县","宋公明夜度益津关 吴学究智取文安县",
    "宋公明大战独鹿山 卢俊义兵陷青石峪","宋公明大战幽州 呼延灼力擒番将",
    "颜统军阵列混天象 宋公明梦授玄女法","宋公明破阵成功 宿太尉颁恩降诏",
    "五台山宋江参禅 双林渡燕青射雁","宋公明兵渡黄河 卢俊义赚城黑夜",
    "振军威小李广神箭 打盖郡智多星密筹","李逵梦闹天池 宋江兵分两路",
    "关胜义降三将 李逵莽陷众人","宋公明忠感后土 乔道清术败宋兵",
    "幻魔君术窘五龙山 入云龙兵围百谷岭","陈瓘谏官升安抚 琼英处女做先锋",
    "张清缘配琼英 吴用计鸩邬梨","花和尚解脱缘缠井 混江龙水灌太原城",
    "张清琼英双建功 陈瓘宋江同奏捷","谋坟地阴险产逆 蹈春阳妖艳生奸",
    "王庆因奸吃官司 龚端被打师军犯","张管营因妾弟丧身 范节级为表兄医脸",
    "段家庄重招新女婿 房山寨双并旧强人","宋公明避暑疗军兵 乔道清回风烧贼寇",
    "书生谈笑却强敌 水军汨没破坚城","宋江大胜纪山军 朱武打破六花阵",
    "乔道清兴雾取城 小旋风藏炮击贼","王庆渡江被捉 宋江剿寇成功",
    "燕青秋林渡射雁 宋江东京城献俘","张顺夜伏金山寺 宋江智取润州城",
    "卢俊义分兵宣州道 宋公明大战毗陵郡","混江龙太湖小结义 宋公明苏州大会垓",
    "宁海军宋江吊孝 涌金门张顺归神","张顺魂捉方天定 宋江智取宁海军",
    "卢俊义分兵歙州道 宋公明大战乌龙岭","睦州城箭射邓元觉 乌龙岭神助宋公明",
    "卢俊义大战昱岭关 宋公明智取清溪洞",
]

def cn_num(n):
    d = "零一二三四五六七八九"
    if n < 10: return d[n]
    if n == 10: return "十"
    if n < 20: return "十" + (d[n-10] if n>10 else "")
    if n < 100:
        t, o = n//10, n%10
        return d[t] + "十" + (d[o] if o else "")
    if n == 100: return "一百"
    if n < 110: return "一百零" + d[n-100]
    if n == 110: return "一百一十"
    if n < 120: return "一百一" + d[n-110]
    return str(n)

with open(RAW, "r", encoding="utf-8") as f:
    text = f.read()
lines = text.split("\n")
secs = []
cur_h, cur_l = None, []
for ln in lines:
    if ln.startswith("===== ") and ln.endswith(" ====="):
        if cur_h is not None:
            secs.append((cur_h, "\n".join(cur_l).strip()))
        cur_h, cur_l = ln, []
    elif cur_h is not None:
        cur_l.append(ln)

# 找"第八十二回"开始
start = 0
for i, (h, _) in enumerate(secs):
    if "第八十二回" in h:
        start = i
        break
body_secs = secs[start:]
print(f"从第82回起共 {len(body_secs)} 个段")

# raw 里第110回标记重复了多次，但正文是110-118连续的（9个重复标记对应110-118回）
# 前28段(82-109)正常 + 后9段(重复标记，实际是110-118回) = 37段
# 总段数应为 37
# 实际body_secs可能>=37（因为"第一百零X"之后才是"第一百一十"重复）
# 策略：按顺序映射 82→索引0, 83→索引1, ... 最后把多出来的合并到最后一章
n_sections = len(body_secs)
n_expected = len(ZSK_TITLES)  # 37

for sub in ["fan", "jian", "bai"]:
    d = os.path.join(VDIR, sub)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)

ch_meta = []
for i in range(min(n_sections, n_expected) - 1):
    num = 82 + i
    fn = f"ch{num:03d}.txt"
    title = f"第{cn_num(num)}回 {ZSK_TITLES[i]}"
    body = body_secs[i][1]
    full = title + "\n\n" + body
    with open(os.path.join(VDIR, "fan", fn), "w", encoding="utf-8") as f:
        f.write(full)
    j = cc.convert(full)
    with open(os.path.join(VDIR, "jian", fn), "w", encoding="utf-8") as f:
        f.write(j)
    with open(os.path.join(VDIR, "bai", fn), "w", encoding="utf-8") as f:
        f.write(j)
    ch_meta.append({"num": num, "title": title, "file": f"fan/{fn}"})

# 最后一章合并剩余
last_i = min(n_sections, n_expected) - 1
num = 82 + last_i
fn = f"ch{num:03d}.txt"
title = f"第{cn_num(num)}回 {ZSK_TITLES[last_i]}"
merged = "\n\n".join(b for _, b in body_secs[last_i:])
full = title + "\n\n" + merged
with open(os.path.join(VDIR, "fan", fn), "w", encoding="utf-8") as f:
    f.write(full)
j = cc.convert(full)
with open(os.path.join(VDIR, "jian", fn), "w", encoding="utf-8") as f:
    f.write(j)
with open(os.path.join(VDIR, "bai", fn), "w", encoding="utf-8") as f:
    f.write(j)
ch_meta.append({"num": num, "title": title, "file": f"fan/{fn}"})

with open(os.path.join(VDIR, "chapters.json"), "w", encoding="utf-8") as f:
    json.dump({"id":"zsk","label":"征四寇（82-118回·招安至征方腊中段）","chapters":ch_meta}, f, ensure_ascii=False, indent=2)

print(f"✅ zsk: {len(ch_meta)} 文件 (82-{num}回)")
print(f"首回: {ch_meta[0]['title']}")
print(f"末回: {ch_meta[-1]['title']}")
print(f"末回结尾: {merged[-80:]}")
