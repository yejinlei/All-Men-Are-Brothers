/* ================= 水浒传本体论 · 前端应用 ================= */

/* ---------- 数据加载 ---------- */
const DATA = {};
async function loadJSON(path) {
  try {
    const r = await fetch(path);
    return await r.json();
  } catch(e) { console.warn('load fail:', path, e); return null; }
}

async function boot() {
  const [baseline, heroes, factions, weapons, events, places, critics, derivatives, relations, idx] = await Promise.all([
    loadJSON('data/_baseline.json'),
    loadJSON('data/heroes/heroes.json'),
    loadJSON('data/factions/factions.json'),
    loadJSON('data/weapons/weapons.json'),
    loadJSON('data/events/events.json'),
    loadJSON('data/places/places.json'),
    loadJSON('data/critics/critics.json'),
    loadJSON('data/derivatives/derivatives.json'),
    loadJSON('data/relations/relations.json'),
    loadJSON('texts/versions/versions_index.json'),
  ]);
  DATA.baseline = baseline;
  DATA.heroes = heroes;
  DATA.factions = factions;
  DATA.weapons = weapons;
  DATA.events = events;
  DATA.places = places;
  DATA.critics = critics;
  DATA.derivatives = derivatives;
  DATA.relations = relations || [];
  DATA.idx = idx;

  renderVersions();
  renderHeroes();
  renderEvents();
  renderPlaces();
  renderWeapons();
  renderFactions();
  renderCritics();
  renderDirections();
  renderDerivatives();
  renderOntology();
  renderRelTable();
  initReader();
  initGraph();
}

/* ---------- 导航切换 ---------- */
document.querySelectorAll('.nav-links a').forEach(a=>{
  a.addEventListener('click', e=>{
    const sec = a.dataset.sec;
    // 外链（跳到 themes.html / kg.html / read.html 等）不拦截，走默认跳转
    if(!sec) return;
    e.preventDefault();
    document.querySelectorAll('.section').forEach(s=>s.classList.add('hidden'));
    const target = document.getElementById(sec);
    if(target) target.classList.remove('hidden');
    document.querySelectorAll('.nav-links a').forEach(x=>x.classList.remove('active'));
    a.classList.add('active');
    window.scrollTo({top:0, behavior:'smooth'});
  });
});

/* ---------- 版本学时间线 ---------- */
function renderVersions() {
  const v = DATA.baseline.versions;
  // 补充冀勤校注本和金批批评本
  const extra = [
    {id:'jiqin', name:'冀勤校注本（容与堂底本）', date:'2014（中央编译出版社）', chapters:100, system:'现代校注本', features:['以容与堂百回本为底本，参校天都外臣、杨定见、芥子园、贯华堂诸本','页下注释6817条，覆盖生僻词、职官、典故、方言','附录三种：容与堂四篇评论文、李贽叙、108将终局表','适合现代读者阅读的白文校注本，无夹批但注释详尽'], color:'#305060'},
    {id:'jinpi', name:'金圣叹批评本（全批语本）', date:'明崇祯十四年（1641）贯华堂本系统', chapters:70, system:'繁本·评点改造本', features:['金圣叹腰斩水浒，去招安及以后内容','含《读第五才子书法》、62篇回前总批、1937条「」夹批','伪造卢俊义惊恶梦作结，清代三百年最通行本','金氏评点思想最完整呈现，独恶宋江、骂宋江为"下下人物"'], color:'#800020'}
  ];
  const all = [...v, ...extra];
  // 排序
  const order = {'嘉靖郭勋本':1520,'天都外臣序本/容与堂本':1589,'袁无涯本':1614,'金圣叹评本':1641,'征四寇（简本）':1650,'七十回本（金圣叹评本·简体）':1950,'七十回本（金圣叹评本·繁体底本）':2000,'冀勤校注本（容与堂底本）':2014,'金圣叹批评本（全批语本）':1641};
  const html = all.map((x,i)=>`
    <div class="tl-item">
      <div class="tl-year">${shortDate(x.date)}</div>
      <div class="tl-dot"></div>
      <div class="tl-body">
        <h4 style="color:${x.color||'#8B4513'}">${x.name} <span style="color:var(--ink-muted); font-size:12px; font-weight:400; font-family:var(--font-sans);">· ${x.chapters}回 · ${x.system||''}</span></h4>
        <p>${x.features?x.features.map(f=>'• '+f).join('<br/>'):''}</p>
      </div>
    </div>
  `).join('');
  document.getElementById('versionsTimeline').innerHTML = html;
}
function shortDate(d){
  const m = d.match(/(\d{3,4})/); return m ? m[1] : (d.length<6?d:d.substring(0,6));
}

/* ---------- 108将 ---------- */
let curHeroFilter = 'all', curHeroSearch='';
function renderHeroes() {
  const grid = document.getElementById('heroGrid');
  const heroes = DATA.heroes.heroes;
  grid.innerHTML = heroes.filter(h=>{
    if (curHeroFilter==='tiangang') return h.rank<=36;
    if (curHeroFilter==='disha') return h.rank>36;
    if (['五虎将','八骠骑','步军头领','水军头领','女将'].includes(curHeroFilter)) {
      return (h.position||'').includes(curHeroFilter.replace('将','')) ||
             (curHeroFilter==='五虎将' && h.group==='五虎将') ||
             (curHeroFilter==='八骠骑' && h.group==='八骠骑') ||
             (curHeroFilter==='步军头领' && h.group==='步军头领') ||
             (curHeroFilter==='水军头领' && h.group==='水军头领') ||
             (curHeroFilter==='女将' && h.group==='女将');
    }
    if (curHeroFilter==='善终') return /善终|出家|坐化|节度使|暹罗|辞官|隐于|大笑而终|为.*臣/.test(h.end);
    if (curHeroFilter==='战死') return /战死|射死|砍死|打死|锤杀|自刎|淹死|坠崖|砸死|被.*杀/.test(h.end) && !/善终|辞官|出家/.test(h.end);
    return true;
  }).filter(h=>{
    if (!curHeroSearch) return true;
    const s = curHeroSearch.toLowerCase();
    return (h.name+h.nickname+h.star+h.origin+h.faction+h.position+h.desc).toLowerCase().includes(s);
  }).map(h=>{
    // portrait 字段带 ../ 前缀会指向 data/heroes/../ 错误路径；image 字段 img/heroes/xxx.jpg 正确
    const img = h.image || h.img;
    return `
    <div class="hero-card ${h.rank<=36?'tiangang':'disha'}" onclick="showHero(${h.id})">
      <div class="rank">${h.rank}</div>
      ${img?`<div class="avatar"><img src="${img}" alt="${h.name}" loading="lazy" onerror="this.style.display='none'"></div>`:''}
      <div class="nick">${h.star} · ${h.nickname}</div>
      <div class="nm">${h.name}</div>
      <div class="pos">${h.position}</div>
    </div>
  `;}).join('');
}
document.querySelectorAll('#heroFilters .filter-btn').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('#heroFilters .filter-btn').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    curHeroFilter = b.dataset.f;
    renderHeroes();
  });
});
document.getElementById('heroSearch').addEventListener('input', e=>{
  curHeroSearch = e.target.value; renderHeroes();
});

