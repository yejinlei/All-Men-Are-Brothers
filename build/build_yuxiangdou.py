#!/usr/bin/env python3
"""从 raw/yuxiangdou 的识典机器录文生成余象斗《水浒志传评林》批注层数据。

识典古籍 CADAL02015583《水滸志傳評林》的机器录文以 lineType 区分版面内容：
  lineType=1  下栏正文（含卷名、回目、诗词）
  lineType=2  上层内容（多数卷与下栏正文混排，残缺过甚）
  lineType=15 上栏评语（仅卷六、卷十一、卷十八、卷二十四被独立切分）
  lineType=3/5 图片/空行

上栏评语原文格式为「評〇〇＋评语」，竖排被切成碎行，本脚本按顺序拼接后再按「評」切分还原。
"""
import json, math, os, re
from opencc import OpenCC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw/yuxiangdou")
OUT = os.path.join(ROOT, "docs/texts/versions/yuxiangdou_comments.json")
t2s = OpenCC("t2s")

# 常见异体/僻字 → 正字（opencc 不处理的字形）
FIX = {'冝':'宜','廼':'乃','呉':'吴','䖏':'处','賔':'宾','顔':'颜','淂':'得','覌':'观',
       '𢙣':'恶','䝨':'贤','囯':'国','慇':'殷','觧':'解','児':'儿','邁':'迈','迺':'乃',
       '𦂯':'才','樑':'梁','𠁅':'处','𬁔':'跳','綉':'绣','㸔':'看'}

# 有独立上栏评语（lineType=15）的卷
VOLS_WITH = {6:'06_卷六', 11:'11_卷十一', 18:'18_卷十八', 24:'24_卷二十四'}

XU = ('先儒谓：尽心之谓忠，心制事之谓义。愚因曰：尽心于为国之为忠，事宜在济民之谓义。'
      '若宋江等，其诸忠者乎？其诸义者乎？当是时，宋德衰微，乾纲不揽，官箴失措，下民咨嗟，'
      '山谷嗷嗷，英雄豪杰，愤国治之不平，悯民庶之失所，乃崛起山东，乌合云从，据水浒之险以为依，'
      '涣汗大号，其势吞天浴日，奔鲸骇鸷，可谓涣奔其杌，涣有丘矣。不知者曰：此民之贼也，国之蠹也。'
      '噫，不然也，彼盖强者锄之，弱者扶之，富者削之，贫者周之，冤屈者起而伸之，囚困者斧而□，'
      '虽未必为仁者博施，众按其行事之迹，可谓桓、文仗义并轨。君子玩之者，当略彼非，取其平济之是，'
      '则豪贫困者生全，而奸官敛手，曰：有为之忠，有济民之义。昔人谓春秋者，史外传心之要典；'
      '愚则谓此传者，纪外叙事之要览也。岂可曰此非圣经，此非贤传，而可藐之哉？谨序。'
      '万历甲午岁腊月吉旦序。')

BIAN = ('水浒一书，坊间梓者纷纷，偏像者十余副，全像者止一家。前像板字中差讹，其板像旧，'
        '惟三槐堂一副，省诗去词，不便观诵。今双峰堂余子改正增评，有不便览者芟之，有漏者删之，'
        '内有失韵诗词欲削去，恐观者言其省漏，皆记上层；前廿余卷一画一句并无差错，士子买者可认。双峰堂为记。')


def fixvar(s):
    for k, v in FIX.items():
        s = s.replace(k, v)
    return s


def clean(s):
    s = t2s.convert(s)
    s = fixvar(s)
    s = re.sub(r'[□㐲�\uFFFD〇]', '', s)
    s = re.sub(r'[。，、；：！？「」『』（）()\[\]·…—\-\s]', '', s)
    return s.strip()


def split_title(head):
    """头部的「評〇〇」对象名：优先取后文再次出现的前缀，否则取前 2 字。"""
    for L in (3, 2, 4):
        cand = head[:L]
        if len(head) > L and cand in head[L:]:
            return cand, head[L:]
    m = re.match(r'^([\u4e00-\u9fff]{2})', head)
    t = m.group(1) if m else head[:2]
    return t, head[len(t):]


def extract_vol(fname):
    d = json.load(open(os.path.join(RAW, fname + '.json'), encoding='utf-8'))
    s15 = ''.join(x['x'] for x in d['lines'] if x['t'] == 15)
    parts = [p for p in re.split(r'(?=[評评])', s15) if p.strip() and p.strip()[0] in '評评']
    items, seen = [], set()
    for p in parts:
        head = clean(p[1:])
        if len(head) < 4:
            continue
        title, body = split_title(head)
        body = body if len(body) >= 4 else head
        if body in seen:
            continue
        seen.add(body)
        items.append('评' + title + '：' + body)
    return items


def vol_range(n):
    """25 卷 120 回，平均 4.8 回/卷；区段连续无重叠。"""
    return [int(math.floor((n - 1) * 4.8)) + 1, int(math.floor(n * 4.8))]


_CN = '零一二三四五六七八九十'


def cn_num(n):
    if n <= 10:
        return _CN[n]
    if n < 20:
        return '十' + _CN[n % 10]
    if n % 10 == 0:
        return _CN[n // 10] + '十'
    return _CN[n // 10] + '十' + _CN[n % 10]


def main():
    by_vol = {n: extract_vol(f) for n, f in VOLS_WITH.items()}
    volumes = []
    for n in range(1, 26):
        volumes.append({'no': n, 'name': '卷之' + cn_num(n),
                        'hui': vol_range(n), 'items': by_vol.get(n, [])})
    data = {
        'id': 'yuxiangdou',
        'name': '余象斗（余仰止·双峰堂）',
        'dynasty': '明',
        'color': '#a9622d',
        'description': '明余象斗（字仰止，号文台，福建建阳双峰堂书坊主）评《京本增补校正全像忠义水浒志传评林》二十五卷一百二十回，万历二十二年（1594）双峰堂刊。此本为现存最早、最完整的《水浒传》评点本，属“文简事繁”简本系统，版式上栏评语、中栏插图、下栏正文；上栏评语简峭峻切，重人物识鉴与情节评断。',
        'source': '识典古籍 CADAL02015583《水浒志传评林》AI整理本；原刊孤本藏日本日光轮王寺慈眼堂（天海藏）。上栏评语系机器录文，残损、讹字存原样，仅供参照。',
        'preface': {'title': '题水浒传叙（万历甲午）', 'text': XU},
        'bian': {'title': '水浒辨（双峰堂识语）', 'text': BIAN},
        'coverage': {'vols_with_comments': sorted(by_vol.keys()),
                     'note': '识典古籍《水滸志傳評林》机器录文中，仅卷六、卷十一、卷十八、卷二十四四卷的上栏评语被独立切分（lineType=15），可校读还原；其余各卷评语在录文中与下栏正文混排、残缺过甚，暂缺。'},
        'volumes': volumes,
    }
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('written', OUT)
    print('卷数', len(volumes), '评语总数', sum(len(v['items']) for v in volumes))
    for v in volumes:
        if v['items']:
            print('  卷', v['no'], v['hui'], len(v['items']), '条  例:', v['items'][0][:50])


if __name__ == '__main__':
    main()
