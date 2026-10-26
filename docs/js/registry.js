/* ============================================================
 * registry.js — 版本 / 批注「注册表」前端加载器（单一可信源）
 * ------------------------------------------------------------
 * 数据来源：data/registry.json
 * 用法：<script src="js/registry.js"></script> 之后 await Registry.load();
 * 之后各页面从 Registry 取版本、批注元数据，不再各自硬编码。
 *
 * 扩充方式：只改 docs/data/registry.json（+ 补齐语料目录），此处无需改动。
 * 若 registry.json 读取失败，自动退回内置 DEFAULT（保证不白屏）。
 * ============================================================ */
(function (global) {
  'use strict';

  /* 内置兜底：与 data/registry.json 同步。仅在注册表读取失败时启用。 */
  const DEFAULT = {
    schema_version: 1,
    versions: [
      {"id": "v120", "order": 1, "short": "袁百二", "shortDiff": "袁", "label": "袁百二回", "name": "袁无涯百二十回全传", "cls": "", "color": "#c0392b", "range": [0, 120], "system": "繁本·全传", "status": "ready"},
      {"id": "v100", "order": 2, "short": "容百回", "shortDiff": "容", "label": "容百回本", "name": "容与堂百回本", "cls": "jade", "color": "#5a7d3a", "range": [0, 100], "system": "繁本·百回", "status": "ready"},
      {"id": "v70", "order": 3, "short": "金七十", "shortDiff": "古", "label": "古本七十", "name": "贯华堂七十回本", "cls": "gold", "color": "#8a6d3b", "range": [0, 70], "system": "七十回本", "status": "ready"},
      {"id": "jin70", "order": 4, "short": "金批繁", "shortDiff": "金·繁", "label": "金批繁本", "name": "金圣叹评本（繁）", "cls": "", "color": "#8b1a1a", "range": [0, 70], "system": "七十回本", "status": "ready"},
      {"id": "jin70_pi", "order": 5, "short": "金批全", "shortDiff": "金·全", "label": "金批全文", "name": "金圣叹批评本（全批繁）", "cls": "", "color": "#7a1414", "range": [0, 70], "system": "七十回本·评点改造本", "status": "ready"},
      {"id": "jinshengtan", "order": 6, "short": "金批简", "shortDiff": "金·简", "label": "金批简本", "name": "金圣叹批评本（简）", "cls": "", "color": "#6b1414", "range": [0, 70], "system": "七十回本", "status": "ready"},
      {"id": "jiqin", "order": 7, "short": "冀勤注", "shortDiff": "冀", "label": "冀勤校注", "name": "冀勤校注百回本", "cls": "jade", "color": "#2f5d50", "range": [0, 100], "system": "现代校注本", "status": "ready"},
      {"id": "zsk", "order": 8, "short": "征四寇", "shortDiff": "寇", "label": "征四寇", "name": "征四寇（简本）", "cls": "gold", "color": "#8a6d3b", "range": [82, 120], "system": "简本·续书", "status": "ready"}
    ],
    commentaries: [
      {"id": "jinpi", "order": 1, "tag": "金批", "who": "金圣叹", "cls": "cmt-jinpi", "chipCls": "red", "color": "#8b1a1a", "file": "jinpi_comments.json", "kind": "jin", "okVer": ["v70", "jin70", "jin70_pi", "jinshengtan"]},
      {"id": "lizhuo", "order": 2, "tag": "容本", "who": "李卓吾", "cls": "cmt-lizhuo", "chipCls": "gold", "color": "#8b4513", "file": "lizhuo_comments.json", "kind": "li", "okVer": ["v100", "jiqin"]},
      {"id": "yuanwy", "order": 3, "tag": "袁本", "who": "袁无涯", "cls": "cmt-yuanwy", "chipCls": "indigo", "color": "#2e5a88", "file": "yuanwy_comments.json", "kind": "yuan", "okVer": ["v120"]},
      {"id": "zhongbo", "order": 4, "tag": "钟批", "who": "钟伯敬", "cls": "cmt-zhongbo", "chipCls": "", "color": "#7a5195", "file": "zhongbo_comments.json", "kind": "zhong", "okVer": ["v100", "jiqin"]},
      {"id": "wangping", "order": 5, "tag": "王评", "who": "王望如", "cls": "cmt-wangping", "chipCls": "jade", "color": "#5a7d3a", "file": "wangping_comments.json", "kind": "wang", "okVer": ["v70", "jin70", "jin70_pi", "jinshengtan"]},
      {"id": "yuxiangdou", "order": 6, "tag": "余评", "who": "余象斗", "cls": "cmt-yuxiangdou", "chipCls": "", "color": "#a9622d", "file": "yuxiangdou_comments.json", "kind": "yu", "okVer": ["v120", "v100", "v70", "jin70", "jin70_pi", "jinshengtan", "jiqin", "zsk"]},
      {"id": "chengzhu", "order": 7, "tag": "程注", "who": "程穆衡", "cls": "cmt-chengzhu", "chipCls": "jade", "color": "#2f6f6f", "file": "chengzhu_notes.json", "kind": "cheng", "okVer": ["v120", "v100", "jiqin"]},
      {"id": "jiqin", "order": 8, "tag": "冀注", "who": "冀勤校注", "cls": "cmt-jiqin", "chipCls": "jade", "color": "#2f5d50", "file": "jiqin_notes.json", "kind": "jiqin", "okVer": ["v100", "jiqin"]},
      {"id": "yannanshang", "order": 9, "tag": "燕评", "who": "燕南尚生", "cls": "cmt-yannanshang", "chipCls": "gold", "color": "#8a6d3b", "file": "yannanshang_comments.json", "kind": "yan", "okVer": ["v120", "v100", "v70", "jin70", "jin70_pi", "jinshengtan", "jiqin", "zsk"]}
    ]
  };

  let _data = null;
  let _loaded = false;
  let _source = 'default'; // 'registry.json' | 'default'

  function norm(d) {
    if (!d || !Array.isArray(d.versions)) return null;
    const versions = d.versions.slice().sort((a, b) => (a.order || 99) - (b.order || 99));
    const commentaries = (Array.isArray(d.commentaries) ? d.commentaries : [])
      .slice().sort((a, b) => (a.order || 99) - (b.order || 99));
    return Object.assign({}, d, { versions, commentaries });
  }

  /* 未显式 load 时也能取到兜底数据，避免调用方因数据未就绪拿到空数组 */
  function _ensure(){ if(!_data) _data = norm(DEFAULT); return _data; }

  const Registry = {
    /* 加载注册表；成功后缓存。path 默认 data/registry.json（相对站点根） */
    async load(path) {
      if (_loaded) return _data;
      try {
        const r = await fetch(path || 'data/registry.json', { cache: 'no-cache' });
        if (r.ok) {
          const j = norm(await r.json());
          if (j && j.versions.length) { _data = j; _source = 'registry.json'; _loaded = true; return _data; }
        }
      } catch (e) { /* 读取失败 → 退回内置默认 */ }
      _data = norm(DEFAULT);
      _source = 'default';
      _loaded = true;
      return _data;
    },

    /* 是否已加载（未加载时可先调用 load） */
    get loaded() { return _loaded; },
    /* 数据来源：registry.json 或 default（兜底） */
    get source() { return _source; },

    /* 全部版本（按 order 排序） */
    versions() { return _ensure().versions; },
    /* 单个版本元数据 */
    version(id) { return this.versions().find(v => v.id === id) || null; },
    /* 版本简称映射：{ id: short } */
    get VER_SHORT() { const m = {}; this.versions().forEach(v => m[v.id] = v.short || v.name); return m; },
    /* 版本全名映射：{ id: name } */
    get VER_NAME() { const m = {}; this.versions().forEach(v => m[v.id] = v.name || v.id); return m; },

    /* 全部批注家（按 order 排序） */
    comments() { return _ensure().commentaries; },
    /* 单个批注家元数据 */
    comment(id) { return this.comments().find(c => c.id === id) || null; },
    /* 某版本可挂载的批注家列表 */
    commentsFor(vid) { return this.comments().filter(c => (c.okVer || []).indexOf(vid) >= 0); },

    /* 版本是否覆盖某回次（range 判定；range 缺省视为全支持） */
    covers(vid, hui) {
      const v = this.version(vid);
      if (!v) return false;
      if (!Array.isArray(v.range)) return true;
      return hui >= v.range[0] && hui <= v.range[1];
    },
    /* 覆盖某回次的全部版本 */
    versionsFor(hui) { return this.versions().filter(v => this.covers(v.id, hui)); },

    /* 描述该版本覆盖回次的中文串，如「0–120 回」 */
    rangeLabel(vid) {
      const v = this.version(vid);
      if (!v || !Array.isArray(v.range)) return '';
      return v.range[0] + '–' + v.range[1] + ' 回';
    }
  };

  global.Registry = Registry;
})(typeof window !== 'undefined' ? window : globalThis);