function showHero(id) {
  const h = DATA.heroes.heroes.find(x=>x.id===id);
  if (!h) return;
  document.getElementById('mHeader').innerHTML = `
    <div class="m-badges">
      <span>${h.star}</span><span>第${h.rank}位</span><span>${h.rank<=36?'天罡':'地煞'}</span>
      ${h.group?`<span style="background:${h.color||'#8B4513'}">${h.group}</span>`:''}
    </div>
    ${(h.image||h.img)?`<img class="m-avatar" src="${h.image||h.img}" alt="${h.name}" onerror="this.style.display='none'">`:''}
    <h2>${h.name}</h2>
    <div class="m-nick">「${h.nickname}」</div>
  `;
  document.getElementById('mBody').innerHTML = `
    <dl class="m-info">
      <dt>梁山职位</dt><dd>${h.position}</dd>
      <dt>兵器/技能</dt><dd>${h.weapon}</dd>
      <dt>上山前身份</dt><dd>${h.origin}</dd>
      <dt>所属派系</dt><dd>${h.faction}</dd>
      <dt>出场/上山</dt><dd>第${h.appear}回出场 / 第${h.up}回上山</dd>
      <dt>最终归宿</dt><dd style="color:var(--vermilion-deep); font-weight:600;">${h.end}</dd>
    </dl>
    <div class="m-desc">${h.desc}</div>
    <div class="m-deeds"><h4>主要事迹</h4><p style="font-size:14px; color:var(--ink-light);">${deedsFor(h.name)}</p></div>
  `;
  document.getElementById('heroModal').classList.add('show');
}
function deedsFor(name) {
  const map = {
    '宋江':'浔阳楼题反诗、三打祝家庄、接受招安、征方腊',
    '卢俊义':'活捉史文恭、征辽征方腊副帅、被水银毒杀',
    '吴用':'智取生辰纲、智赚卢俊义、排九宫八卦阵、自缢蓼儿洼',
    '公孙胜':'斗法破高廉、芒砀山降樊瑞、征辽前辞归',
    '林冲':'误入白虎堂、刺配沧州道、风雪山神庙、雪夜上梁山、火并王伦',
    '鲁智深':'拳打镇关西、大闹五台山、倒拔垂杨柳、大闹野猪林、六和寺坐化',
    '武松':'景阳冈打虎、斗杀西门庆、醉打蒋门神、大闹飞云浦、血溅鸳鸯楼、单臂擒方腊',
    '李逵':'江州劫法场、沂岭杀四虎、寿张乔坐衙、饮毒酒共宋江死',
    '杨志':'杨志卖刀、押送生辰纲、夺宝珠寺',
    '花荣':'大闹清风寨、梁山射雁、对影山射戟、神箭射红灯',
    '燕青':'智扑擎天柱、月夜遇道君、功成身退',
    '张顺':'魂断涌金门、金华太保成神'
  };
  return map[name] || '梁山聚义、南征北战，一百单八位好汉聚义梁山、替天行道';
}
function closeModal(){ document.getElementById('heroModal').classList.remove('show'); }
document.getElementById('heroModal').addEventListener('click', e=>{
  if (e.target.id==='heroModal') closeModal();
});

/* ---------- 事件时间轴 ---------- */
function renderEvents() {
  const el = document.getElementById('eventList');
  el.innerHTML = DATA.events.events.map(e=>{
    const stars = e.weight;
    return `
    <div class="event-item">
      <div class="event-hui">
        <div class="hnum">第${e.hui}回</div>
        <div class="hph">${e.phase}</div>
      </div>
      <div class="event-body">
        <h4>${e.name}</h4>
        <div class="emeta"><span class="ev-star">${stars}</span> · ${e.place} · ${e.type}</div>
        <p>${e.desc}</p>
      </div>
    </div>`;
  }).join('');
}

