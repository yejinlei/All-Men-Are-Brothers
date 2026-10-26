#!/usr/bin/env python3
"""从识典古籍 CADAL02015977《鍾批水滸傳》机器录文提取卷一、卷二的回后总评，
写入 docs/texts/versions/zhongbo_comments.json 的 chapters 字段。

钟批本传世仅存前二回正文（四知馆/积庆堂刊本），识典仅上线 卷首/目录/前序/卷一/卷二。
其中卷末「總評」为结构完整的回后总评，可校读；正文眉批、侧批与下栏正文混排过甚，暂不成层。
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/tmp/zb'
RAW = os.path.join(ROOT, 'raw/zhongbo')
OUT = os.path.join(ROOT, 'docs/texts/versions/zhongbo_comments.json')
os.makedirs(RAW, exist_ok=True)

HEAD_RE = re.compile(r'^[□總总]?評[：:。]?$|^[□總总]評$')


def load_html(fn):
    h = open(fn, encoding='utf-8').read()
    s = h.find('window._ROUTER_DATA'); s = h.find('{', s)
    depth = 0; instr = False; esc = False
    for j in range(s, len(h)):
        c = h[j]
        if esc: esc = False; continue
        if c == '\\': esc = True; continue
        if c == '"': instr = not instr; continue
        if instr: continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return json.loads(h[s:j+1])


def lines(fn):
    d = load_html(os.path.join(SRC, fn))
    pl = d['loaderData']['__session/(lang$)/book/$']['paragraphList']
    out = []
    for p in pl:
        try:
            obj = json.loads(p['content'])
        except Exception:
            continue
        for ln in obj.get('lines', []):
            c = ln.get('content', '')
            if c.strip():
                out.append({'t': ln.get('lineType'), 'x': c})
    return out


def tidy(s):
    s = re.sub(r'[□〇口\uFFFD]', '', s)
    s = re.sub(r'\s+', '', s)
    return s.strip('，。、')


def extract_zongping(ls):
    si = None
    for i, l in enumerate(ls):
        if HEAD_RE.match(l['x'].strip()):
            si = i                       # 取最后一处「評」标记
    if si is None:
        return None
    ei = len(ls)
    for j in range(len(ls) - 1, si, -1):
        if '鍾伯敬' in ls[j]['x'] or '卷之' in ls[j]['x']:
            ei = j
            break
    body = ''.join(x['x'] for x in ls[si + 1:ei])
    return tidy(body)


def main():
    data = json.load(open(OUT, encoding='utf-8'))
    chapters = []
    for fn, num in (('juan1.html', 1), ('juan2.html', 2)):
        ls = lines(fn)
        json.dump({'lines': ls}, open(os.path.join(RAW, fn.replace('.html', '.json')), 'w',
                                      encoding='utf-8'), ensure_ascii=False)
        zp = extract_zongping(ls)
        items = [{'k': '回后总评', 'v': zp}] if zp and len(zp) >= 6 else []
        chapters.append({'num': num, 'name': f'第{num}回', 'items': items})
        print(f'{fn} -> 第{num}回 总评 {len(items)} 条：{zp}')
    data['chapters'] = chapters
    data['description'] = ('明钟惺（字伯敬）批评《水浒忠义传》一百卷一百回，正文有眉批、侧批及回后总评，'
                           '卷首附《水浒传人品评》。据识典古籍 CADAL02015977 号机器整理本辑录。'
                           '钟批本传世仅存前二回正文（另序文、目录残缺），故正文批语见卷一、卷二；'
                           '《人品评》逐人品第，为钟批特色。')
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写入', OUT)


if __name__ == '__main__':
    main()
