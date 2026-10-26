#!/usr/bin/env python3
"""扩充余象斗《水浒志传评林》批注层：在原 4 卷（t=15 独立切分）基础上，
按「評」字起头成块的方式，尽力从其余各卷的上栏录文中还原评语。

识典机器录文里，部分卷的上栏评语与中栏插图标题同属 lineType=1，交错混排。
本脚本以空行（lineType=3/5）切块，取「評」起头的块，
再按「文言虚词」特征裁掉块尾的中栏插图标题（图题如「楊志遇見魯智深」不含之/也/矣）。
"""
import json, os, re, math
from opencc import OpenCC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw/yuxiangdou")
OUT = os.path.join(ROOT, "docs/texts/versions/yuxiangdou_comments.json")
t2s = OpenCC("t2s")

FIX = {'冝':'宜','廼':'乃','呉':'吴','䖏':'处','賔':'宾','顔':'颜','淂':'得','覌':'观',
       '𢙣':'恶','䝨':'贤','囯':'国','慇':'殷','觧':'解','児':'儿','邁':'迈','迺':'乃',
       '𦂯':'才','樑':'梁','𠁅':'处','𬁔':'跳','綉':'绣','㸔':'看','杲':'呆','𢀰':'爱'}

# 文言虚词（评语常用）
XUCI = set('之也矣哉耳乎焉而其者乃耶')
# 中栏插图标题常见动词（简体，因裁切在转简之后进行）
TUTI_V = ('遇见','会见','议计','议事','相见','拜见','分付','说知','听得','来看','来见','捉住',
          '入去','上山','上岗','下寨','在关','出阵','杀了','打死','救出','放火','取去',
          '入二龙山','见太守','说与','细说','来文','入伙','捉贼','报知','大败','杀入','议军务','问路','拿小七','对敌','见兄','坐堂')

VOLS_WITH_T15 = {6, 11, 18, 24}


def load_names():
    """从站点数据载入人物名、地名，用于识别中栏图题。"""
    names = set()

    def rec(o):
        if isinstance(o, dict):
            v = o.get('name')
            if isinstance(v, str) and 1 < len(v) <= 6:
                names.add(v)
            for x in o.values():
                rec(x)
        elif isinstance(o, list):
            for x in o:
                rec(x)
    for rel in ('docs/data/heroes/heroes.json', 'docs/data/places/places.json'):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            rec(json.load(open(p, encoding='utf-8')))
    return names


NAMES = None


def fixvar(s):
    for k, v in FIX.items():
        s = s.replace(k, v)
    return s


def to_simp(s):
    return fixvar(t2s.convert(s))


def blocks(d):
    out, cur = [], []
    for l in d['lines']:
        if l['t'] in (3, 5):
            if cur:
                out.append(cur); cur = []
        else:
            cur.append(l)
    if cur:
        out.append(cur)
    return out


def is_tuti(seg):
    """判断一个短句是否为中栏插图标题（而非评语）。"""
    seg = seg.strip()
    if not seg:
        return False
    if any(c in XUCI for c in seg):        # 含文言虚词 → 是评语
        return False
    if len(seg) > 18:
        return False
    has_name = bool(NAMES) and any(nm in seg for nm in NAMES)
    if has_name and (any(v in seg for v in TUTI_V) or len(seg) <= 12):
        return True
    return any(v in seg for v in TUTI_V)


def trim_tuti(text):
    """从块尾向前，逐句剔除中栏图题。"""
    segs = re.findall(r'[^。！？]*[。！？]|[^。！？]+$', text)
    segs = [s for s in segs if s.strip()]
    cut = len(segs)
    while cut > 1 and is_tuti(segs[cut - 1]):
        cut -= 1
    return ''.join(segs[:cut])


def extract_from_vol(fname):
    d = json.load(open(os.path.join(RAW, fname + '.json'), encoding='utf-8'))
    items, seen = [], set()
    # 1) t=15 独立切分（若有，优先，最完整）
    s15 = ''.join(x['x'] for x in d['lines'] if x['t'] == 15)
    srcs = []
    if s15.strip():
        srcs.append(s15)
    # 2) 「評」起头成块
    for b in blocks(d):
        txt = ''.join(x['x'] for x in b)
        if txt.startswith(('評', '评')) and '評林' not in txt[:12]:
            srcs.append(txt)
    for raw in srcs:
        for p in re.split(r'(?=[評评])', raw):
            p = p.strip()
            if not p or p[0] not in '評评':
                continue
            body = to_simp(p[1:])
            body = re.sub(r'[□㐲�\uFFFD〇■]', '', body)
            body = trim_tuti(body)
            body = re.sub(r'\s+', '', body)
            if len(body) < 6:
                continue
            if body in seen:
                continue
            seen.add(body)
            items.append('评' + body)
    return items


def main():
    global NAMES
    NAMES = load_names()
    data = json.load(open(OUT, encoding='utf-8'))
    vols = data['volumes']
    fmap = {v['no']: f for v, f in zip(vols, sorted(os.listdir(RAW))) if f.endswith('.json')}
    # 建立 卷号 -> 文件名（raw 顺序 00 卷首 01 卷一 ... 25 卷二十五）
    raw_files = sorted([f for f in os.listdir(RAW) if f.endswith('.json')])
    # 卷一 ... 卷二十五 对应 raw_files[1:26]
    name2file = {}
    for f in raw_files:
        m = re.search(r'卷之?([一二三四五六七八九十]+)', f)
        if m:
            name2file[f] = m.group(1)
    CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,
          '十九':19,'二十':20,'二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25}
    volno2file = {}
    for f in raw_files:
        m = re.search(r'卷之?([一二三四五六七八九十]+)\.json', f)
        if m and m.group(1) in CN:
            volno2file[CN[m.group(1)]] = f

    stat = []
    for v in vols:
        no = v['no']
        if v['items']:                       # 保留原有成果
            stat.append((no, len(v['items']), '原有'))
            continue
        f = volno2file.get(no)
        if not f:
            stat.append((no, 0, '无源'))
            continue
        items = extract_from_vol(f[:-5])
        v['items'] = items
        stat.append((no, len(items), '新增' if items else '空'))

    data['coverage'] = {
        "vols_with_comments": [v['no'] for v in vols if v['items']],
        "note": ("识典古籍《水滸志傳評林》机器录文中，上栏评语仅部分卷被独立切分（lineType=15，"
                 "即卷之六、十一、十八、二十四）；其余各卷之上栏评语与中栏插图标题同属行类型 1、交错混排，"
                 "本库按空行切块、取「評」起头者，据文言特征裁去块尾图题后存录，残损字与讹字存原样，仅供参照。")
    }
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('卷号  条数  来源')
    tot = 0
    for no, n, src in stat:
        tot += n
        print(f'  {no:2d}   {n:4d}  {src}')
    print('合计评语条数:', tot)


if __name__ == '__main__':
    main()