/* ---------- 地理空间 ---------- */
function renderPlaces() {
  const pts = document.getElementById('placePoints');
  const list = document.getElementById('placeList');
  const W=1100, H=740;
  // 投影：扩大画布与范围（lon 103-125, lat 26-43），让中原核心区点位拉开
  function proj(lon,lat){
    const x = ((lon-103)/22)*1040+30;
    const y = ((43-lat)/17)*680+30;
    return [x,y];
  }
  // 按类型决定圆点大小与颜色
  const typeStyle = {
    '聚义地':       {r:12, fill:'#8B1A1A', big:true},
    '都城':         {r:10, fill:'#B8860B', big:true},
    '陪都':         {r:9,  fill:'#DAA520'},
    '州府':         {r:7,  fill:'#8A9A3C'},
    '县治':         {r:6,  fill:'#7B5E3B'},
    '战场':         {r:7,  fill:'#8B1A1A'},
    '敌国':         {r:9,  fill:'#5C4B6B'},
    '叛王地盘':     {r:9,  fill:'#4F6B3A'},
    '山寨':         {r:8,  fill:'#3A5B7A'},
    '庄园':         {r:6,  fill:'#7A3A4F'},
    '村落':         {r:6,  fill:'#5B4B6B'},
    '事件地':       {r:6,  fill:'#C48640'},
    '英雄地':       {r:7,  fill:'#B22222'},
    '黑店地':       {r:6,  fill:'#4B3B3B'},
    '配军地':       {r:6,  fill:'#5C7F4F'},
    '流放地':       {r:7,  fill:'#2E5C7F'},
    '酒楼':         {r:5,  fill:'#8B1A1A'},
    '市集':         {r:5,  fill:'#C48640'},
    '建筑':         {r:5,  fill:'#3A4A5C'},
    '险地':         {r:6,  fill:'#2E4A3F'},
    '佛刹':         {r:7,  fill:'#B8860B'},
    '终局地':       {r:8,  fill:'#1A3A5C'},
    '终局寺':       {r:7,  fill:'#1A3A5C'},
    '任所':         {r:6,  fill:'#3A4A5C'},
    '江湖势力':     {r:6,  fill:'#7B4A2E'},
  };
  // 对重叠点做像素级微调（dx,dy 像素）+ 标签锚点方向
  // anchor: 'r'=标签在右,'l'=左,'t'=上,'b'=下,'tr'=右上,'tl'=左上,'br'=右下,'bl'=左下
  // 原则：①保留真实地理关系 ②同城/同山寨"子景点"偏移 8-18px 即可
  //       ③梁山核心团簇（半径 40km 内 10 个点）向四周扇形散开，位移不超过 28px
  const override = {
    // 梁山泊（中心锚定）
    '梁山泊':     {dx:0,   dy:0,   anchor:'b'},
    '忠义堂':     {dx:14,  dy:-12, anchor:'tr'},
    // 郓城方向（梁山西南）
    '郓城县':     {dx:-24, dy:10,  anchor:'bl'},
    // 黄泥冈（郓城东南，梁山西南偏东）
    '黄泥冈':     {dx:4,   dy:-20, anchor:'t'},
    // 祝家庄（梁山南独龙岗）
    '祝家庄':     {dx:6,   dy:20,  anchor:'b'},
    // 扈家庄（祝家庄西侧）
    '扈家庄':     {dx:-20, dy:8,   anchor:'l'},
    // 阳谷县+景阳冈（梁山西北）
    '阳谷县':     {dx:-30, dy:-8,  anchor:'tl'},
    '景阳冈':     {dx:-8,  dy:20,  anchor:'bl'},
    // 曾头市（梁山北偏东凌州）
    '曾头市':     {dx:12,  dy:-20, anchor:'t'},
    // 高唐州（梁山北偏东）
    '高唐州':     {dx:24,  dy:-16, anchor:'tr'},
    // 桃花山/二龙山/清风寨/白虎山（青州片区，错落排开）
    '桃花山':     {dx:-22, dy:4,   anchor:'l'},
    '二龙山':     {dx:0,   dy:-16, anchor:'t'},
    '清风寨':     {dx:18,  dy:-12, anchor:'tr'},
    '白虎山':     {dx:14,  dy:10,  anchor:'br'},
    // 柴家庄（沧州南）+ 沧州
    '沧州':       {dx:0,   dy:-10, anchor:'t'},
    '柴家庄':     {dx:-20, dy:20,  anchor:'bl'},
    // 孟州一城四景（十字坡/快活林/鸳鸯楼围绕孟州散开）
    '孟州':       {dx:0,   dy:0,   anchor:'b'},
    '十字坡':     {dx:-24, dy:-20, anchor:'tl'},
    '快活林':     {dx:16,  dy:-14, anchor:'tr'},
    '鸳鸯楼':     {dx:22,  dy:18,  anchor:'br'},
    // 江州（浔阳楼江边/揭阳镇对岸）
    '江州':       {dx:-10, dy:0,   anchor:'l'},
    '浔阳楼':     {dx:14,  dy:-10, anchor:'tr'},
    '揭阳岭/镇':  {dx:0,   dy:22,  anchor:'b'},
    // 大相国寺（开封城内东南）
    '东京开封府': {dx:0,   dy:0,   anchor:'b'},
    '大相国寺':   {dx:-18, dy:14,  anchor:'bl'},
    // 野猪林（开封往沧州道上）
    '野猪林':     {dx:-16, dy:-14, anchor:'tl'},
    // 楚州-蓼儿洼
    '楚州':       {dx:-12, dy:0,   anchor:'l'},
    '蓼儿洼':     {dx:14,  dy:-10, anchor:'tr'},
    // 杭州-六和寺
    '杭州':       {dx:-10, dy:-8,  anchor:'tl'},
    '六和寺':     {dx:18,  dy:-8,  anchor:'tr'},
    // 睦州/乌龙岭/方腊
    '睦州 / 清溪':{dx:-12, dy:12,  anchor:'bl'},
    '乌龙岭':     {dx:0,   dy:-14, anchor:'t'},
    '江南方腊':   {dx:18,  dy:10,  anchor:'br'},
    // 少华山/华州/史家村
    '少华山':     {dx:12,  dy:-10, anchor:'tr'},
    '华州':       {dx:-12, dy:0,   anchor:'l'},
    '史家村':     {dx:-24, dy:20,  anchor:'bl'},
    // 其他
    '渭州':       {dx:8,   dy:0,   anchor:'r'},
    '五台山':     {dx:0,   dy:0,   anchor:'b'},
    '大名府':     {dx:-14, dy:0,   anchor:'l'},
    '蓟州':       {dx:0,   dy:-10, anchor:'t'},
    '登州':       {dx:12,  dy:-8,  anchor:'tr'},
    '沂水县':     {dx:0,   dy:14,  anchor:'b'},
    '辽国':       {dx:-8,  dy:-4,  anchor:'r'},
    '芒砀山':     {dx:0,   dy:14,  anchor:'b'},
    '河北田虎':   {dx:0,   dy:-14, anchor:'t'},
    '淮西王庆':   {dx:0,   dy:14,  anchor:'b'},
    '润州':       {dx:0,   dy:4,   anchor:'r'},
  };
  const coordFix = {}; // 地理错误已直接修正到 places.json 中
  // 渲染：先算初始位置 → 标签自动避让（松弛）→ 生成 SVG（带引线）
  const DIR = {r:[1,0,'start'], l:[-1,0,'end'], t:[0,-1,'middle'], b:[0,1,'middle'],
               tr:[0.72,-0.72,'start'], tl:[-0.72,-0.72,'end'],
               br:[0.72,0.72,'start'],  bl:[-0.72,0.72,'end']};
  const nodes = DATA.places.places.map(p=>{
    const [lon,lat] = coordFix[p.name] || p.coord;
    let [x,y] = proj(lon,lat);
    const ov = override[p.name] || {};
    x += (ov.dx||0); y += (ov.dy||0);
    const st = typeStyle[p.type] || {r:6, fill:'#5C4B3A'};
    const big = !!st.big;
    const r = st.r;
    const off = r + (big?9:7);
    const d = DIR[ov.anchor || 'r'];
    return {name:p.name, desc:p.desc, x, y, _ox:x, _oy:y, r, fill:st.fill,
            big, fontS: big?13:11, fw: big?700:500,
            anchor: ov.anchor || 'r', base: ov.anchor || 'r',
            ix: x + d[0]*off, iy: y + d[1]*off,
            lx: x + d[0]*off, ly: y + d[1]*off};
  });
  function reposition(n, anchor){
    n.anchor = anchor;
    const d = DIR[anchor];
    const off = n.r + (n.big?9:7);
    n.ix = n.x + d[0]*off; n.iy = n.y + d[1]*off;
    n.lx = n.ix; n.ly = n.iy;
  }
  function geom(n){
    const ta = DIR[n.anchor][2];
    const w = n.name.length*n.fontS*0.98 + 4;
    const h = n.fontS*1.2;
    const x0 = ta==='start' ? n.lx : (ta==='end' ? n.lx-w : n.lx-w/2);
    const y0 = n.ly - h/2;
    return {x0, y0, w, h, ta, cx:x0+w/2, cy:y0+h/2};
  }
  function rectArea(A,B){
    const ox = Math.min(A.x0+A.w, B.x0+B.w) - Math.max(A.x0, B.x0);
    const oy = Math.min(A.y0+A.h, B.y0+B.h) - Math.max(A.y0, B.y0);
    return (ox>0 && oy>0) ? ox*oy : 0;
  }
  function dotHit(A, m){
    const qx = Math.max(A.x0, Math.min(m.x, A.x0+A.w));
    const qy = Math.max(A.y0, Math.min(m.y, A.y0+A.h));
    const d = Math.hypot(qx-m.x, qy-m.y);
    const R = m.r + 2.5;
    return d < R ? (R-d)*(R-d) : 0;
  }
  // ⓪ 圆点互斥：同城/近邻点先散开（位移 ≤34px，保留地理关系）
  for(let it=0; it<260; it++){
    let moved = 0;
    for(let a=0; a<nodes.length; a++) for(let b=a+1; b<nodes.length; b++){
      const A=nodes[a], B=nodes[b];
      let dx=A.x-B.x, dy=A.y-B.y, d=Math.hypot(dx,dy);
      const need = A.r + B.r + 2.5;
      if(d < need){
        if(d<0.01){ dx=(a<b?1:-1); dy=0.6; d=Math.hypot(dx,dy); }
        const push=(need-d)/2, ux=dx/d, uy=dy/d;
        A.x+=ux*push; A.y+=uy*push; B.x-=ux*push; B.y-=uy*push;
        moved++;
      }
    }
    nodes.forEach(n=>{
      const ddx=n.x-n._ox, ddy=n.y-n._oy, dd=Math.hypot(ddx,ddy);
      if(dd>34){ n.x=n._ox+ddx/dd*34; n.y=n._oy+ddy/dd*34; }
    });
    if(!moved) break;
  }
  nodes.forEach(n=>reposition(n, n.base));

  // ① 贪心锚点：按「大点优先」顺序，为每个标签在 8 个方向中挑压盖最少者
  const order = nodes.slice().sort((a,b)=>(b.r-a.r)||(b.fontS-a.fontS));
  const placed = [];
  order.forEach(n=>{
    let best = null;
    for(const key of ['r','l','t','b','tr','tl','br','bl']){
      reposition(n, key);
      const g = geom(n);
      let cost = 0;
      placed.forEach(b=>{ cost += rectArea(g,b)*1.0; });
      for(const m of nodes){ if(m!==n) cost += dotHit(g,m)*2.4; }
      if(!best || cost < best.cost) best = {key, cost};
    }
    reposition(n, best.key);
    placed.push(geom(n));
  });
  // ② 松弛：标签互斥 + 标签避让圆点 + 轻微回弹（保持地理真实）
  const px = new Array(nodes.length).fill(0), py = new Array(nodes.length).fill(0);
  for(let it=0; it<600; it++){
    const G = nodes.map(geom);
    px.fill(0); py.fill(0);
    for(let a=0; a<nodes.length; a++) for(let b=a+1; b<nodes.length; b++){
      const A=G[a], B=G[b];
      const ox = Math.min(A.x0+A.w, B.x0+B.w) - Math.max(A.x0, B.x0);
      const oy = Math.min(A.y0+A.h, B.y0+B.h) - Math.max(A.y0, B.y0);
      if(ox>0 && oy>0){
        if(ox < oy){ const s=(ox/2+0.35)*(A.x0<B.x0?1:-1); px[a]-=s; px[b]+=s; }
        else       { const s=(oy/2+0.35)*(A.y0<B.y0?1:-1); py[a]-=s; py[b]+=s; }
      }
    }
    for(let a=0; a<nodes.length; a++){
      const A=G[a];
      for(let b=0; b<nodes.length; b++){
        if(a===b) continue;
        const m=nodes[b];
        const qx=Math.max(A.x0, Math.min(m.x, A.x0+A.w));
        const qy=Math.max(A.y0, Math.min(m.y, A.y0+A.h));
        let vx=qx-m.x, vy=qy-m.y;
        let dist=Math.hypot(vx,vy);
        const R=m.r+3;
        if(dist<R){
          if(dist<0.01){
            const left=m.x-A.x0, right=A.x0+A.w-m.x, up=m.y-A.y0, down=A.y0+A.h-m.y;
            const mn=Math.min(left,right,up,down);
            if(mn===left){vx=-1;vy=0;} else if(mn===right){vx=1;vy=0;}
            else if(mn===up){vx=0;vy=-1;} else {vx=0;vy=1;}
            dist=0.5;
          }
          const pen=R-dist;
          px[a]+=vx/dist*pen*0.9; py[a]+=vy/dist*pen*0.9;
        }
      }
    }
    for(let a=0; a<nodes.length; a++){
      const n=nodes[a];
      px[a] += (n.ix-n.lx)*0.03; py[a] += (n.iy-n.ly)*0.03;
      n.lx += px[a]*0.42; n.ly += py[a]*0.42;
      const ddx=n.lx-n.x, ddy=n.ly-n.y, d=Math.hypot(ddx,ddy);
      if(d>58){ n.lx=n.x+ddx/d*58; n.ly=n.y+ddy/d*58; }
    }
  }
  const items = nodes.map(n=>{
    const g = geom(n);
    const dist = Math.hypot(n.lx-n.ix, n.ly-n.iy);
    const leader = dist>7
      ? `<line x1="${n.x}" y1="${n.y}" x2="${n.lx}" y2="${n.ly}" stroke="${n.fill}" stroke-width=".8" opacity=".42"/>`
      : '';
    return `<g class="place-dot" data-name="${n.name}">
      <circle cx="${n.x}" cy="${n.y}" r="${n.r}" fill="${n.fill}" stroke="#fff" stroke-width="2" opacity=".95">
        <title>${n.name}：${n.desc}</title>
      </circle>
      ${leader}
      <text x="${n.lx}" y="${n.ly}" text-anchor="${g.ta}" font-size="${n.fontS}" fill="${n.fill}" font-family="serif" font-weight="${n.fw}" dominant-baseline="middle"
            stroke="#fff" stroke-width="3" paint-order="stroke" class="place-label">${n.name}</text>
    </g>`;
  }).join('');

  // 梁山聚义核心连线：以梁山泊为中心连到主要州府（淡线装饰）
  const _li = DATA.places.places.find(p=>p.name==='梁山泊');
  const [bcx,bcy] = proj(_li.coord[0], _li.coord[1]);
  const corePlaces = ['东京开封府','沧州','江州','大名府','蓟州','登州','杭州','华州','渭州','孟州','沂水县'];
  const lines = corePlaces.map(n=>{
    const p = DATA.places.places.find(x=>x.name===n); if(!p) return '';
    const [lon,lat]=coordFix[n]||p.coord;
    let [x,y]=proj(lon,lat);
    const ov=override[n]||{}; x+=ov.dx||0; y+=ov.dy||0;
    return `<path d="M${bcx},${bcy} Q${(bcx+x)/2},${(bcy+y)/2-20} ${x},${y}" fill="none" stroke="#8B1A1A" stroke-width="0.6" opacity=".18"/>`;
  }).join('');

  pts.innerHTML = lines + items;

  list.innerHTML = DATA.places.places.map(p=>`
    <div class="place-item" data-name="${p.name}">
      <div class="pn">${p.name}</div>
      <div class="pt">${p.type} · ${p.today||'—'} · 关联：${(p.assoc||[]).join('、')}</div>
    </div>
  `).join('');

  // 悬停联动：列表/圆点互高亮
  const dots = pts.querySelectorAll('.place-dot');
  const items2 = list.querySelectorAll('.place-item');
  function highlight(name){
    dots.forEach(g=>{
      const c = g.querySelector('circle');
      const t = g.querySelector('text');
      if(g.dataset.name===name){
        c.setAttribute('r', parseFloat(c.getAttribute('r'))+3);
        c.setAttribute('stroke','var(--vermilion)');
        c.setAttribute('stroke-width','3');
        t.setAttribute('font-weight','700');
      } else {
        c.style.opacity='.3'; t.style.opacity='.35';
      }
    });
    items2.forEach(it=>{
      it.style.background = it.dataset.name===name ? 'var(--paper-warm)' : '#fff';
      it.style.borderColor = it.dataset.name===name ? 'var(--vermilion)' : 'var(--border)';
    });
  }
  function reset(){
    dots.forEach(g=>{
      const c = g.querySelector('circle');
      const t = g.querySelector('text');
      const st = typeStyle[DATA.places.places.find(p=>p.name===g.dataset.name)?.type] || {};
      c.setAttribute('r', st.r||6);
      c.setAttribute('stroke','#fff');
      c.setAttribute('stroke-width','2');
      c.style.opacity=''; t.style.opacity='';
      t.setAttribute('font-weight', st.big?700:500);
    });
    items2.forEach(it=>{ it.style.background='#fff'; it.style.borderColor='var(--border)'; });
  }
  dots.forEach(g=>{
    g.addEventListener('mouseenter',()=>highlight(g.dataset.name));
    g.addEventListener('mouseleave',reset);
  });
  items2.forEach(it=>{
    it.addEventListener('mouseenter',()=>highlight(it.dataset.name));
    it.addEventListener('mouseleave',reset);
  });
}

