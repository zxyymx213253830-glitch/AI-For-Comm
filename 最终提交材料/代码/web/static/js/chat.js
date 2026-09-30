/* ==========================================================
   对话问答页 — 专家卡片 + 快问快答（自动路由，真实接口）
   ========================================================== */

/* 快捷填入问题（供模板内联按钮调用） */
function fillChat(text) {
  var input = document.getElementById('chatInput');
  if (!input) return;
  input.value = text;
  input.focus();
}

(function () {
  var stream = document.getElementById('chatStream');
  var input = document.getElementById('chatInput');
  var sendBtn = document.getElementById('chatSend');
  var busy = false;

  /* 每位专家的示例问题 */
  var SAMPLES = {
    math_agent: '请推导香农信道容量公式，并解释各参数含义',
    comm_agent: '5G 随机接入流程的信令是怎样的？',
    hw_agent: '用 Verilog 设计一个 BPSK 调制模块',
    sim_agent: '写一段 BPSK 在 AWGN 信道下的蒙特卡洛仿真代码',
    lit_review_agent: '帮我调研 MIMO-OFDM 信道容量研究的代表性文献',
    verify_agent: '如何校验一份通信仿真研究报告的正确性？'
  };

  /* 渲染六张专家能力卡片 */
  function renderExperts() {
    var grid = document.getElementById('expertGrid');
    if (!grid) return;
    var keys = ['math_agent', 'comm_agent', 'hw_agent', 'sim_agent', 'lit_review_agent', 'verify_agent'];
    grid.innerHTML = keys.map(function (k) {
      var m = AGENT_META[k];
      return '<button class="glass card expert-card" type="button" data-key="' + k + '">' +
        '<div class="ic">' + m.icon + '</div>' +
        '<h4>' + m.short + ' Agent</h4>' +
        '<p>' + esc(m.desc) + '</p>' +
        '<div class="eg">点击开始提问 →</div></button>';
    }).join('');
    grid.querySelectorAll('.expert-card').forEach(function (card) {
      card.addEventListener('click', function () {
        fillChat(SAMPLES[card.dataset.key] || '');
      });
    });
  }

  function addMsg(role, bubbleHtml) {
    var row = document.createElement('div');
    row.className = 'msg ' + role;
    row.innerHTML = '<div class="av">' + (role === 'user' ? '研' : 'AI') + '</div>' +
      '<div class="bubble">' + bubbleHtml + '</div>';
    stream.appendChild(row);
    row.scrollIntoView({ behavior: 'smooth', block: 'end' });
    return row;
  }

  async function send() {
    var q = input.value.trim();
    if (!q) { showToast('请先输入问题', 'warn'); return; }
    if (busy) { showToast('上一个问题还在回答中', 'warn'); return; }
    busy = true;
    sendBtn.disabled = true;
    input.value = '';

    addMsg('user', esc(q));
    var row = addMsg('sys',
      '<div class="route-badge">⌁ 自动路由 · 正在分析…</div>' +
      '<span class="typing"><i></i><i></i><i></i> 专家思考中，请稍候…</span>');
    var bubble = row.querySelector('.bubble');

    try {
      var data = await api('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      var name = agentShort(data.agent) + ' Agent';
      bubble.innerHTML = '<div class="route-badge">⌁ 自动路由 · ' + esc(name) + '</div>' +
        (data.tools_text ? '<span class="tool-tag">本地工具：' + esc(data.tools_text) + '</span>' : '') +
        '<div class="md"></div>';
      renderMarkdown(bubble.querySelector('.md'), data.answer);
      row.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } catch (e) {
      bubble.innerHTML = '<div class="route-badge" style="color:var(--red);background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.4)">✕ 调用失败</div>' +
        '<div class="md">' + esc(e.message) + '</div>';
      showToast(e.message, 'err');
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  renderExperts();
  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
})();
