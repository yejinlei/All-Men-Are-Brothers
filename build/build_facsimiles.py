"""
Step 17 影像并置：为各版本生成"版刻风格"仿真书影卡（牌记页 + 首卷正文页），
并输出 facsimiles.json 登记公版高清影印的外部永久链接。

为什么不把几百 MB~数 GB 的原刻本 PDF 入仓：影印本 PDF 普遍在 500MB~5GB，
GitHub Pages 仓库会被严重撑爆，也无法在线翻阅；因此本站提供：
  1. 版刻风格仿真样页（展示每版的版式特征：行格/框线/栏式/书坊牌记/绣像位置）；
  2. 外部高清源登记（书格 / HathiTrust / Gallica / 日本国立公文书馆 / Internet Archive 等公版镜像）。
"""
from __future__ import annotations
import json, os, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'docs', 'img', 'facs')
os.makedirs(OUT_DIR, exist_ok=True)

# 中文字体路径（系统自带 Noto Sans CJK）
FONT_CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONT_SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'

# ---------- 版本元数据（含外部高清源链接） ----------
FACSIMILES = [
    {
        'id': 'guohua',
        'short': '国图容与堂本',
        'full': '李卓吾先生批评忠义水浒传（容与堂本）',
        'year': '明万历三十八年（1610）前后',
        'printer': '杭州容与堂',
        'colophon': '庚戌仲夏日虎林孫樸書于三生石畔',
        'repo': '中国国家图书馆（甲本，罗原觉旧藏）；日本内阁文库亦藏一部',
        'format': '半叶十一行，行二十二字，白口，四周单边；框高 21.3×14.4 厘米',
        'features': [
            '百回繁本中现存最早完整本',
            '每回首有插图一叶两幅（黄应光、吴凤台刻，共两百幅）',
            '眉批、夹批、回末总评俱全（学界多认为出自叶昼托名李贽）',
        ],
        'style': 'rongyu',
        'sample_chap': '第一回　張天師祈禳瘟疫　洪太尉誤走妖魔',
        'sample_line': '話說大宋仁宗天子在位嘉祐三年三月三日五更三點天子駕坐紫宸殿受百',
        'downloads': [
            {'label': '书格 高清影印 PDF', 'url': 'https://s.shuge.org/rytshz', 'note': '容与堂本，含全部绣像'},
            {'label': '国家图书馆影印本（2019）', 'url': 'https://book.douban.com/subject/34446942/', 'note': '国家图书馆出版社 6 册精装'},
            {'label': '日本国立公文书馆（内阁文库）在线浏览', 'url': 'https://www.digital.archives.go.jp/img/4446087', 'note': '李卓吾先生批评忠义水滸伝 20 册，公开发布'},
        ],
    },
    {
        'id': 'jinshengtan',
        'short': '贯华堂金批本',
        'full': '第五才子书施耐庵水浒传（金圣叹贯华堂本）',
        'year': '明崇祯十四年（1641）',
        'printer': '苏州贯华堂',
        'colophon': '貫華堂所藏古本　施耐庵撰　聖歎外書',
        'repo': '贯华堂原刻本存世稀少，后世翻刻甚多；中华书局 1975 年据崇祯原刻影印',
        'format': '半叶八行，行十九字，白口，左右双边；眉批、夹批、回前总评',
        'features': [
            '金圣叹"腰斩"七十回，新增"惊恶梦"结尾',
            '评点系统最完整：三篇序、读第五才子书法、回前总评、双行夹批',
            '清代以来最通行的水浒版本',
        ],
        'style': 'guanhuatang',
        'sample_chap': '楔子　張天師祈禱瘟疫　洪太尉誤走妖魔',
        'sample_line': '一部大書七十回 吾讀之 只是一揮而就 妙絕',
        'downloads': [
            {'label': '中华书局 1975 影印本（豆瓣）', 'url': 'https://book.douban.com/subject/4836040/', 'note': '影印崇祯贯华堂刻本，8 册'},
            {'label': '万卷出版社《贯华堂第五才子书》', 'url': 'https://book.douban.com/subject/3637020/', 'note': '周锡山编校排印本'},
        ],
    },
    {
        'id': 'zhongbo',
        'short': '钟伯敬批评本',
        'full': '钟伯敬先生批评水浒忠义传',
        'year': '明天启四至五年（1624—1626）',
        'printer': '四知馆梓行（疑用积庆堂板刷印）',
        'colophon': '鍾伯敬先生批評水滸忠義傳　四知館梓行',
        'repo': '法国国家图书馆 CHINOIS 3992/3993/3994；京都大学附属图书馆藏积庆堂本',
        'format': '半叶十二行，行二十六字，白口，四周单边；框高 20×12.8 厘米；有眉批、侧批、回末总评',
        'features': [
            '书前附绣像 39 幅（一图一赞）',
            '题"竟陵钟惺伯敬父批评"，是晚明竟陵派评点小说的代表',
            '书格公开的是法国国家图书馆原色扫描本（5.29GB）',
        ],
        'style': 'zhongbo',
        'sample_chap': '卷之一　第一回　張天師祈禳瘟疫　洪太尉誤走妖魔',
        'sample_line': '鍾伯敬先生批評忠義水滸傳　竟陵鍾惺伯敬父批評',
        'downloads': [
            {'label': '书格 原色高清 PDF（5.29G）', 'url': 'https://t.shuge.org/zpshzt', 'note': '含法国图藏四知馆本 + 京都大学积庆堂本'},
            {'label': '广陵书社 2018 影印本（豆瓣）', 'url': 'https://book.douban.com/subject/35693998/', 'note': '二函十八册线装'},
            {'label': '京都大学藏积庆堂本', 'url': 'https://rmda.kulib.kyoto-u.ac.jp/', 'note': '京都大学贵重资料デジタルアーカイブ'},
        ],
    },
    {
        'id': 'yuping',
        'short': '余象斗评林本',
        'full': '京本增补校正全像忠义水浒志传评林（双峰堂本）',
        'year': '明万历二十二年（1594）',
        'printer': '福建建阳余氏双峰堂',
        'colophon': '雙峰堂余子改正增評　士子買者可認雙峰堂為記',
        'repo': '日本日光山轮王寺慈眼堂藏本（天海僧正旧藏），为现存最早最完整简本水浒',
        'format': '半叶三栏式：上栏评语、中栏图、下栏正文；每页一图（1236 幅插图）',
        'features': [
            '现存最早的水浒简本（文简事繁本），约 37 万字',
            '上评、中图、下文三栏版式，是连环画式通俗刊本的代表',
            '王古鲁 1956 年据照片内部影印 1000 套，缺卷九两叶',
        ],
        'style': 'shuangfeng',
        'sample_chap': '卷之一　第一回　張天師祈禳瘟疫',
        'sample_line': '且說宋朝天子仁宗在位 嘉祐三年 三月三日 天子陞殿',
        'downloads': [
            {'label': '沈阳出版社 2012 原大影印本（豆瓣）', 'url': 'https://book.douban.com/subject/6712465/', 'note': '精装上下卷，据原版原大影印'},
            {'label': '百度网盘影印资源（社区整理）', 'url': 'https://pan.baidu.com/s/1caXqPthlNsxCJMgz6cj19w?pwd=0000', 'note': '含古本小说集成 DjVu 版本'},
        ],
    },
    {
        'id': 'yuanwy',
        'short': '袁无涯全传本',
        'full': '李卓吾评忠义水浒全传（袁无涯书种堂/郁郁堂本）',
        'year': '明万历四十二年（1614）前后初刻，崇祯郁郁堂重梓',
        'printer': '苏州书种堂袁叔度无涯（后版归郁郁堂）',
        'colophon': '李卓吾先生批評忠義水滸全書　出像評點　郁郁堂梓',
        'repo': '北京大学图书馆、南京图书馆藏郁郁堂本；日本宫内厅书陵部亦藏',
        'format': '半叶十行，行二十二字；卷首有 120 幅绣像（五字标目）；有眉批、双行夹批',
        'features': [
            '现存最早的百二十回足本（增插征田虎、王庆二十回）',
            '1954 年人民文学出版社《水浒全传》以袁无涯系统为底本',
            '郁郁堂重印本（国内现存最早郁郁堂刊本）藏南京图书馆',
        ],
        'style': 'yuanwuya',
        'sample_chap': '第一回　張天師祈禳瘟疫　洪太尉誤走妖魔',
        'sample_line': '新鐫李氏藏本忠義水滸全書　施耐庵集撰　羅貫中纂修',
        'downloads': [
            {'label': '广陵书社 郁郁堂本影印', 'url': 'https://baijiahao.baidu.com/s?id=1796281570813491964', 'note': '四函三十六册，据南京图书馆藏甲本影印'},
            {'label': '人民文学出版社 1975/2019 百二十回排印本', 'url': 'https://book.douban.com/subject/1066830/', 'note': '通行袁系统整理本'},
        ],
    },
    {
        'id': 'dayuanren',
        'short': '大涤余人序本（李玄伯旧藏）',
        'full': '忠义水浒传（大涤余人序本 / 李玄伯原藏本）',
        'year': '明万历—天启间（约十七世纪初叶）',
        'printer': '明末杭州刊本（刻工含新安黄诚之、黄子立、刘启先）',
        'colophon': '大滌餘人序　徽派版畫',
        'repo': '原郑振铎旧藏，今归中国国家图书馆（残本存 44 回）',
        'format': '版画集中于首册，单图不依回目；应为百幅，存 97 幅；图版心有篆书二至七字标目',
        'features': [
            '徽派版画名作，构图精细、人物传神，与容与堂本插图并不重复',
            '芥子园本、袁无涯本、郁郁堂本的水浒图像均源出于此',
            '郑振铎编入《中国古代版画丛刊初编》（1958）',
        ],
        'style': 'daxu',
        'sample_chap': '圖：魯智深拳打鎮關西　篆書標目',
        'sample_line': '新安黃誠之　黃子立　劉啟先　刻',
        'downloads': [
            {'label': '广陵书社 2018 钟批本附录李玄伯本图像', 'url': 'https://baijiahao.baidu.com/s?id=1614887153044217510', 'note': '所缺三幅/两幅残图以芥子园本配补'},
            {'label': '郑振铎辑《中国古代版画丛刊初编》', 'url': 'https://book.douban.com/subject/1869812656/', 'note': '1958 年影印'},
        ],
    },
    {
        'id': 'chenhon',
        'short': '陈洪绶水浒叶子',
        'full': '陈老莲水浒叶子（博古酒牌）',
        'year': '明崇祯末年（约 1640 年代）',
        'printer': '明末刻本（徽州黄子立刻酒牌）',
        'colophon': '水滸葉子　陳章侯畫',
        'repo': '明末原刻本多有影印流传（如李一氓旧藏本）',
        'format': '酒牌叶子，每叶一位好汉，旁书赞语四行；白描高古，变形奇崛',
        'features': [
            '陈洪绶（老莲，1598–1652）晚年白描精品',
            '共绘宋江、林冲、武松、鲁智深、李逵等四十人（非 108 全数）',
            '后世水浒人物画的母本之一，影响了崔子忠、任熊、张光宇等人',
        ],
        'style': 'yezi',
        'sample_chap': '及時雨宋江　　呼保義',
        'sample_line': '刀筆小吏　爾身為義　敢笑黄巢不丈夫',
        'downloads': [
            {'label': '书格 陈老莲水浒叶子 PDF', 'url': 'https://www.shuge.org/', 'note': '收录于书格艺术类·明代版画合集'},
            {'label': '陈洪绶《水浒叶子》研究资料（豆瓣）', 'url': 'https://book.douban.com/subject/1425045/', 'note': '多家出版社有彩印本'},
        ],
    },
]