/* ---------- 兵器 ---------- */
function renderWeapons() {
  document.getElementById('weaponGrid').innerHTML = DATA.weapons.weapons.map(w=>`
    <div class="weapon-card" style="border-left-color:${w.color||'var(--vermilion)'}">
      <h4>${w.name}</h4>
      <div class="wmeta">使用者：${w.user} · ${w.category} · ${w.weight}</div>
      <p>${w.desc}</p>
    </div>
  `).join('');
}

/* ---------- 派系 ---------- */
function renderFactions() {
  const heroMap = {};
  DATA.heroes.heroes.forEach(h=>heroMap[h.id]=h);
  document.getElementById('factionChart').innerHTML = DATA.factions.factions.map(f=>`
    <div class="faction-card" style="border-top:4px solid ${f.color};">
      <div style="position:absolute; top:10px; right:14px; font-family:var(--font-serif); font-size:22px; color:${f.color}; opacity:.3;">${f.count}人</div>
      <h4>${f.name}</h4>
      <div class="fmeta">${f.count}位好汉</div>
      <p>${f.desc}</p>
      <div class="faction-avatars">
        ${f.core.map(c=>`<span>${heroMap[c.id]?.nickname||''}${heroMap[c.id]?.name||''}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

/* ---------- 评点家 ---------- */
function renderCritics() {
  document.getElementById('criticGrid').innerHTML = DATA.critics.critics.map(c=>`
    <div class="critic-card" style="border-top:4px solid ${c.color};">
      <div class="cc-era">${c.era}</div>
      <h3>${c.name}</h3>
      <div class="cc-work">${c.work}</div>
      <p><b style="color:var(--gold);">学派：</b>${c.school}<br/><b style="color:var(--gold);">核心观点：</b>${c.core_view}</p>
      <p style="font-size:13px; line-height:1.8;">${c.desc}</p>
      ${c.key_quotes && c.key_quotes[0]?`<blockquote>"${c.key_quotes[0]}"</blockquote>`:''}
      <div style="margin-top:8px; font-size:12px; color:var(--gold);">影响力：${c.influence||'★★★★'}</div>
    </div>
  `).join('');
}
function renderDirections() {
  document.getElementById('directionGrid').innerHTML = DATA.critics.research_directions.map(d=>`
    <div class="card">
      <span class="badge" style="background:var(--indigo);">${d.id}</span>
      <h3>${d.name}</h3>
      <div class="meta">核心议题 ${d.key_issues.length}项</div>
      <div class="desc">
        <b>核心问题：</b>${d.core}<br/>
        <b>关键问题：</b>${d.key_issues.join('；')}<br/>
        <b>代表学者：</b>${d.main_scholars.join('、')}
      </div>
    </div>
  `).join('');
}

/* ---------- 衍生作品 ---------- */
function renderDerivatives() {
  const tabs = {seq:['seq01','seq02','seq03','seq04','seq05'], tv:['mv01','mv02','mv03','mv04','mv07','mv08','mv09'], op:['op01','op02','op03','op04','op05'], game:['game01','game02','game03','game04','anime01','comic01','comic02','mv05','mv06']};
  const typeName = {mv01:'电视剧',mv02:'电视剧',mv03:'电视剧',mv04:'人物剧',mv05:'电影',mv06:'电影',mv07:'电视剧',mv08:'少儿剧',mv09:'衍生剧',op01:'京剧',op02:'京剧',op03:'京剧',op04:'戏曲',op05:'昆曲',game01:'街机游戏',game02:'网游',game03:'手游',game04:'网游',anime01:'日本动画',comic01:'日本漫画',comic02:'港漫',seq01:'续书',seq02:'反水浒续书',seq03:'转世续书',seq04:'民国续书',seq05:'抗战续书'};
  Object.keys(tabs).forEach(t=>{
    document.getElementById('derGrid-'+t).innerHTML = tabs[t].map(id=>{
      const d = DATA.derivatives.derivatives.find(x=>x.id===id);
      if(!d) return '';
      return `<div class="card" style="border-top:3px solid ${d.color||'var(--vermilion)'};">
        <span class="badge" style="background:${d.color||'var(--vermilion)'};">${typeName[id]}</span>
        <h3>${d.name} <span style="font-size:13px; color:var(--ink-muted); font-weight:400;">(${d.year})</span></h3>
        <div class="meta">${d.director||d.creator||d.author||''}${d.cast?' · '+d.cast.substring(0,30)+(d.cast.length>30?'…':''):''}</div>
        <div class="desc">${d.core_features}</div>
        ${d.rating?`<div style="margin-top:10px; font-size:12px; color:var(--gold);">评分 ${d.rating}/10</div>`:''}
        ${d.influence?`<div style="margin-top:10px; font-size:12px; color:var(--gold);">影响力 ${d.influence}</div>`:''}
      </div>`;
    }).join('');
  });
  document.querySelectorAll('#derTabBar .tab-btn').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('#derTabBar .tab-btn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
      document.getElementById('tab-'+b.dataset.tab).classList.add('active');
    });
  });
}

