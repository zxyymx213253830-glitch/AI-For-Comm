/* ==========================================================
   AI for Comm — 全局工具与智能体元信息
   ========================================================== */

/* 七位专家智能体的中文名称、简介与图标（与后端 config.json 键名一致） */
var AGENT_META = {
  math_agent:       { short: '数学推导', desc: '信息论公式推导与信道容量计算', icon: '∑' },
  comm_agent:       { short: '通信工程', desc: '3GPP 协议查询与信令流程分析', icon: '⌁' },
  hw_agent:         { short: '硬件实践', desc: 'FPGA / Verilog 模块生成与时序分析', icon: '◇' },
  sim_agent:        { short: '通信仿真', desc: '蒙特卡洛仿真代码生成与运行', icon: '◌' },
  lit_review_agent: { short: '文献调研', desc: '公网与知识库双源检索和综述', icon: '⌕' },
  verify_agent:     { short: '综合校验', desc: '对专家产出进行三级校验与回退', icon: '✓' },
  report_agent:     { short: '报告主编', desc: '统稿、排版并生成结构化研究报告', icon: '▤' }
};
var AGENT_ORDER = ['math_agent', 'comm_agent', 'hw_agent', 'sim_agent',
                   'lit_review_agent', 'verify_agent', 'report_agent'];

function agentShort(key) {
  var m = AGENT_META[key];
  return m ? m.short : key;
}

/* Toast 提示：type 取 ok / warn / err */
var _toastTimer = null;
function showToast(text, type) {
  var t = document.getElementById('toast');
  if (!t) return;
  type = type || 'ok';
  t.className = 'toast show ' + type;
  t.innerHTML = (type === 'ok' ? '✓ ' : type === 'warn' ? '! ' : '✕ ') + esc(text);
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(function () { t.classList.remove('show'); }, 2600);
}

/* HTML 转义 */
function esc(s) {
  var d = document.createElement('div');
  d.textContent = (s == null ? '' : String(s));
  return d.innerHTML;
}

/* 本地 Markdown 渲染器（外网排版库不可达时的兜底，保证回复永不退化成裸文本）
   覆盖智能体回复实际用到的子集：代码围栏/标题/表格/引用/列表/粗斜体/行内码/链接 */
function localMarkdown(text) {
  var src = String(text == null ? '' : text);
  var fences = [];
  src = src.replace(/```([^\n`]*)\n([\s\S]*?)```/g, function (m, lang, code) {
    fences.push('<pre><code class="lang-' + esc(lang.trim()) + '">' + esc(code) + '</code></pre>');
    return '\u0000F' + (fences.length - 1) + '\u0000';
  });
  src = esc(src);
  function inline(s) {
    return s
      .replace(/`([^`\n]+)`/g, function (m, c) { return '<code>' + c + '</code>'; })
      .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
      .replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }
  var lines = src.split(/\r?\n/), out = [], i = 0;
  function isTableSep(s) { return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(s) && s.indexOf('-') >= 0; }
  while (i < lines.length) {
    var ln = lines[i];
    if (!ln.trim()) { i++; continue; }
    var fm = ln.match(/^\u0000F(\d+)\u0000\s*$/);
    if (fm) { out.push(fences[+fm[1]]); i++; continue; }
    var hm = ln.match(/^(#{1,6})\s+(.*)$/);
    if (hm) { out.push('<h' + hm[1].length + '>' + inline(hm[2]) + '</h' + hm[1].length + '>'); i++; continue; }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(ln)) { out.push('<hr>'); i++; continue; }
    if (ln.indexOf('|') >= 0 && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      var head = ln.split('|').map(function (c) { return c.trim(); }).filter(function (c, idx, a) { return c !== '' || (idx > 0 && idx < a.length - 1); });
      i += 2;
      var rows = [];
      while (i < lines.length && lines[i].indexOf('|') >= 0 && lines[i].trim()) {
        rows.push(lines[i].split('|').map(function (c) { return c.trim(); }).filter(function (c, idx, a) { return c !== '' || (idx > 0 && idx < a.length - 1); }));
        i++;
      }
      var html = '<table><thead><tr>' + head.map(function (c) { return '<th>' + inline(c) + '</th>'; }).join('') + '</tr></thead><tbody>';
      html += rows.map(function (r) { return '<tr>' + r.map(function (c) { return '<td>' + inline(c) + '</td>'; }).join('') + '</tr>'; }).join('');
      out.push(html + '</tbody></table>');
      continue;
    }
    if (/^\s*&gt;\s?/.test(ln)) {
      var q = [];
      while (i < lines.length && /^\s*&gt;\s?/.test(lines[i])) { q.push(lines[i].replace(/^\s*&gt;\s?/, '')); i++; }
      out.push('<blockquote>' + inline(q.join('<br>')) + '</blockquote>');
      continue;
    }
    if (/^\s*[-*+]\s+/.test(ln)) {
      var ul = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) { ul.push('<li>' + inline(lines[i].replace(/^\s*[-*+]\s+/, '')) + '</li>'); i++; }
      out.push('<ul>' + ul.join('') + '</ul>');
      continue;
    }
    if (/^\s*\d+[.、)]\s+/.test(ln)) {
      var ol = [];
      while (i < lines.length && /^\s*\d+[.、)]\s+/.test(lines[i])) { ol.push('<li>' + inline(lines[i].replace(/^\s*\d+[.、)]\s+/, '')) + '</li>'); i++; }
      out.push('<ol>' + ol.join('') + '</ol>');
      continue;
    }
    var para = [ln];
    i++;
    while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|\s*[-*+]\s|\s*\d+[.、)]\s|\s*&gt;)/.test(lines[i]) && !/^\u0000F\d+\u0000\s*$/.test(lines[i])) { para.push(lines[i]); i++; }
    out.push('<p>' + inline(para.join('<br>')) + '</p>');
  }
  var html2 = out.join('\n');
  return html2.replace(/\u0000F(\d+)\u0000/g, function (m, n) { return fences[+n]; });
}