# ---------- 版刻风格颜色 ----------
STYLES = {
    'rongyu':      {'paper': '#f2e9d3', 'ink': '#1e1a16', 'seal': '#9e2b25', 'lines': '#1e1a16'},
    'guanhuatang': {'paper': '#ede4c9', 'ink': '#111111', 'seal': '#9e2b25', 'lines': '#111111'},
    'zhongbo':     {'paper': '#f5ecd4', 'ink': '#2a1f14', 'seal': '#9e2b25', 'lines': '#2a1f14'},
    'shuangfeng':  {'paper': '#e9dfc3', 'ink': '#2b241a', 'seal': '#8a1d1a', 'lines': '#2b241a'},
    'yuanwuya':    {'paper': '#f0e6ce', 'ink': '#1a1612', 'seal': '#9e2b25', 'lines': '#1a1612'},
    'daxu':        {'paper': '#f3e9d1', 'ink': '#1b1814', 'seal': '#9e2b25', 'lines': '#1b1814'},
    'yezi':        {'paper': '#efe5cf', 'ink': '#131210', 'seal': '#9e2b25', 'lines': '#131210'},
}


def _load_font(size, serif=False):
    path = FONT_SERIF if serif else FONT_CJK
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_frame(draw, box, style):
    ink = style['ink']
    x1, y1, x2, y2 = box
    # 外四边
    draw.rectangle([x1, y1, x2, y2], outline=ink, width=3)
    # 内细边（双边）
    draw.rectangle([x1+8, y1+8, x2-8, y2-8], outline=ink, width=1)