/* ---------- 本体模型 ---------- */
function renderOntology() {
  const classes = [
    {icon:'📖', name:'文学作品类', sub:'繁本系统、简本系统、评点改造本、续书衍生本', props:'版本ID、刊刻年代、刊刻机构、存世状态、底本来源、回数'},
    {icon:'👤', name:'人物类', sub:'梁山好汉、朝廷官员、民间角色、妖道僧俗', props:'姓名、绰号、星宿、座次、登场回、死亡回、阵营、武器、结局'},
    {icon:'⚔️', name:'事件类', sub:'个人事件、群体事件、战争事件、结局事件', props:'事件ID、发生回目、时间线、参与人物、地点、情节权重'},
    {icon:'🗺️', name:'空间类', sub:'故事虚构地点、历史真实地点、当代坐标', props:'地名、所属州府、经纬度、关联事件、遗存状态'},
    {icon:'🎓', name:'学术主体类', sub:'古代评点家、近现代学者、研究机构', props:'姓名、生卒年、流派、研究方向、代表论著'},
    {icon:'📚', name:'学术成果类', sub:'评点本、研究论著、学术论文、会议成果', props:'成果ID、年份、核心观点、引用文献、方向'},
    {icon:'🎬', name:'衍生作品类', sub:'影视、戏曲、动漫、游戏改编', props:'作品名、改编类型、年份、改编特征、主创团队'}
  ];
  document.getElementById('ontoGrid').innerHTML = classes.map(c=>`
    <div class="onto-card">
      <div class="oc-icon">${c.icon}</div>
      <h4>${c.name}</h4>
      <p>${c.sub}</p>
      <ul><li>${c.props.split('、').join('</li><li>')}</li></ul>
    </div>
  `).join('');
}
function renderRelTable() {
  const rels = [
    ['人物-人物','结拜为兄弟','人物→人物','结义回目、排序权重'],
    ['人物-人物','敌对','人物→人物','首次冲突回目、冲突强度'],
    ['人物-人物','师徒','人物→人物','授艺内容、登场回目'],
    ['人物-人物','上下级','人物→人物','从属时间、官职属性'],
    ['人物-人物','主仆/恩义','人物→人物','关系来源、忠义级别'],
    ['人物-人物','夫妇','人物→人物','结合回目、结局'],
    ['人物-事件','参与','人物→事件','角色定位、情节权重'],
    ['人物-地点','活动于','人物→地点','停留回目、事件关联'],
    ['版本-人物','登场于','版本→人物','人物结局差异、文本异文'],
    ['版本-事件','收录于','版本→事件','情节删改特征、文字异文'],
    ['版本-版本','演化自','版本→版本','刊刻时间差、文本承袭度'],
    ['学者-成果','创作','学术主体→成果','发表时间、核心观点'],
    ['学者-学者','学术论战','学术主体→学术主体','论战主题、时间'],
    ['版本-学者','研究','版本→学术主体','研究成果、核心考证'],
    ['事件-地点','发生于','事件→地点','事件时间、地理坐标'],
    ['衍生作品-版本','改编自','衍生→文学作品','改编幅度、情节改动'],
    ['人物-兵器','惯用','人物→兵器','使用回目、战绩'],
    ['评点家-回目','评点于','评点家→回目','评语类型、核心观点']
  ];
  document.getElementById('relTable').innerHTML = rels.map(r=>`
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:10px 14px; color:var(--vermilion); font-family:var(--font-serif);">${r[0]}</td>
      <td style="padding:10px 14px; font-weight:600;">${r[1]}</td>
      <td style="padding:10px 14px; color:var(--ink-muted); font-family:monospace;">${r[2]}</td>
      <td style="padding:10px 14px; font-size:12px; color:var(--ink-light);">${r[3]}</td>
    </tr>
  `).join('');
}

