#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
互文网络构建：
输入：
  raw/intertext/dxyhs/*.txt（《大宋宣和遗事》四集）
  raw/intertext/zaju/*.txt（元水浒杂剧 8 种）
  docs/texts/versions/v120/jian/ch*.txt（袁百二回本简体会作为对照主线）
  docs/data/heroes/heroes.json（梁山人物）
  docs/data/events/events.json（情节事件）
输出：
  docs/data/intertext.json  互文源 + 复用关系 + 人物映射表
"""
import json, os, re, glob
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw', 'intertext')
OUT = os.path.join(ROOT, 'docs', 'data')
TXTV120 = os.path.join(ROOT, 'docs', 'texts', 'versions', 'v120', 'jian')

# ---------- 工具 ----------
def normalize(s):
    """留汉字、字母、数字"""
    return ''.join(c for c in s if '\u4e00' <= c <= '\u9fff' or c.isalnum())

def ngrams(text, n=4):
    t = normalize(text)
    return set(t[i:i+n] for i in range(len(t)-n+1)) if len(t)>=n else set()

def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / max(len(a | b), 1)

def read_text(p):
    with open(p, encoding='utf-8') as f:
        return f.read()

# ---------- 源文元数据 ----------
SOURCES = [
    {
        'id':'dxyhs', 'label':'大宋宣和遗事', 'era':'南宋末年-元初（约13世纪）',
        'author':'无名氏（宋人旧本，经元人增益）',
        'type':'讲史话本', 'chars':0, 'extant':'full',
        'refs':['鲁迅《中国小说史略》元明传来之讲史','《士礼居丛书》本二卷系统'],
        'note':'分元亨利贞四集。水浒故事集中在元集末段与亨集前半，杨志卖刀/生辰纲/宋江杀惜/九天玄女天书/三十六将/张叔夜招降/征方腊等核心母题已具雏形。',
        'files':['raw/intertext/dxyhs/yuan.txt','raw/intertext/dxyhs/heng.txt','raw/intertext/dxyhs/li.txt','raw/intertext/dxyhs/zhen.txt'],
        'credibility':'B', # 公版话本，底本清后期重刊，本次录入经通行本核对
    },
    {
        'id':'zaju_shuang_xian_gong','label':'黑旋风双献功','era':'元代·前期','author':'高文秀','type':'元杂剧',
        'chars':0,'extant':'full','note':'又名《双献头》。孙孔目泰安神州烧香，李逵化装庄家护送，杀白衙内、郭念儿，双献头归山。是高文秀"黑旋风杂剧系列"唯一存世完本。',
        'files':['raw/intertext/zaju/shuang_xian_gong.txt'],'credibility':'B',
        'refs':['《元曲选》壬集','隋树森《元曲选外编》校对']
    },
    {
        'id':'zaju_yanqing_boyu','label':'同乐院燕青博鱼','era':'元代·前期','author':'李文蔚','type':'元杂剧',
        'chars':0,'extant':'full','note':'燕青因违限遭杖责双目失明，下山医眼，与燕顺、燕和兄弟结识同乐院博鱼，痛打与燕和妻王腊梅私通的杨衙内。',
        'files':['raw/intertext/zaju/yanqing_boyu.txt'],'credibility':'B','refs':['《元曲选》己集']
    },
    {
        'id':'zaju_zheng_bao_en','label':'争报恩三虎下山','era':'元代','author':'无名氏','type':'元杂剧',
        'chars':0,'extant':'full','note':'关胜、徐宁、花荣先后在权家店被通判夫人李千娇救护，后李千娇遭二夫人王腊梅诬陷，三虎下山法场相救。',
        'files':['raw/intertext/zaju/zheng_bao_en.txt'],'credibility':'B','refs':['《元曲选》辛集']
    },
    {
        'id':'zaju_likui_fu_jing','label':'梁山泊李逵负荆','era':'元代·前期','author':'康进之','type':'元杂剧',
        'chars':0,'extant':'full','note':'宋刚、鲁智恩冒充宋江鲁智深抢王林之女满堂娇，李逵怒砍杏黄旗，下山对质后负荆请罪，擒贼将功折罪。是现存元水浒戏中与《水浒传》最吻合的剧本，第七十三回"黑旋风乔捉鬼 梁山泊双献头"情节据此改造。',
        'files':['raw/intertext/zaju/likui_fu_jing.txt'],'credibility':'B+','refs':['《元曲选》壬集','学界通行认定此剧为《水浒》第七十三回直接祖本']
    },
    {
        'id':'zaju_huan_lao_mo','label':'都孔目风雨还牢末','era':'元代','author':'李致远','type':'元杂剧',
        'chars':0,'extant':'full','note':'东平府孔目李荣祖救护史进、刘唐遭陷两次入牢，李逵劫法场救出全家归山。剧中"李山儿"与李逵重名，造成后世版本混淆。',
        'files':['raw/intertext/zaju/huan_lao_mo.txt'],'credibility':'C+','refs':['《元曲选》癸集；本次录入为情节梗概+开场合璧']
    },
    {
        'id':'zaju_huanghua_yu','label':'鲁智深喜赏黄花峪','era':'元末明初','author':'无名氏','type':'元杂剧',
        'chars':0,'extant':'full','note':'刘庆甫妻李幼奴被蔡衙内强占，杨雄解救未果，李逵假扮货郎深入水南寨营救，鲁智深于黄花峪云岩寺擒获蔡衙内。"权豪势要强占人妻"母题被视为《水浒传》高衙内情节的戏曲源头。',
        'files':['raw/intertext/zaju/huanghua_yu.txt'],'credibility':'C+','refs':['《孤本元明杂剧》本；本次录入关键折开场+情节梗概']
    },
    {
        'id':'zaju_zhangyi_shucai','label':'黑旋风仗义疏财','era':'明初','author':'朱有燉','type':'明杂剧',
        'chars':0,'extant':'full','note':'赵都巡强抢李憋古之女，李逵、燕青假扮新娘痛打恶人，后上梁山发兵擒赵。教化色彩浓重。',
        'files':['raw/intertext/zaju/zhangyi_shucai.txt'],'credibility':'C','refs':['《明周宪王乐府三种》；本次录入情节梗概']
    },
    {
        'id':'zaju_baozi_heshang','label':'豹子和尚自还俗','era':'明初','author':'朱有燉','type':'明杂剧',
        'chars':0,'extant':'full','note':'鲁智深因口角离山再出家，宋江派李逵、吴学究、妻子等轮番劝归，最终念及骨肉还俗。',
        'files':['raw/intertext/zaju/baozi_heshang.txt'],'credibility':'C','refs':['《明周宪王乐府三种》；本次录入情节梗概']
    },
]

# ---------- 人名异写表（蓝本 → 《水浒》名） ----------
NAME_ALIAS = {
    # 宣和遗事异名
    '吴加亮':'吴用','卢进义':'卢俊义','李进义':'卢俊义','吴学究':'吴用','李海':'李俊',
    '阮进':'阮小二','关必胜':'关胜','张青':'张清','朱同':'朱仝','王雄':'杨雄',
    '穆横':'穆弘','呼延绰':'呼延灼','石秀':'石秀','张岑':'张横','杜千':'杜迁',
    '铁天王晁盖':'晁盖','晁盖':'晁盖','马安国':'','尹大谅':'','花约':'',
    '张大年':'','梁师宝':'','王成':'','阎婆惜':'阎婆惜','吴伟':'','张叔夜':'张叔夜',
    '吴加亮(吴用)':'吴用','孙立':'孙立','秦明':'秦明','燕青':'燕青','董平':'董平','一撞直董平':'董平',
    '李进义(卢俊义)':'卢俊义','浪里百跳张顺':'张顺','浪里白跳张顺':'张顺',
    '大刀关必胜':'关胜','金枪手徐宁':'徐宁','扑天雕李应':'李应','赤发鬼刘唐':'刘唐',
    '插翅虎雷横':'雷横','美髯公朱同':'朱仝','神行太保戴宗':'戴宗','赛关索王雄':'杨雄',
    '小李广花荣':'花荣','没羽箭张青':'张清','没遮拦穆横':'穆弘','混江龙李海':'李俊',
    '短命二郎阮进':'阮小二','立地太岁阮小五':'阮小五','活阎罗阮小七':'阮小七',
    '九纹龙史进':'史进','入云龙公孙胜':'公孙胜','铁鞭呼延绰':'呼延灼','急先锋索超':'索超',
    '火船工张岑':'张横','摸着云杜千':'杜迁','弃命二郎石秀':'石秀',
    '一丈青张横':'张横',  # 宣和本中"一丈青张横"，水浒后为扈三娘绰号
    # 杂剧常见称
    '宋公明':'宋江','山儿李逵':'李逵','李山儿':'李逵','鲁智恩':'','宋刚':'',
    '孙孔目':'','郭念儿':'','白衙内':'','王林':'','满堂娇':'','刘庆甫':'','李幼奴':'蔡衙内',
    '赵通判':'','李千娇':'','王腊梅':'','丁都管':'','蔡疙疸':'蔡衙内',
    '杨衙内':'','燕和':'','燕顺':'','吕彦彪':'','赵令史':'','萧娥':'',
    '李憋古':'','李荣祖':'','孙荣':'','满堂娇':'',
}

# ---------- 情节对表（人工标注的明确对应）----------
PLOT_PARALLELS = [
    {
        'src':'dxyhs','src_anchor':'杨志卖刀/雪阻卖刀杀人','title':'杨志卖刀',
        'hui':12,'shz_event':'汴京城杨志卖刀','heroes':['杨志','孙立'],
        'evidence':'宣和遗事：杨志颖州雪阻，货宝刀杀恶少，配卫州；孙立等十一人黄河岸劫救落草。水浒第十二回改为东京卖刀杀泼皮牛二，被大名府梁中书看中。'
    },
    {
        'src':'dxyhs','src_anchor':'五花营劫生辰纲','title':'智取生辰纲',
        'hui':16,'shz_event':'吴用智取生辰纲','heroes':['晁盖','吴用','刘唐','阮小二','阮小五','阮小七'],
        'evidence':'宣和遗事：五花营堤上，"酒海花家"借酒桶，晁盖铁天王为首劫蔡太师十万贯金珠，八人名单含吴加亮、刘唐、秦明、阮进、阮通、阮小七、燕青。水浒改黄泥冈，加入白胜、吴用、公孙胜，秦明未加入该段。'
    },
    {
        'src':'dxyhs','src_anchor':'石碣村报信','title':'宋江私放晁天王',
        'hui':18,'shz_event':'宋公明私放晁天王','heroes':['宋江','晁盖'],
        'evidence':'宣和遗事：押司宋江接文字星夜去石碣村报信，晁盖暮夜逃走。水浒第十八回情节几乎一致，只是"右碣村"改"石碣村"，"铁天王"已改为"托塔天王"。'
    },
    {
        'src':'dxyhs','src_anchor':'杀阎婆惜吴伟','title':'宋江杀惜',
        'hui':21,'shz_event':'宋江怒杀阎婆惜','heroes':['宋江','阎婆惜'],
        'evidence':'宣和遗事：宋江撞见阎婆惜与吴伟偎依，怒杀二人，题诗"杀了阎婆惜，寰中显姓名"。水浒改为只杀阎婆惜，删吴伟，改于第二十一回。'
    },
    {
        'src':'dxyhs','src_anchor':'九天玄女庙得天书','title':'还道村受天书',
        'hui':42,'shz_event':'还道村受三卷天书','heroes':['宋江'],
        'evidence':'宣和遗事：宋江躲于屋后九天玄女庙，香案上得天书一卷列三十六人姓名。水浒第四十二回为还道村玄女庙授三卷天书，名单扩为一百零八人。'
    },
    {
        'src':'dxyhs','src_anchor':'三十六将归聚张叔夜招降征方腊','title':'梁山聚义/招安/征方腊',
        'hui':82,'shz_event':'梁山泊分金大买市','heroes':['宋江'],
        'evidence':'宣和遗事：天书点三十六将，张叔夜招降，收方腊有功封节度使。水浒扩为百/百二十回，招安延后至八十二回，征方腊在九十回之后，且宋江未封节度使而被赐毒酒。'
    },
    {
        'src':'zaju_likui_fu_jing','src_anchor':'冒名抢亲/砍旗负荆',
        'title':'黑旋风乔捉鬼·双献头（第七十三回）',
        'hui':73,'shz_event':'黑旋风乔捉鬼 梁山泊双献头','heroes':['李逵','宋江','鲁智深'],
        'evidence':'康进之《李逵负荆》：宋刚鲁智恩冒名抢满堂娇，李逵怒砍杏黄旗，下山对质后负荆。水浒第七十三回情节直接据此改写，只是把满堂娇改为刘太公之女，歹徒改名。'
    },
    {
        'src':'zaju_huanghua_yu','src_anchor':'权豪强占人妻',
        'title':'豹子头误入白虎堂（第七回高衙内母题）',
        'hui':7,'shz_event':'豹子头误入白虎堂','heroes':['林冲'],
        'evidence':'《黄花峪》蔡衙内"打死人如揭瓦"强占李幼奴。学界认为"权豪势要强占人妻"是元水浒戏的固定母题，被《水浒》改造为第七回高衙内强占林娘子桥段。'
    },
    {
        'src':'zaju_shuang_xian_gong','src_anchor':'泰安神州烧香护臂',
        'title':'燕青泰安打擂（第七十四回）',
        'hui':74,'shz_event':'燕青智扑擎天柱','heroes':['李逵','燕青'],
        'evidence':'《双献功》写泰安神州烧香，李逵化装护臂；水浒第七十四回燕青智扑擎天柱任原，地点同为泰安州东岳庙，李逵同去大闹寿张县，场景重合。'
    },
    {
        'src':'zaju_yanqing_boyu','src_anchor':'燕青博鱼/同乐院痛打杨衙内',
        'title':'燕青形象塑造的戏曲素材',
        'hui':74,'shz_event':'燕青智扑擎天柱','heroes':['燕青'],
        'evidence':'此剧是燕青为主角的仅存元杂剧，水浒中燕青的"相扑""市井气""博鱼/博钱"细节与此剧有血脉关系，但具体情节被重构。'
    },
    {
        'src':'zaju_zheng_bao_en','src_anchor':'关胜徐宁花荣先后被救/法场相救',
        'title':'多人单刀救援模式',
        'hui':62,'shz_event':'放冷箭燕青救主 劫法场石秀跳楼','heroes':['关胜','徐宁','花荣'],
        'evidence':'此剧"三虎下山法场救人"是元水浒戏常见结构，水浒中劫法场（石秀跳楼、江州）亦延续此结构，但人物与情节已改写。'
    },
    {
        'src':'zaju_huan_lao_mo','src_anchor':'李孔目救护梁山人遭陷',
        'title':'梁山与官府小吏的恩义网络',
        'hui':0,'shz_event':'（多回累积）','heroes':['史进','刘唐','李逵'],
        'evidence':'此剧以官府小吏（孔目）救护梁山好汉反遭迫害为戏剧冲突，水浒中宋江（押司）、朱仝（都头）、雷横（都头）、叶孔目等人物形象均延续此脉络。'
    },
]

def main():
    # 读水浒主角名
    heroes = json.load(open(os.path.join(OUT,'heroes','heroes.json'),encoding='utf-8'))
    hnames = set(x['name'] for x in heroes['heroes'])
    # 加入主要绰号做识别
    nicks = {x['name']:x['nickname'] for x in heroes['heroes']}

    # 读水浒各回 v120 简体
    hui_text = {}
    for fp in sorted(glob.glob(os.path.join(TXTV120,'ch*.txt'))):
        m=re.search(r'ch(\d+)\.txt', os.path.basename(fp))
        if not m: continue
        num=int(m.group(1))
        txt=read_text(fp)
        hui_text[num]=txt

    # 读 events
    events = json.load(open(os.path.join(OUT,'events','events.json'),encoding='utf-8'))['events']
    ev_by_hui = defaultdict(list)
    for ev in events:
        ev_by_hui[ev['hui']].append(ev)

    # 组装源文全文+字数
    sources=[]
    src_text={}
    for s in SOURCES:
        full=''
        for rel in s['files']:
            p=os.path.join(ROOT, rel)
            if os.path.exists(p):
                full += read_text(p)+'\n'
        # 简体化（原文繁体直接保留，不做转写；标记为"存录原貌"）
        s['chars']=len(normalize(full))
        s = {k:v for k,v in s.items() if k not in ('files',)}
        sources.append(s)
        src_text[s['id']]=full

    # 计算 n-gram 重叠：每源 → 每回（以 120 回为主线）
    HUI_NG = {h: ngrams(t,4) for h,t in hui_text.items()}

    parallels=[]
    pid=0
    # 1) 人工标注的情节对表（置信度高）
    for p in PLOT_PARALLELS:
        sid=p['src']
        src=src_text.get(sid,'')
        # 截取 src_anchor 附近片段
        idx=src.find(p['src_anchor'][:6])
        if idx<0: idx=src.find(p['src_anchor'][-6:])
        if idx<0: idx=0
        snip=src[max(0,idx-40):idx+160].strip().replace('\n',' ')
        # ngram 重叠
        s4=ngrams(snip,4)
        ov=len(s4 & HUI_NG.get(p['hui'],set()))
        # 共享人物
        sh_heroes=[h for h in p['heroes'] if h in snip or h in src[:5000]]
        parallels.append({
            'id':f'P{pid:03d}','src':sid,'src_anchor':p['src_anchor'],'src_excerpt':snip,
            'hui':p['hui'],'event':p['shz_event'],'heroes':p['heroes'],
            'shared_4gram':ov,'relation':'plot_inherited','confidence':'A' if p['src']=='zaju_likui_fu_jing' or p['src']=='dxyhs' else 'B',
            'evidence':p['evidence']
        })
        pid+=1

    # 2) 自动发现：对每个源文滑窗 200 字，与每回做 ngram 重叠，阈值=3
    auto_found=0
    for sid, txt in src_text.items():
        norm=normalize(txt)
        for start in range(0,len(norm)-200,120):
            window=norm[start:start+240]
            w4=ngrams(window,4)
            if len(w4)<50: continue
            best=[]
            for h,h4 in HUI_NG.items():
                ov=len(w4 & h4)
                if ov>=3:
                    best.append((ov,h))
            best.sort(reverse=True)
            if best and best[0][0]>=4:
                ov,h=best[0]
                # 排除已有人工标注覆盖的 hui
                if any(x['src']==sid and x['hui']==h for x in parallels):
                    continue
                # 找窗口出现的梁山人物
                present=[hn for hn in hnames if hn in window]
                if len(present)>=2 or ov>=6:
                    snip=window[:120]
                    parallels.append({
                        'id':f'P{pid:03d}','src':sid,'src_anchor':'(滑窗检测)','src_excerpt':snip,
                        'hui':h,'event':ev_by_hui[h][0]['name'] if ev_by_hui.get(h) else f'第{h}回',
                        'heroes':present[:6],'shared_4gram':ov,'relation':'ngram_overlap','confidence':'C',
                        'evidence':f'4-gram 重叠 {ov} 字，可能是共用表述或互文片段，需人工复核。'
                    })
                    pid+=1; auto_found+=1
                    if auto_found>60: break
        if auto_found>60: break

    # 3) 人物异写对应表
    name_mappings=[]
    for old,new in sorted(set(NAME_ALIAS.items())):
        if not new: continue
        # 统计源文中出现次数
        cnt=0
        for sid,t in src_text.items():
            if old in t: cnt+=t.count(old)
        if cnt>0 or old in ('吴加亮','李进义','卢进义','关必胜','阮进','王雄','朱同','穆横','呼延绰','李海','张岑','杜千'):
            name_mappings.append({'source_name':old,'shz_name':new,'occurrence_in_sources':cnt})
    # 加入不在 ALIAS 的水浒重要人物"源文无出现"作为对照
    for hn in ['公孙胜','林冲','武松','鲁智深','董平','张清','李俊','张横','解珍','解宝','卢俊义','吴用']:
        if not any(x['shz_name']==hn for x in name_mappings):
            # 看原名是否在源文中出现
            cnt=sum(t.count(hn) for t in src_text.values())
            name_mappings.append({'source_name':hn,'shz_name':hn,'occurrence_in_sources':cnt,'note':'今本《水浒》人物，在《宣和遗事》或杂剧中以异名或未出现'})

    # ---------- 异名演化表（宣和36将 → 龚开36赞 → 水浒36天罡）----------
    xuanhe_36 = [
        ('智多星吴加亮','吴用'),('玉麒麟卢进义','卢俊义'),('青面兽杨志','杨志'),
        ('混江龙李海','李俊'),('九纹龙史进','史进'),('入云龙公孙胜','公孙胜'),
        ('浪里百跳张顺','张顺'),('霹雳火秦明','秦明'),('活阎罗阮小七','阮小七'),
        ('立地太岁阮小五','阮小五'),('短命二郎阮进','阮小二'),('大刀关必胜','关胜'),
        ('豹子头林冲','林冲'),('黑旋风李逵','李逵'),('小旋风柴进','柴进'),
        ('金枪手徐宁','徐宁'),('扑天雕李应','李应'),('赤发鬼刘唐','刘唐'),
        ('一撞直董平','董平'),('插翅虎雷横','雷横'),('美髯公朱同','朱仝'),
        ('神行太保戴宗','戴宗'),('赛关索王雄','杨雄'),('病尉迟孙立','孙立'),
        ('小李广花荣','花荣'),('没羽箭张青','张清'),('没遮拦穆横','穆弘'),
        ('浪子燕青','燕青'),('花和尚鲁智深','鲁智深'),('行者武松','武松'),
        ('铁鞭呼延绰','呼延灼'),('急先锋索超','索超'),('弃命二郎石秀','石秀'),
        ('火船工张岑','张横'),('摸着云杜千','杜迁'),('铁天王晁盖','晁盖'),
    ]

    # ---------- 统计 ----------
    by_src=Counter(p['src'] for p in parallels)
    by_relation=Counter(p['relation'] for p in parallels)
    src_with_para=[s['id'] for s in sources if by_src.get(s['id'],0)>0]

    out={
        'meta':{
            'title':'《水浒传》互文网络数据',
            'version':'2026-10-27',
            'note':'本数据集为"成书来源互文"研究底座。包含源文元信息、4-gram 重叠检测、人物异写映射、情节承继人工标注。n-gram 检测为统计近似，不可视为定论；置信度 A 为学界公认直接承继，B 为情节母题强关联，C 为自动检测候选需人工复核。',
            'method':{
                'ngram_n':4,'window_size':240,'window_step':120,
                'auto_threshold':4,'baseline_version':'v120',
                'caveats':['以《袁百二回》简体版为回次基线，金本等异文系另参','繁简字未转换，可能漏检部分异写','4-gram 重叠不区分"直接抄袭""共用叙事套语""通用汉语词组"','人名异写仅覆盖学界已知主要条目，未做全面异体字归一']
            },
            'stats':{
                'sources':len(sources),'extant_full':sum(1 for s in sources if s['extant']=='full'),
                'plot_parallels_total':len(parallels),
                'manual_confirmed':sum(1 for p in parallels if p['relation']=='plot_inherited'),
                'auto_detected':sum(1 for p in parallels if p['relation']=='ngram_overlap'),
                'name_mappings':len(name_mappings),
                'covered_hui':len(set(p['hui'] for p in parallels if p['hui']>0)),
                'by_source':dict(by_src),'by_relation':dict(by_relation),
            }
        },
        'sources':sources,
        'xuanhe_36':[{'nick_old':a.split(' ',1)[0] if ' ' in a else a,'name_old':a,'name_shz':b} for a,b in xuanhe_36],
        'name_mappings':name_mappings,
        'parallels':sorted(parallels, key=lambda x:(x['src'], x['hui'])),
        'lost_plays_note':[
            '高文秀《黑旋风诗酒丽春园》《黑旋风大闹牡丹园》《黑旋风敷衍刘耍和》《黑旋风斗鸡会》《黑旋风穷风月》《双献头武松大报仇》',
            '康进之《黑旋风老收心》',
            '红字李二《折担儿武松打虎》《板踏儿黑旋风》《窄袖儿武松》《全火儿张弘》',
            '杨显之《黑旋风乔断案》',
            '李文蔚《燕青射雁》'
        ]
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT,'intertext.json'),'w',encoding='utf-8') as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print('intertext.json 写入 OK')
    print('stats:', json.dumps(out['meta']['stats'], ensure_ascii=False, indent=2))

if __name__=='__main__':
    main()