/* 公式保护：排版库会把 LaTeX 里的下划线当成斜体强调（$P_{eff}$ 一出现，
   它到下一个下划线之间的整段正文都会变斜体），也会把正文里的 ~ 当成下标标记
   （6~10dB 到下一个 ~ 之间的字会被吞成小字）。所以排版前先把公式和波浪号
   摘成占位符，排完再放回，最后才交给 KaTeX。与 core/report.py 同口径。 */
function protectMath(text) {
  var store = [];
  var s = String(text == null ? '' : text)
    .replace(/\$\$[\s\S]+?\$\$/g, function (m) { store.push(m); return '\u0000K' + (store.length - 1) + '\u0000'; })
    .replace(/\$(?:[^$\n])+?\$/g, function (m) { store.push(m); return '\u0000K' + (store.length - 1) + '\u0000'; });
  s = s.replace(/~/g, '\u0000W\u0000');
  return [s, store];
}

function restoreMath(html, store) {
  return String(html)
    .replace(/\u0000K(\d+)\u0000/g, function (m, i) { return store[+i] == null ? m : store[+i]; })
    .replace(/\u0000W\u0000/g, '~');
}

/* 公式卫生：\text{} 里的下划线/脱字符 KaTeX 文本模式不接受，先转义掉，
   否则整条公式报错标红并原样显示（与后端 core/report.sanitize_math 同口径） */
function fixTexText(s) {
  return String(s).replace(/\\(text(?:rm|bf|it)?|mbox)\s*\{([^{}]*)\}/g, function (m, cmd, inner) {
    return '\\' + cmd + '{' + inner.replace(/_/g, '\\_').replace(/\^/g, '\\textasciicircum ') + '}';
  });
}

/* Markdown + 公式 + 代码高亮 渲染（外网库缺失时自动落到本地渲染器） */
function renderMarkdown(el, text) {
  var src = fixTexText(text || '');
  var guarded = protectMath(src);
  var html;
  if (window.marked && window.marked.parse) {
    try { html = marked.parse(guarded[0]); }
    catch (e) { html = localMarkdown(guarded[0]); }
  } else {
    html = localMarkdown(guarded[0]);
  }
  el.innerHTML = restoreMath(html, guarded[1]);
  if (window.hljs) {
    el.querySelectorAll('pre code').forEach(function (b) {
      try { hljs.highlightElement(b); } catch (e) { /* 忽略 */ }
    });
  }
  if (window.renderMathInElement) {
    try {
      renderMathInElement(el, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false
      });
    } catch (e) { /* 忽略 */ }
  }
}

/* fetch 封装：返回解析后的 JSON，非 2xx 抛出带 error 信息的对象 */
async function api(url, opts) {
  var resp = await fetch(url, opts);
  var data = null;
  try { data = await resp.json(); } catch (e) { data = null; }
  if (!resp.ok) {
    var msg = (data && (data.error || (data.errors || []).join('；'))) || ('请求失败（' + resp.status + '）');
    var err = new Error(msg);
    err.status = resp.status;
    err.data = data;
    throw err;
  }
  return data;
}

/* 侧栏云端连接状态：根据平台配置是否就绪更新指示 */
(async function () {
  var dot = document.getElementById('cloudDot');
  var txt = document.getElementById('cloudTxt');
  if (!dot || !txt) return;
  try {
    var cfg = await api('/api/admin/config');
    var base = (cfg && cfg.platform && cfg.platform.baseUrl) || '';
    if (base) {
      dot.className = 'cdot ok';
      txt.textContent = 'OpenTrek 云端 · 已接入';
    } else {
      dot.className = 'cdot bad';
      txt.textContent = 'OpenTrek 云端 · 未配置';
    }
  } catch (e) {
    dot.className = 'cdot bad';
    txt.textContent = 'OpenTrek 云端 · 状态未知';
  }
})();