/* ---------- 关系图谱（Canvas力导向） ---------- */
function initGraph() {
  const canvas = document.getElementById('graphCanvas');
  const wrap = document.getElementById('graph-wrap');
  function resize(){
    canvas.width = wrap.clientWidth;
    canvas.height = wrap.clientHeight;
  }
  resize(); window.addEventListener('resize', resize);

  const ctx = canvas.getContext('2d');
  const heroMap = {};
  DATA.heroes.heroes.forEach(h=>heroMap[h.id]=h);
  // 派系颜色
  const factionColor = id=>{
    for(const f of DATA.factions.factions){
      if(f.core.some(c=>c.id===id)) return f.color;
    }
    return '#888';
  };
  // 取关键节点：前36天罡+若干代表人物
  const keyIds = new Set([1,2,3,4,5,6,7,8,9,10,12,13,14,15,16,17,18,19,20,22,23,24,25,26,27,28,30,31,32,33,36,39,58,59,107,101]);
  const nodes = DATA.heroes.heroes.filter(h=>keyIds.has(h.id)).map(h=>({
    id:h.id, name:h.name, nick:h.nickname, r: h.rank<=10?18 : (h.rank<=24?14:11),
    x: canvas.width/2 + (Math.random()-0.5)*300,
    y: canvas.height/2 + (Math.random()-0.5)*200,
    vx:0, vy:0, color:factionColor(h.id)
  }));
  const idMap={}; nodes.forEach(n=>idMap[n.id]=n);
  const edges = DATA.relations.filter(r=>idMap[r.from] && idMap[r.to]).map(r=>({
    a:idMap[r.from], b:idMap[r.to], type:r.type, w:r.weight||5
  }));

  let dragNode=null;
  canvas.addEventListener('mousedown', e=>{
    const rect=canvas.getBoundingClientRect();
    const mx=e.clientX-rect.left, my=e.clientY-rect.top;
    for(const n of nodes){
      if((mx-n.x)**2+(my-n.y)**2 < n.r*n.r){ dragNode=n; break; }
    }
  });
  canvas.addEventListener('mousemove', e=>{
    if(!dragNode) return;
    const rect=canvas.getBoundingClientRect();
    dragNode.x = e.clientX-rect.left;
    dragNode.y = e.clientY-rect.top;
    dragNode.vx=0; dragNode.vy=0;
  });
  canvas.addEventListener('mouseup', ()=>dragNode=null);
  canvas.addEventListener('dblclick', ()=>{ nodes.forEach(n=>{n.x=canvas.width/2+(Math.random()-0.5)*300; n.y=canvas.height/2+(Math.random()-0.5)*200; n.vx=n.vy=0;}); });

  function step(){
    // 斥力
    for(let i=0;i<nodes.length;i++){
      for(let j=i+1;j<nodes.length;j++){
        const a=nodes[i], b=nodes[j];
        let dx=a.x-b.x, dy=a.y-b.y;
        let d=Math.sqrt(dx*dx+dy*dy)||1;
        const f=800/(d*d);
        const fx=dx/d*f, fy=dy/d*f;
        a.vx+=fx; a.vy+=fy; b.vx-=fx; b.vy-=fy;
      }
    }
    // 弹力
    for(const e of edges){
      let dx=e.a.x-e.b.x, dy=e.a.y-e.b.y;
      let d=Math.sqrt(dx*dx+dy*dy)||1;
      const rest = 80 + (10-e.w)*8;
      const f=(d-rest)*0.02;
      const fx=dx/d*f, fy=dy/d*f;
      e.a.vx-=fx; e.a.vy-=fy; e.b.vx+=fx; e.b.vy+=fy;
    }
    // 向心
    nodes.forEach(n=>{
      n.vx += (canvas.width/2 - n.x)*0.002;
      n.vy += (canvas.height/2 - n.y)*0.002;
      n.vx*=0.88; n.vy*=0.88;
      n.x += n.vx; n.y += n.vy;
      n.x=Math.max(n.r, Math.min(canvas.width-n.r, n.x));
      n.y=Math.max(n.r, Math.min(canvas.height-n.r, n.y));
    });
    // 绘制
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle='rgba(139,26,26,.12)';
    ctx.lineWidth=1;
    edges.forEach(e=>{
      ctx.beginPath();
      ctx.moveTo(e.a.x,e.a.y);
      ctx.lineTo(e.b.x,e.b.y);
      ctx.stroke();
    });
    nodes.forEach(n=>{
      ctx.beginPath();
      ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
      ctx.fillStyle = n.color || 'var(--vermilion)';
      ctx.fill();
      ctx.strokeStyle='#fff';
      ctx.lineWidth=2;
      ctx.stroke();
      ctx.fillStyle='#fff';
      ctx.font = 'bold '+ (n.r>14?12:10) +'px serif';
      ctx.textAlign='center';
      ctx.textBaseline='middle';
      ctx.fillText(n.name, n.x, n.y);
    });
    requestAnimationFrame(step);
  }
  step();
}