def _vertical_text(draw, x, y, text, font, ink, char_gap=6):
    """竖排文字：从上到下、从右到左；这里只写单列。"""
    cy = y
    for ch in text:
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((x - w // 2, cy), ch, font=font, fill=ink)
        cy += h + char_gap
    return cy


def _colophon_page(meta, style, W=820, H=1160):
    """生成牌记页（封面/书名页）。"""
    c = STYLES[style]
    img = Image.new('RGB', (W, H), c['paper'])
    d = ImageDraw.Draw(img)

    # 外框（版框）
    margin = 90
    _draw_frame(d, [margin, margin, W - margin, H - margin], c)

    # 版心上下鱼尾（简单三角）
    cx = W // 2
    d.polygon([(cx-10, margin+20), (cx+10, margin+20), (cx, margin+38)], fill=c['ink'])
    d.polygon([(cx-10, H-margin-20), (cx+10, H-margin-20), (cx, H-margin-38)], fill=c['ink'])

    # 中间大字书名：竖排三列（按版本）
    title_big = _load_font(78, serif=True)
    title_mid = _load_font(46, serif=True)
    title_sm  = _load_font(28)

    if style == 'shuangfeng':
        # 三栏：上评/中图/下文提示；这里只画牌记页的三栏框示范
        # 主书名大标题
        txt_lines = ['忠', '義', '水', '滸', '志', '傳', '評', '林']
        col_x = cx
        cy = margin + 80
        for ch in txt_lines:
            bb = title_big.getbbox(ch); w = bb[2]-bb[0]
            d.text((col_x - w//2, cy), ch, font=title_big, fill=c['ink'])
            cy += 90
    elif style == 'yezi':
        txt_lines = ['水', '滸', '葉', '子']
        col_x = cx
        cy = margin + 120
        for ch in txt_lines:
            bb = title_big.getbbox(ch); w = bb[2]-bb[0]
            d.text((col_x - w//2, cy), ch, font=title_big, fill=c['ink'])
            cy += 110
        # 右下"陈章侯画"小字
        f_sig = _load_font(26)
        d.text((W-margin-180, H-margin-80), '陳章侯畫', font=f_sig, fill=c['ink'])
    else:
        # 主标题：以 full 字段拆字竖排
        name = meta['full']
        # 截断中间主名
        if '李卓吾先生批評' in name or '李卓吾评' in name:
            main = '忠義水滸傳'
        elif '第五才子' in name:
            main = '第五才子書'
        elif '鍾伯敬' in name or '钟伯敬' in name:
            main = '水滸忠義傳'
        elif '忠義水滸' in name:
            main = '忠義水滸全書'
        else:
            main = '水滸傳'
        # 左列（卷次）、中列（主名大字）、右列（批评者）
        cy = margin + 100
        for ch in main:
            bb = title_big.getbbox(ch); w = bb[2]-bb[0]
            d.text((cx - w//2, cy), ch, font=title_big, fill=c['ink'])
            cy += 100
        # 左右小字：批评者 / 书坊
        left_txt = meta['printer'].replace('杭州','').replace('苏州','').replace('福建建阳余氏','')[:8]
        _vertical_text(d, cx - 160, margin + 180, left_txt, title_mid, c['ink'], char_gap=14)
        if '金' in style or '金圣叹' in meta['short']:
            _vertical_text(d, cx + 160, margin + 180, '聖歎外書', title_mid, c['ink'], char_gap=14)
        elif '容与' in meta['short']:
            _vertical_text(d, cx + 160, margin + 180, '李卓吾批評', title_mid, c['ink'], char_gap=14)
        elif '钟' in meta['short']:
            _vertical_text(d, cx + 160, margin + 180, '鍾惺伯敬父批評', title_mid, c['ink'], char_gap=12)
        elif '袁' in meta['short']:
            _vertical_text(d, cx + 160, margin + 180, '李卓吾評', title_mid, c['ink'], char_gap=14)
        elif '大涤' in meta['short']:
            _vertical_text(d, cx + 160, margin + 180, '徽派版畫', title_mid, c['ink'], char_gap=14)

    # 下方牌记（小字）
    colophon_font = _load_font(22)
    ctext = meta['colophon']
    bb = colophon_font.getbbox(ctext)
    tw = sum(colophon_font.getbbox(ch)[2]-colophon_font.getbbox(ch)[0]+8 for ch in ctext)
    d.text((cx - tw//2, H - margin - 80), ctext, font=colophon_font, fill=c['ink'])

    # 右上角朱印（方形）
    sx, sy, ss = W - margin - 100, margin + 40, 64
    d.rectangle([sx, sy, sx+ss, sy+ss], outline=c['seal'], width=3)
    seal_font = _load_font(20)
    seal_txt = ['水', '滸', '之', '印']
    for i, ch in enumerate(seal_txt):
        bx = sx + 12 + (i%2)*28
        by = sy + 8 + (i//2)*28
        d.text((bx, by), ch, font=seal_font, fill=c['seal'])

    # 左下角小字：年代
    year_font = _load_font(22)
    d.text((margin+40, H-margin-60), meta['year'], font=year_font, fill=c['ink'])

    return img


def _text_page(meta, style, W=820, H=1160):
    """生成首卷正文样页（含眉批/夹批示意）。"""
    c = STYLES[style]
    img = Image.new('RGB', (W, H), c['paper'])
    d = ImageDraw.Draw(img)

    margin = 70
    # 双半叶框（古籍筒子页）
    gutter = 28
    half_w = (W - 2*margin - gutter)//2
    box_L = [margin, margin+30, margin+half_w, H-margin-30]
    box_R = [margin+half_w+gutter, margin+30, W-margin, H-margin-30]

    _draw_frame(d, box_L, c)
    _draw_frame(d, box_R, c)

    # 版心（gutter 处）鱼尾 + 书名卷次
    cx = W//2
    cy_top = margin+30
    d.polygon([(cx-8, cy_top+10), (cx+8, cy_top+10), (cx, cy_top+26)], fill=c['ink'])
    d.polygon([(cx-8, H-margin-40), (cx+8, H-margin-40), (cx, H-margin-24)], fill=c['ink'])
    bx_font = _load_font(18)
    d.text((cx-40, cy_top+40), '忠義水滸傳', font=bx_font, fill=c['ink'])
    d.text((cx-16, H-margin-70), '第一回', font=bx_font, fill=c['ink'])

    body_font = _load_font(22, serif=True)
    pi_font   = _load_font(16)
    headpi_f  = _load_font(16)

    chap = meta['sample_chap']
    line = meta['sample_line']

    if style == 'shuangfeng':
        # 三栏：上批 18%，中图 32%，下文 50%
        for box in (box_L, box_R):
            x1,y1,x2,y2 = box
            h = y2-y1
            h_pi = int(h*0.18); h_img = int(h*0.32); h_txt = h - h_pi - h_img
            # 上栏
            d.line([(x1, y1+h_pi), (x2, y1+h_pi)], fill=c['ink'], width=1)
            d.text((x1+12, y1+10), '評曰：', font=pi_font, fill=c['ink'])
            d.text((x1+50, y1+10), '此言豪傑之起也 須看其', font=pi_font, fill=c['ink'])
            # 中栏：图（示意简笔人物+山形）
            d.line([(x1, y1+h_pi+h_img), (x2, y1+h_pi+h_img)], fill=c['ink'], width=1)
            mx, my = (x1+x2)//2, y1+h_pi + h_img//2
            # 山
            d.polygon([(x1+20, y1+h_pi+h_img-30), (mx-40, y1+h_pi+40), (mx-10, y1+h_pi+h_img-30)], outline=c['ink'], fill=None)
            d.polygon([(mx+10, y1+h_pi+h_img-30), (mx+80, y1+h_pi+50), (x2-20, y1+h_pi+h_img-30)], outline=c['ink'], fill=None)
            # 人物圆圈
            d.ellipse([mx-20, my-40, mx+20, my], outline=c['ink'], width=2)
            d.line([(mx, my), (mx, my+50)], fill=c['ink'], width=2)
            d.text((x1+12, y1+h_pi+8), '张天师祈禳瘟疫', font=pi_font, fill=c['ink'])
            # 下栏正文（横式模拟竖排）
            ty = y1+h_pi+h_img+14
            for i in range(9):
                txt = '話說大宋仁宗天子在位 這樁事從頭說來 ' + str(i+1)
                d.text((x1+12, ty), txt, font=pi_font, fill=c['ink'])
                ty += 28
    else:
        # 常规版式：竖排正文 10 列
        def fill_columns(box, has_head_pi=True, has_inter_pi=False):
            x1,y1,x2,y2 = box
            inner = [x1+16, y1+16, x2-16, y2-16]
            ix1, iy1, ix2, iy2 = inner
            # 眉批
            if has_head_pi:
                d.text((ix1+4, iy1), '眉批：開書第一回便從瘟疫起 見得亂自上作也', font=headpi_f, fill=c['ink'])
                body_top = iy1 + 28
                d.line([(ix1, body_top-6), (ix2, body_top-6)], fill=c['ink'], width=1)
            else:
                body_top = iy1
            # 回目大字顶列
            # 列从右到左
            col_w = (ix2-ix1)//10
            col_xs = [ix2 - (i+1)*col_w + col_w//2 for i in range(10)]
            # 第一列：回目
            cx0 = col_xs[0]
            cy = body_top
            ch_idx = 0
            for ch in chap:
                if ch == '　':
                    cy += 10; continue
                bb = body_font.getbbox(ch); w = bb[2]-bb[0]; h = bb[3]-bb[1]
                if cy + h > iy2: break
                d.text((cx0 - w//2, cy), ch, font=body_font, fill=c['ink'])
                cy += h + 6
                ch_idx += 1
            # 第二列起：正文 + 偶尔双行小字夹批模拟
            for col_i in range(1, 10):
                cx_ = col_xs[col_i]
                cy = body_top
                for k in range(14):
                    sample_chars = line * 2
                    pos = (col_i*14 + k) % len(sample_chars)
                    ch = sample_chars[pos]
                    if ch == '　': cy += 6; continue
                    # 偶尔插入夹批：第三列第 4 行起
                    if col_i == 3 and k == 4 and has_inter_pi:
                        sm = _load_font(13)
                        for kk, cc in enumerate(['妙','絕','一','個','祈','字']):
                            bb = sm.getbbox(cc); ww = bb[2]-bb[0]; hh = bb[3]-bb[1]
                            d.text((cx_+6 - ww//2, cy + kk*(hh+2)), cc, font=sm, fill=c['ink'])
                        cy += 12*2; continue
                    bb = body_font.getbbox(ch); w = bb[2]-bb[0]; h = bb[3]-bb[1]
                    if cy + h > iy2: break
                    d.text((cx_ - w//2, cy), ch, font=body_font, fill=c['ink'])
                    cy += h + 4
        fill_columns(box_L, has_head_pi=True, has_inter_pi=(style in ('guanhuatang','rongyu','zhongbo','yuanwuya')))
        fill_columns(box_R, has_head_pi=False, has_inter_pi=True)

    # 朱圈点（金圣叹式）：在几个字旁打朱圈
    if style == 'guanhuatang':
        for px, py in [(margin+half_w+gutter+30, margin+180), (margin+half_w+gutter+30, margin+220)]:
            d.ellipse([px-8, py-8, px+8, py+8], outline=c['seal'], width=2)

    return img


def main():
    manifest = []
    for m in FACSIMILES:
        sid = m['id']
        p_col = os.path.join(OUT_DIR, f'{sid}_colophon.png')
        p_txt = os.path.join(OUT_DIR, f'{sid}_text.png')
        col = _colophon_page(m, m['style'])
        col.save(p_col, 'PNG', optimize=True)
        txt = _text_page(m, m['style'])
        txt.save(p_txt, 'PNG', optimize=True)
        m_out = dict(m)
        m_out['colophon_img'] = f'img/facs/{sid}_colophon.png'
        m_out['text_img'] = f'img/facs/{sid}_text.png'
        manifest.append(m_out)
        print('wrote', p_col, os.path.getsize(p_col), 'bytes;', p_txt, os.path.getsize(p_txt), 'bytes')

    out_json = os.path.join(ROOT, 'docs', 'data', 'facsimiles.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            '_note': 'Step 17 影像并置元数据：仿真书影 + 公版外部高清影印链接',
            'updated': '2026-10-27',
            'method': '书影卡为本站以 PIL 绘制的版刻风格仿真示意，用于呈现各版本的版式特征（行格、框线、栏式、书坊牌记、绣像位置）；完整影印 PDF 请点击外部源前往下载（均为公版古籍）。',
            'facsimiles': manifest,
        }, f, ensure_ascii=False, indent=2)
    print('wrote', out_json)


if __name__ == '__main__':
    main()
