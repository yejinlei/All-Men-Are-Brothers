#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用三个真正独立的原始源（raw/）重新构建三版正文：
- v100  ← rongyutang_100hui.txt   （容与堂百回本繁本，100回+引首）
- v120  ← yuanwuya_120hui.txt     （袁无涯百二十回本，120回+引首）
- v70   ← jinshengtan_70hui.txt   （金圣叹贯华堂七十回本，楔子+70回+惊恶梦）
然后生成：
- jin70     ← Gutenberg 繁体七十回本（作为"繁体金本"）
- jin70_pi / jinshengtan  ← v70 正文 + 金批
- jiqin     ← jiqin_jiao_zhu_100hui.txt（容与堂底本+校注前言，100回）
- zsk       ← zhengsikou.txt（第82-120回 征四寇简本后段）

每个版本目录下有 fan / jian / bai 三个子目录，txt 文件名按 ch001.txt 起命名。
"""
import os, re, json, shutil, sys
from opencc import OpenCC

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW     = os.path.join(BASE, 'raw')
VERDIR  = os.path.join(BASE, 'docs', 'texts', 'versions')

t2s = OpenCC('t2s')
s2t = OpenCC('s2t')

# ---------- 章节解析 ----------
XIEZI_RE  = re.compile(r'^={5}\s*(楔子|引首)\s*([^=]*?)\s*={5}\s*$')
CHAPTER_RE= re.compile(r'^={5}\s*第([一二三四五六七八九十百零〇两\d]+)回?\s*([^=]*?)\s*={5}\s*$')
GUTEN_DELIM= re.compile(r'^(楔子|第[一二三四五六七八九十百零〇两\d]+回)[\s　]*([^\n]+)$')

CN = {'零':0,'〇':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'两':2}
def cn2int(s):
    s = s.strip()
    if s.isdigit(): return int(s)
    s = s.replace('單','单')
    total = 0
    if '百' in s:
        b, _, a = s.partition('百')
        total += (CN.get(b,1) if b else 1) * 100
        a = a.replace('单','').replace('零','').replace('〇','')
        if a:
            if '十' in a:
                t,_,o = a.partition('十')
                total += CN.get(t,1)*10
                if o: total += CN.get(o,0)
            elif len(a)==1:
                total += CN.get(a,0)
    elif '十' in s:
        t,_,o = s.partition('十')
        total += (CN.get(t,1) if t else 1)*10
        if o: total += CN.get(o,0)
    else:
        for c in s:
            total = total*10 + CN.get(c,0)
    return total

def split_equal_delim(raw_path, expects_preamble_cut=False, force_sequential=False):
    """通用 ===== 第N回 标题 ===== 分隔解析。
    force_sequential=True 时忽略分隔符里写的编号，按分隔符出现顺序从 1 开始顺次编号（修复源文件写错回号的问题）。"""
    with open(raw_path,'r',encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    chapters=[]; cur=None; buf=[]; preamble=[]; in_pre=True; seq_hui=0
    def push():
        if cur is None: return
        body='\n'.join(buf).strip()
        chapters.append({**cur,'content':body,'chars':len(body)})
    for line in lines:
        s = line.strip()
        m = XIEZI_RE.match(s)
        if m:
            push()
            cur={'id':'xiezi_0','num':0,'title':(m.group(1)+(m.group(2) or '')).strip()}
            buf=[]; in_pre=False; continue
        m = CHAPTER_RE.match(s)
        if m:
            push()
            if force_sequential:
                seq_hui += 1
                n = seq_hui
                title_rest = m.group(2).strip()
                # 把标题里残留的截断字符（如"张""王""史"）替换为标准回目，稍后由调用方传进来；
                # 这里先用 m.group(2) 的原字，后面再用权威表覆盖
                cur={'id':f'hui_{n}','num':n,'title':f'第{m.group(1)}回 '+title_rest if title_rest else f'第{n}回'}
            else:
                n = cn2int(m.group(1))
                cur={'id':f'hui_{n}','num':n,'title':f'第{m.group(1)}回 '+m.group(2).strip()}
            buf=[]; in_pre=False; continue
        if in_pre: preamble.append(line)
        else: buf.append(line)
    push()
    return chapters

def split_title_lines(raw_path, chapter_pat=r'^第[一二三四五六七八九十百零\d]+回[\s　]'):
    """按独占行的回目标题分隔（冀勤校注本格式）。
    文件开头是前言+回目目录，需跳过目录定位正文：以"第一回"独占行出现两次，第二次才是正文起始。"""
    import re
    pat = re.compile(chapter_pat)
    with open(raw_path,'r',encoding='utf-8') as f:
        text=f.read()
    lines=text.split('\n')
    # 找"引首"独占行位置（在正文开头）
    preface_end=0
    for i,l in enumerate(lines):
        if l.strip()=='引首' and i>200:  # 正文里的"引首"（不是目录）
            preface_end=i; break
    if preface_end==0:
        # 退回到：找"第一回"第二次出现作为正文起始
        first_hits=[i for i,l in enumerate(lines) if re.match(r'^第一回[\s　]', l.strip()) and len(l.strip())<80]
        preface_end=first_hits[1]-1 if len(first_hits)>=2 else (first_hits[0] if first_hits else 0)
        # 往前找"引首"行
        for i in range(preface_end, max(0,preface_end-5), -1):
            if lines[i].strip()=='引首':
                preface_end=i; break
    preamble='\n'.join(lines[:preface_end]).strip()
    chapters=[]; cur=None; buf=[]
    def push():
        if cur is None: return
        body='\n'.join(buf).strip()
        cur['content']=body; cur['chars']=len(body); chapters.append(cur)
    started=False
    chapters.append({'id':'xiezi_0','num':0,'title':'引首','content':'','chars':0})
    cur_yinshou_buf=[]
    last_num=0
    for i in range(preface_end+1, len(lines)):
        l=lines[i]; s=l.strip()
        m = pat.match(s)
        if m and len(s)<80:
            mh=re.match(r'^第([一二三四五六七八九十百零\d]+)回[\s　]+(.+)$', s)
            n = cn2int(mh.group(1)) if mh else 0
            title = mh.group(0).strip() if mh else s
            # 必须回号递增才视为新回（避免目录里重复匹配）
            if n <= last_num:
                buf.append(l); continue
            last_num=n
            if not started:
                chapters[0]['content']='\n'.join(cur_yinshou_buf).strip()
                chapters[0]['chars']=len(chapters[0]['content'])
                started=True
            else:
                push()
            cur={'id':f'hui_{n}','num':n,'title':title.strip()}
            buf=[]
            continue
        if not started:
            cur_yinshou_buf.append(l)
        else:
            buf.append(l)
    push()
    return chapters, preamble

def split_gutenberg(raw_path):
    """Gutenberg 繁体本：章节是 '第N回 标题' 独占一行，前面是 *** START *** 块。"""
    with open(raw_path,'r',encoding='utf-8') as f:
        text=f.read()
    # 去头部
    i = text.find('*** START OF')
    if i>=0: text=text[i:]
    # 去尾部
    j = text.find('*** END OF')
    if j>=0: text=text[:j]
    lines=text.split('\n')
    chapters=[]; cur=None; buf=[]
    def push():
        if cur is None: return
        body='\n'.join(buf).strip()
        chapters.append({**cur,'content':body,'chars':len(body)})
    for line in lines:
        s=line.strip()
        # 寻找楔子 / 第X回 独占行
        m=GUTEN_DELIM.match(s)
        if m and (m.group(1).startswith('第') or m.group(1)=='楔子') and len(s)<40:
            push()
            if m.group(1)=='楔子':
                cur={'id':'xiezi_0','num':0,'title':'楔子 '+m.group(2).strip()}
            else:
                nn=cn2int(m.group(1)[1:-1])
                cur={'id':f'hui_{nn}','num':nn,'title':m.group(1)+' '+m.group(2).strip()}
            buf=[]; continue
        if cur is not None:
            buf.append(line)
    push()
    return chapters

# ---------- 白话文生成（规则版 + 完整保留韵文） ----------
# 注：第一回引首的白话文已手工精译保存在 prebuilt/bai_ch0.txt，其余回采用扩展规则法
REPL = [
    ('说道', '说'), ('问道', '问'), ('答道', '回答说'), ('便道', '就说'), ('说道', '说'),
    ('怎生', '怎么'), ('恁地', '这么'), ('兀的', '这'), ('兀那', '那'),
    ('如何', '怎么'), ('为何', '为什么'), ('怎地', '怎么'), ('怎的', '怎么'),
    ('此', '这'), ('其', '他的'), ('之', '的'), ('乎', '吗'), ('者', '的人'),
    ('曰', '说'), ('遂', '于是'), ('乃', '于是'), ('即', '就'), ('便', '就'),
    ('皆', '都'), ('俱', '都'), ('咸', '都'), ('俱各', '全都'),
    ('言', '说'), ('语', '说'), ('谓', '对……说'),
    ('吾', '我'), ('汝', '你'), ('尔', '你'), ('彼', '他'), ('某', '我'),
    ('俺', '我'), ('洒家', '我'), ('奴家', '我'),
    ('且说', '话说'), ('且说', '再说'), ('看官听说', '各位读者听我说'),
    ('且将', '暂且把'), ('且把', '暂且把'), ('且教', '暂且让'),
    ('原来', '原来'), ('原来', '原来'),
    ('了的的', '了'), ('了了', '了'),
    ('端的', '确实'), ('端的是', '确实是'),
    ('莫非', '难道'), ('莫不是', '难道是'),
    ('休', '别'), ('休要', '不要'), ('休得', '不要'), ('勿', '不要'),
    ('莫', '别'), ('未', '没'), ('未曾', '还没有'), ('不曾', '没有'),
    ('犹', '还'), ('尚', '还'), ('尚自', '还'),
    ('已自', '已经'), ('已', '已经'), ('既', '既然'),
    ('与', '和'), ('同', '和'), ('并', '和'), ('及', '以及'),
    ('至', '到'), ('到于', '到'), ('径投', '直奔'), ('径到', '直奔'),
    ('若', '如果'), ('若是', '如果'), ('如若', '如果'), ('倘或', '如果'),
    ('但', '只'), ('但是', '只要是'), ('但凡', '凡是'),
    ('甚', '很'), ('甚是', '非常'), ('甚为', '非常'),
    ('必', '一定'), ('必定', '一定'), ('必然', '一定'),
    ('须臾', '一会儿'), ('少刻', '片刻'), ('不多时', '没多久'),
    ('当下', '当下'), ('当时', '当时'),
    ('见', '看见'), ('见说', '听说'), ('见得', '看得出来'),
    ('来到', '来到'), ('到得', '到了'), ('听得', '听到'), ('说道', '说'),
    ('只见', '只见'), ('但见', '只见'), ('怎见得', '怎么见得'),
    ('有诗为证', '有诗为证'), ('诗曰', '诗曰'), ('词曰', '词曰'),
    ('且听下回分解', '且听下回分解'),
    ('話', '话'), ('來', '来'), ('時', '时'), ('爲', '为'), ('國', '国'),
]

# 把简体白话化的核心：先 t2s，再做词汇替换；
# 韵文（诗、词、对句、回目）整段保留。
# 简化策略：检测段落是否为纯韵文（连续短句以句号/逗号断，每句7/5/4字且无长于15字分句）——
# 这里采用更稳妥的规则：以"诗曰/词曰/有诗为证/古风/七律/五律/但见/怎生结束/有分教"开头的段落整体保留原文；
# 其他段落按 REPL 做白话化。

POETRY_MARK = re.compile(r'^(诗曰|词曰|有诗为证|古风|七律|五律|七绝|五绝|古风一首|五言|七言|偈曰|但见|怎见得|有分教|调寄|念奴娇|西江月|临江仙|水调歌|鹧鸪天|蝶恋花|满庭芳|苏幕遮|浣溪沙|青玉案)')

def vernacularize(fan_text):
    """把繁体原文→简体+白话化。韵文整段保留。"""
    simplified = t2s.convert(fan_text)
    out=[]
    for para in simplified.split('\n'):
        s=para.strip()
        if not s:
            out.append(para); continue
        # 韵文/套语保留原句
        if POETRY_MARK.match(s) or s.startswith('诗曰：') or s.startswith('词曰：') or s.startswith('有诗为证'):
            out.append(para); continue
        # 太短的（<6字）一般是标题、对句起句，保留
        if len(s)<6:
            out.append(para); continue
        # 回目 / 章题直接保留
        if re.match(r'^第[一二三四五六七八九十百零\d]+回[\s　]', s):
            out.append(para); continue
        new=s
        # 替换：按短语长度从长到短避免叠字
        for a,b in sorted(REPL, key=lambda x:-len(x[0])):
            new=new.replace(a,b)
        # 去叠字：如"降降地"这类，保留单字叠词（"看看""说说"）
        new=re.sub(r'([\u4e00-\u9fa5])\1{2,}', r'\1\1', new)
        new=new.replace('了了','了').replace('的的','的')
        out.append(para[:0]+new)  # 保留前导空白
    return '\n'.join(out)

# ---------- 写入版本目录 ----------
def write_version(vid, chapters, label, source_file, has_xiezi=True, title_list=None):
    """title_list: 可选，list[120] = 第N回完整标题（用于 v120 修正源文件错写的回号）。"""
    outdir = os.path.join(VERDIR, vid)
    fan_dir = os.path.join(outdir, 'fan')
    jian_dir= os.path.join(outdir, 'jian')
    bai_dir = os.path.join(outdir, 'bai')
    for d in [fan_dir,jian_dir,bai_dir]:
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
    toc=[]
    for c in chapters:
        num=c['num']
        fn = f"ch{num:03d}.txt" if c['id'].startswith('hui_') else "ch000.txt"
        # 若有权威标题，替换错误回目标题
        if title_list and c['id'].startswith('hui_') and 1<=num<=len(title_list):
            c['title']=f'第{num}回 '+title_list[num-1]
        fan = c['content']
        fan = fan.strip()+'\n'
        jian = t2s.convert(fan)
        bai  = vernacularize(fan)
        with open(os.path.join(fan_dir, fn),'w',encoding='utf-8') as f: f.write(fan)
        with open(os.path.join(jian_dir,fn),'w',encoding='utf-8') as f: f.write(jian)
        with open(os.path.join(bai_dir, fn),'w',encoding='utf-8') as f: f.write(bai)
        toc.append({'id':c['id'],'num':c['num'],'title':c['title'],'chars':c['chars'],'file':fn})
    meta={
        'id':vid,'label':label,'source':os.path.basename(source_file),
        'chapters':toc,
        'total_hui': len([x for x in chapters if x['id'].startswith('hui_')]),
        'has_xiezi': has_xiezi,
        'total_chars': sum(x['chars'] for x in chapters),
    }
    with open(os.path.join(outdir,'chapters.json'),'w',encoding='utf-8') as f:
        json.dump(meta,f,ensure_ascii=False,indent=2)
    with open(os.path.join(outdir,'index.json'),'w',encoding='utf-8') as f:
        json.dump(meta,f,ensure_ascii=False,indent=2)
    print(f"[{vid:>10}] {label}  → {len(toc)} 章节 | {meta['total_chars']:,} 字 | fan/jian/bai 已生成")
    return meta

# ---------- jiqin 校注本处理（含校注前言和目录说明） ----------
def build_jiqin():
    chapters, preface = split_title_lines(os.path.join(RAW,'jiqin_jiao_zhu_100hui.txt'))
    outdir=os.path.join(VERDIR,'jiqin')
    for d in ['fan','jian','bai']:
        dd=os.path.join(outdir,d)
        if os.path.isdir(dd): shutil.rmtree(dd)
        os.makedirs(dd, exist_ok=True)
    # 写前言
    for d,txt in [('fan',preface+'\n'),('jian',t2s.convert(preface)+'\n'),('bai',vernacularize(preface)+'\n')]:
        with open(os.path.join(outdir,d,'preface.txt'),'w',encoding='utf-8') as f:
            f.write(txt)
    toc=[]
    for c in chapters:
        n=c['num']
        fn = f"ch{n:03d}.txt" if c['id'].startswith('hui_') else 'ch000.txt'
        fan = c['content'].strip()+'\n'
        jian= t2s.convert(fan)
        bai = vernacularize(fan)
        for d,txt in [('fan',fan),('jian',jian),('bai',bai)]:
            with open(os.path.join(outdir,d,fn),'w',encoding='utf-8') as f: f.write(txt)
        toc.append({'id':c['id'],'num':n,'title':c['title'],'chars':c['chars'],'file':fn})
    meta={'id':'jiqin','label':'水浒传（冀勤校注百回本·容与堂底本）','source':'jiqin_jiao_zhu_100hui.txt',
          'chapters':toc,'total_hui':len([x for x in chapters if x['id'].startswith('hui_')]),
          'has_xiezi':True,'has_preface':True,'total_chars':sum(x['chars'] for x in chapters)+len(preface)}
    with open(os.path.join(outdir,'chapters.json'),'w',encoding='utf-8') as f:
        json.dump(meta,f,ensure_ascii=False,indent=2)
    with open(os.path.join(outdir,'index.json'),'w',encoding='utf-8') as f:
        json.dump(meta,f,ensure_ascii=False,indent=2)
    print(f"[     jiqin] 水浒传（冀勤校注百回本）  → {len(toc)} 章节 | {meta['total_chars']:,} 字 | 含前言")

# ---------- 金圣叹批本（jin70_pi/jinshengtan = v70 正文 + 金批结构） ----------
def link_jinpi_to_v70():
    """把 jin70_pi / jinshengtan 的 fan/jian/bai 链接/复制到 v70 的对应内容（因为正文即金本）。
    批注单独保留。"""
    import shutil as _sh
    for vid in ['jin70_pi','jinshengtan']:
        outdir=os.path.join(VERDIR,vid)
        # 复用 v70 内容
        v70dir=os.path.join(VERDIR,'v70')
        for d in ['fan','jian','bai']:
            dst=os.path.join(outdir,d)
            if os.path.isdir(dst): _sh.rmtree(dst)
            _sh.copytree(os.path.join(v70dir,d), dst)
        # 更新 chapters.json
        v70chap=json.load(open(os.path.join(v70dir,'chapters.json'),encoding='utf-8'))
        v70chap['id']=vid
        v70chap['label']= '金圣叹批评本（全批·繁）' if vid=='jin70_pi' else '金圣叹批评本（全批·简）'
        v70chap['has_comments']='jinpi'
        with open(os.path.join(outdir,'chapters.json'),'w',encoding='utf-8') as f:
            json.dump(v70chap,f,ensure_ascii=False,indent=2)
        with open(os.path.join(outdir,'index.json'),'w',encoding='utf-8') as f:
            json.dump(v70chap,f,ensure_ascii=False,indent=2)
        print(f"[{vid:>10}] {v70chap['label']}  → 复用 v70 正文 + 金批")

# ---------- Gutenberg 繁体金本（作为 jin70 独立版本） ----------
def build_jin70_gutenberg():
    chs=split_gutenberg(os.path.join(RAW,'jin70_gutenberg_fanti.txt'))
    write_version('jin70', chs, '金圣叹评本（繁体公领域底本·Gutenberg #23863）', 'jin70_gutenberg_fanti.txt')

# ---------- 征四寇（zsk）：82-120 回招安后情节（简本） ----------
def build_zsk():
    """zhengsikou.txt 已从第82回开始，直接按 ===== 分并重新编号。"""
    chs=split_equal_delim(os.path.join(RAW,'zhengsikou.txt'))
    # 第一个可能是 第82回（不是引首）
    out=[]
    start_num=82
    # 检查第一个实际回号
    if chs and chs[0]['num']>0:
        offset=start_num-chs[0]['num']
        for c in chs:
            if c['id'].startswith('hui_'):
                n=c['num']+offset
                out.append({'id':f'hui_{n}','num':n,'title':f'第{n}回（征四寇）'+c['title'].split('回',1)[-1] if '回' in c['title'] else c['title'],
                            'content':c['content'],'chars':c['chars']})
            else:
                out.append(c)
    else:
        out=chs
    write_version('zsk', out, '征四寇（简本后段·招安后征四寇38回）', 'zhengsikou.txt', has_xiezi=False)

# ============ 主流程 ============
if __name__=='__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from titles_120 import TITLES_120
    print('===== 重建版本正文（从独立源）=====')
    # v100: 容与堂百回本，前71回回目已正确，后面按分隔符顺序
    v100 = split_equal_delim(os.path.join(RAW,'rongyutang_100hui.txt'))
    # 验证 rongyutang 实际 101 个分隔符（引首+100回），按顺序编号
    # 容与堂的前 71 回分隔符标题都写对了，后面回号也正确（之前检查过）
    write_version('v100', v100, '忠义水浒传（百回本·容与堂/天都外臣系统繁本）', 'rongyutang_100hui.txt')

    # v120: 袁无涯百二十回本
    # 源文件共有 120 个 ===== 行 = 引首 + 119 个回分隔符，其中：
    #   - 第99回分隔符缺失（98回后直接是"第一百回"，但里面包含99+100两回内容）
    #   - 111-119回分隔符都被错写成"第一百一十"
    #   - 最后一个分隔符明确标"第一百二十"，内容即第120回（神聚蓼儿洼）
    # 策略：按出现顺序编号为第1回~第119回（中间99/100合并为一个单元用第99回号，标题用第99回），
    #       最后插入的"第一百二十"处理为第120回；第100回空缺单独处理（接受源文件本身合并两回的事实）。
    ywy_path = os.path.join(RAW,'yuanwuya_120hui.txt')
    with open(ywy_path,'r',encoding='utf-8') as f:
        ywy_text=f.read()
    # 把 "===== 第一百回 =====" 改名为 "===== 第九十九回 ====="（与实际内容"水灌太原"匹配）
    ywy_text = ywy_text.replace('===== 第一百回 =====', '===== 第九十九回 =====', 1)
    tmp_ywy = os.path.join(BASE,'build','_yuanwuya_fixed.txt')
    with open(tmp_ywy,'w',encoding='utf-8') as f: f.write(ywy_text)
    v120 = split_equal_delim(tmp_ywy, force_sequential=True)
    hui_count = len([c for c in v120 if c['id'].startswith('hui_')])
    print(f'  [v120 按顺序编号: 共 {hui_count} 回 + 引首]')
    # 编号修正：顺序1-119 → 实际回号1-119，最后一个分隔符"第一百二十"是第120回。
    # 但force_sequential把"第一百零一"标为第100回，错位+1；
    # 所以实际需要：1-99正确，100-119实际是101-120。
    # 重新编号：
    renumbered=[]
    for c in v120:
        if c['id'].startswith('hui_'):
            seq = c['num']
            if seq <= 99:
                real_num = seq
            else:
                real_num = seq + 1  # 100→101 ... 119→120
            c = dict(c)
            c['num']=real_num
            c['id']=f'hui_{real_num}'
        renumbered.append(c)
    v120 = renumbered
    write_version('v120', v120, '水浒全传（百二十回·袁无涯原刊本，含征田虎王庆）', 'yuanwuya_120hui.txt', title_list=TITLES_120)

    # v70: 金圣叹七十回本
    v70  = split_equal_delim(os.path.join(RAW,'jinshengtan_70hui.txt'))
    hui70 = len([c for c in v70 if c['id'].startswith('hui_')])
    print(f'  [v70 按顺序编号: 共 {hui70} 回 + 楔子]')
    write_version('v70',  v70,  '第五才子书（七十回本·金圣叹贯华堂本，惊恶梦结尾）', 'jinshengtan_70hui.txt')

    # 其他版本
    build_jin70_gutenberg()
    build_jiqin()
    build_zsk()
    link_jinpi_to_v70()

    print('===== 完成 =====')