/* ---------- 阅读器 ---------- */
let RD = { ver:'v120', chap:0, lang:'fan', comment:'all', data:null, chapters:[], comments:[], notes:[] };
function initReader() {
  const verSelect = document.getElementById('verSelect');
  const statusEl = document.getElementById('readerStatus');
  if(!DATA.idx || !DATA.idx.versions) { statusEl.textContent='版本索引加载失败，请刷新页面重试'; return; }
  // 默认选第一个可用版本
  if(!DATA.idx.versions.find(v=>v.id===RD.ver)) RD.ver = DATA.idx.versions[0].id;
  verSelect.innerHTML = DATA.idx.versions.map(v=>`<option value="${v.id}">${v.name}（${v.count||'?'}回）</option>`).join('');
  verSelect.value = RD.ver;
  verSelect.addEventListener('change', ()=>{ RD.ver=verSelect.value; RD.chap=0; loadChapter(); });
  document.getElementById('chapSelect').addEventListener('change', e=>{ RD.chap=+e.target.value; loadChapter(); });
  document.querySelectorAll('[data-lang]').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('[data-lang]').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      RD.lang=b.dataset.lang; loadChapter();
    });
  });
  document.getElementById('commentSelect').addEventListener('change', e=>{ RD.comment=e.target.value; loadChapter(); });
  document.getElementById('prevBtn').addEventListener('click',()=>{ if(RD.chap>0){RD.chap--; loadChapter();} });
  document.getElementById('nextBtn').addEventListener('click',()=>{ if(RD.chap<RD.chapters.length-1){RD.chap++; loadChapter();} });
  loadChapter();
}

async function loadChapter() {
  const status = document.getElementById('readerStatus');
  const content = document.getElementById('readerContent');
  const ver = DATA.idx.versions.find(v=>v.id===RD.ver);
  if(!ver) { status.textContent='未找到对应版本'; return; }
  status.innerHTML = '<span style="color:var(--gold);">●</span> 正在加载章节数据……';
  // 加载章节列表JSON
  if(!RD.data || RD.data._id !== RD.ver) {
    const listPath = `texts/versions/${RD.ver}/chapters.json`;
    let raw = await loadJSON(listPath);
    if(!raw) raw = [];
    // chapters.json 可能是 {chapters:[...]} 对象，也可能直接是数组
    if(Array.isArray(raw)){ RD.chapters = raw; }
    else { RD.chapters = raw.chapters || []; }
    RD.data = {_id:RD.ver, chapters:RD.chapters};
    // 填充回目下拉
    const sel = document.getElementById('chapSelect');
    sel.innerHTML = RD.chapters.map((c,i)=>`<option value="${i}">${c.title}</option>`).join('');
    // 批注
    RD.comments = await loadJSON(`texts/versions/${RD.ver}/comments.json`) || [];
    RD.notes = await loadJSON(`texts/versions/${RD.ver}/notes.json`) || [];
  }
  if(RD.chap >= RD.chapters.length) RD.chap = RD.chapters.length-1;
  document.getElementById('chapSelect').value = RD.chap;
  const chap = RD.chapters[RD.chap];
  if(!chap) { status.innerHTML = '章节列表为空，请切换版本'; content.innerHTML='<p style="text-align:center;color:var(--ink-muted);padding:60px;">本版本暂无章节数据。</p>'; return; }

  const langName = {fan:'繁体原文',jian:'简体原文',bai:'白话译文'}[RD.lang];
  status.innerHTML = `当前语体：<b style="color:var(--vermilion-deep);">${langName}</b> · 版本：<b>${ver.name}</b> · ${chap.title} · 约${chap.size||'?'}字`;

  // 加载文本文件（chap.file 已带 fan/jian/bai 前缀，按语体选对应字段）
  const fileKey = RD.lang==='fan'?'file':(RD.lang==='jian'?'file_simp':'file_bai');
  const subPath = chap[fileKey] || chap.file;
  const filePath = `texts/versions/${RD.ver}/${subPath}`;
  try {
    const r = await fetch(filePath);
    if(!r.ok) throw new Error('HTTP '+r.status);
    const txt = await r.text();
    renderChapter(txt, chap);
    applyExtraComments(chap);
  } catch(e) {
    console.warn('load chapter fail:', filePath, e);
    document.getElementById('readerContent').innerHTML = '<p style="text-align:center; color:var(--ink-muted); padding:60px;">本回文本加载失败。部分版本可能仅部分回目支持白话/繁体。<br><small style="color:#c00;">路径：'+filePath+'</small></p>';
    status.innerHTML = '加载失败：'+filePath;
  }
}

function renderChapter(txt, chap) {
  const content = document.getElementById('readerContent');
  const notesBox = document.getElementById('readerNotes');
  let html = `<h2 class="ch-title">${chap.title}</h2>`;
  // 回前总批（金圣叹）
  if(RD.comment!=='none' && (RD.comment==='all'||RD.comment==='jin') && chap.zongpi) {
    html += `<div class="zongpi"><b style="color:var(--gold);">【金圣叹回前总批】</b><br/>${chap.zongpi}</div>`;
  }
  // 正文分段
  const lines = txt.split(/\n+/);
  let verseBuf = [];
  const flushVerse = ()=>{ if(verseBuf.length){ html += `<p class="verse">${verseBuf.join('<br/>')}</p>`; verseBuf=[]; } };
  lines.forEach(line=>{
    line = line.trim();
    if(!line) return;
    if(/^[《【]/ || /[，。；？！]$/.test(line)===false && /^[^\u4e00-\u9fa5]*[a-zA-Z\u4e00-\u9fa5\s，。、：；]{3,20}$/.test(line) && line.length<40) {
      // 诗句/韵文
      if(/^[诗偈词赋歌]曰|^古风|^七言|^五言|^临江仙|^念奴娇|^满庭芳|^沁园春|^西江月|^鹧鸪天|^清平乐/.test(line)) { verseBuf.push(line); return; }
      if(verseBuf.length>0 && line.length<30) { verseBuf.push(line); return; }
      flushVerse();
    } else { flushVerse(); }
    // 夹批处理（「」）
    let p = line;
    p = p.replace(/「([^」]+)」/g, (m,c)=>{
      if(RD.comment==='none' || RD.comment==='jiqin' || RD.comment==='li' || RD.comment==='yuan') return '';
      return `<span class="comment-inline" title="${c}">${c}</span>`;
    });
    // 注释 (N)
    p = p.replace(/\((\d+)\)/g, (m,n)=>{
      if(RD.comment==='none' || RD.comment==='jin' || RD.comment==='li' || RD.comment==='yuan') return '';
      return `<sup class="pi" data-note="${n}">${n}</sup>`;
    });
    html += `<p>${p}</p>`;
  });
  flushVerse();
  content.innerHTML = html;

  // 注释区
  if(RD.comment!=='none' && RD.comment!=='jin' && RD.comment!=='li' && RD.comment!=='yuan' && !EXTRA[RD.comment] && RD.notes.length) {
    const chapNotes = RD.notes.filter(n=>n.chap===chap.id || n.chapter===chap.title);
    if(chapNotes.length) {
      notesBox.style.display='block';
      notesBox.innerHTML = `<h4>注 释（${chapNotes.length}条）</h4>` + chapNotes.map(n=>`<div class="note"><b>(${n.no||n.id})</b>${n.text}</div>`).join('');
    } else { notesBox.style.display='none'; }
  } else { notesBox.style.display='none'; }
}

/* ---------- 批注层：钟批 / 王评 / 程注 / 余评 ---------- */
const EXTRA={
  zhong:{tag:'钟批',who:'钟伯敬',color:'#7a5195',file:'zhongbo_comments.json',ok:['v100','jiqin'],kind:'zhong'},
  wang:{tag:'王评',who:'王望如',color:'#5a7d3a',file:'wangping_comments.json',ok:['v70','jin70','jin70_pi','jinshengtan'],kind:'wang'},
  cheng:{tag:'程注',who:'程穆衡',color:'#2f6f6f',file:'chengzhu_notes.json',ok:['v100','jiqin'],kind:'cheng'},
  yu:{tag:'余评',who:'余象斗',color:'#a9622d',file:'yuxiangdou_comments.json',ok:['v120','v100','v70','jin70','jin70_pi','jinshengtan','jiqin','zsk'],kind:'yu'}
};
const EXTRA_CACHE={};
function extraItems(kind,data,chap){
  const num = (chap && chap.num!=null) ? chap.num : RD.chap;
  const out=[];
  if(kind==='zhong'){
    if(num<=1)(data.pin_ren||[]).forEach(p=>out.push({k:'人品评·'+p.name,v:p.text}));
  }else if(kind==='wang'){
    const tgt='第'+num+'回';
    (data.chapters||[]).filter(c=>c.chapter===tgt).forEach(c=>out.push({k:(c.vol||'')+' '+(c.type||'总评'),v:c.text}));
  }else if(kind==='cheng'){
    const no=num<1?1:num;const vols=data.volumes||[];
    const vol=vols.find(v=>v.no===no)||vols.find(v=>v.no===no+1)||vols.find(v=>v.no===no-1);
    if(vol)(vol.items||[]).forEach(it=>out.push({k:it.k,v:it.v}));
  }else if(kind==='yu'){
    if(num<=1&&data.preface)out.push({k:'卷首叙',v:data.preface.text});
    if(num<=1&&data.bian)out.push({k:'水浒辨',v:data.bian.text});
    const no=num<1?1:num;
    const vol=(data.volumes||[]).find(v=>no>=v.hui[0]&&no<=v.hui[1]);
    if(vol&&(vol.items||[]).length){
      (vol.items||[]).forEach((t,i)=>out.push({k:vol.name+'·'+(i+1),v:t}));
    }else if(num>1){
      const cov=(data.coverage&&data.coverage.vols_with_comments)||[];
      const names=(data.volumes||[]).filter(v=>cov.indexOf(v.no)>=0).map(v=>v.name).join('、');
      if(names)out.push({k:'录文说明',v:'评林本上栏评语系孤本影印＋机器录文，现仅 '+names+' 切分完整、可校读；其余各卷评语与下栏正文混排、残缺过甚，暂缺。'});
    }
  }
  return out;
}
async function applyExtraComments(chap){
  const box=document.getElementById('readerNotes');
  const cfg=EXTRA[RD.comment];
  if(!cfg){ box.style.display='none'; return; }
  if(!cfg.ok.includes(RD.ver)){
    box.style.display='block';
    box.innerHTML='<h4>'+cfg.tag+'·'+cfg.who+'</h4><div class="note">此批注（'+cfg.tag+'）仅适用于对应版本，请切换到：'+cfg.ok.join(' / ')+'</div>';
    return;
  }
  if(!(cfg.file in EXTRA_CACHE)) EXTRA_CACHE[cfg.file]= await loadJSON('texts/versions/'+cfg.file);
  const data=EXTRA_CACHE[cfg.file];
  if(!data){ box.style.display='none'; return; }
  const items=extraItems(cfg.kind,data,chap);
  box.style.display='block';
  if(!items.length){ box.innerHTML='<h4>'+cfg.tag+'·'+cfg.who+'</h4><div class="note">本回暂无'+cfg.who+'批注。</div>'; return; }
  box.innerHTML='<h4 style="color:'+cfg.color+';">'+cfg.tag+'·'+cfg.who+'（'+items.length+'条）</h4>'+
    items.map(it=>'<div class="note"><b style="color:'+cfg.color+';">〔'+it.k+'〕</b>'+it.v+'</div>').join('');
}

/* ---------- 启动 ---------- */
document.addEventListener('DOMContentLoaded', boot);
