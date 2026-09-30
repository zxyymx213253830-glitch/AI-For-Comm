/* ==========================================================
   科研任务页 — 六步流水线 + 协作网络 + SSE 实时进度
   ========================================================== */

/* 快捷填入课题（供模板内联按钮调用） */
function fillTopic(text) {
  var t = document.getElementById('topic');
  if (!t) return;
  t.value = text;
  t.focus();
}

(function () {
  /* ── 流水线六步与智能体的对应关系 ── */
  var STAGES = [
    { id: 1, name: '问题拆解', agents: ['comm_agent'] },
    { id: 2, name: '文献调研', agents: ['lit_review_agent'] },
    { id: 3, name: '并行专家', agents: ['math_agent', 'comm_agent', 'hw_agent', 'sim_agent'] },
    { id: 4, name: '综合校验', agents: ['verify_agent'] },
    { id: 5, name: '报告统稿', agents: ['report_agent'] },
    { id: 6, name: '报告渲染', agents: [] }
  ];

  /* ── 协作网络节点坐标（600×420 坐标系，按百分比定位保证对齐） ── */
  var CENTER = { x: 300, y: 210 };
  var NODE_POS = {
    lit_review_agent: { x: 300, y: 85 },
    math_agent:       { x: 151, y: 132 },
    comm_agent:       { x: 449, y: 132 },
    verify_agent:     { x: 115, y: 238 },
    hw_agent:         { x: 485, y: 238 },
    report_agent:     { x: 218, y: 323 },
    sim_agent:        { x: 382, y: 323 }
  };
  var EDGES = [];
  AGENT_ORDER.forEach(function (k) { EDGES.push(['center', k]); });
  ['math_agent', 'comm_agent', 'hw_agent', 'sim_agent', 'lit_review_agent']
    .forEach(function (k) { EDGES.push([k, 'verify_agent']); });
  EDGES.push(['verify_agent', 'report_agent']);

  /* ── 运行时状态 ── */
  var nodeState = {};                       // 'center'/agent -> online|working|verifying|done
  var stepState = [null, 'idle', 'idle', 'idle', 'idle', 'idle', 'idle']; // 1..6
  var stepElapsed = [null, 0, 0, 0, 0, 0, 0];
  var activeStep = -1;
  var tickTimer = null, eventSource = null, currentTask = null, running = false;
  var autoRotate = true, rotY = 0, rotX = 0, rotateFrame = null;

  var topicInput = document.getElementById('topic');
  var runBtn = document.getElementById('runBtn');
  var stepper = document.getElementById('stepper');
  var links = document.getElementById('links');
  var scene = document.getElementById('scene');
  var tooltip = document.getElementById('tooltip');
  var logBox = document.getElementById('logBox');
  var prodBox = document.getElementById('prodBox');
  var verifyBox = document.getElementById('verifyBox');
  var resultBanner = document.getElementById('resultBanner');
  var failBanner = document.getElementById('failBanner');

  /* ══════════ 协作网络渲染 ══════════ */
  function resetStates() {
    nodeState = { center: 'online' };
    AGENT_ORDER.forEach(function (k) { nodeState[k] = 'online'; });
  }

  function edgeClass(a, b) {
    var busy = ['working', 'verifying'];
    if (busy.indexOf(nodeState[a]) >= 0 || busy.indexOf(nodeState[b]) >= 0) {
      return (nodeState[a] === 'verifying' || nodeState[b] === 'verifying') ? 'flow-warn' : 'flow';
    }
    return '';
  }

  function renderNetwork() {
    links.innerHTML = EDGES.map(function (e) {
      var p = e[0] === 'center' ? CENTER : NODE_POS[e[0]];
      var q = e[1] === 'center' ? CENTER : NODE_POS[e[1]];
      return '<line class="' + edgeClass(e[0], e[1]) + '" x1="' + p.x + '" y1="' + p.y + '" x2="' + q.x + '" y2="' + q.y + '"/>';
    }).join('');

    var html = '<button class="node ' + nodeState.center + '" data-id="center" style="left:' +
      (CENTER.x / 600 * 100) + '%;top:' + (CENTER.y / 420 * 100) + '%">' +
      '<span class="ring"><span class="spin-ring"></span>⌬</span><span class="nl">编排器</span></button>';
    html += AGENT_ORDER.map(function (k) {
      var p = NODE_POS[k], m = AGENT_META[k];
      return '<button class="node ' + nodeState[k] + '" data-id="' + k + '" style="left:' +
        (p.x / 600 * 100) + '%;top:' + (p.y / 420 * 100) + '%">' +
        '<span class="ring"><span class="spin-ring"></span>' + m.icon + '</span>' +
        '<span class="nl">' + m.short + '</span></button>';
    }).join('');
    scene.innerHTML = html;

    scene.querySelectorAll('.node').forEach(function (node) {
      node.addEventListener('mouseenter', function () { showNodeTip(node); });
      node.addEventListener('mouseleave', hideNodeTip);
    });
  }

  var STATE_LABEL = { online: '在线', working: '工作中', verifying: '校验中', done: '已完成', offline: '离线' };

  function showNodeTip(node) {
    var id = node.dataset.id;
    var name = id === 'center' ? '本地编排器' : AGENT_META[id].short + ' Agent';
    var desc = id === 'center' ? '任务调度 · 消息总线 · 仿真执行 · 报告渲染' : AGENT_META[id].desc;
    tooltip.innerHTML = '<b>' + esc(name) + '</b><div class="d">' + esc(desc) + '</div>' +
      '<div class="d">状态：' + (STATE_LABEL[nodeState[id]] || '在线') + '</div>';
    var st = document.getElementById('stage');
    tooltip.style.left = Math.min(node.offsetLeft + 60, st.clientWidth - 190) + 'px';
    tooltip.style.top = Math.max(node.offsetTop - 10, 10) + 'px';
    tooltip.classList.add('show');
  }
  function hideNodeTip() { tooltip.classList.remove('show'); }

  /* 3D 自转与拖拽（节点反向旋转，保证标签始终正面朝向镜头） */
  function animateNetwork() {
    if (autoRotate) rotY = (rotY + 0.12) % 360;
    scene.style.transform = 'rotateY(' + rotY + 'deg) rotateX(' + rotX + 'deg)';
    var inv = 'rotateX(' + (-rotX) + 'deg) rotateY(' + (-rotY) + 'deg)';
    scene.querySelectorAll('.node').forEach(function (n) { n.style.transform = inv; });
    rotateFrame = requestAnimationFrame(animateNetwork);
  }
  (function bindDrag() {
    var stage = document.getElementById('stage');
    var dragging = false, lx = 0, ly = 0;
    stage.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.node')) return;
      dragging = true; lx = e.clientX; ly = e.clientY;
      stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      rotY += (e.clientX - lx) * 0.4;
      rotX = Math.max(-40, Math.min(40, rotX - (e.clientY - ly) * 0.3));
      lx = e.clientX; ly = e.clientY;
    });
    stage.addEventListener('pointerup', function () { dragging = false; });
    document.getElementById('autoBtn').addEventListener('click', function () {
      autoRotate = !autoRotate;
      this.textContent = autoRotate ? '⏸ 暂停自转' : '▶ 开始自转';
    });
  })();

  /* ══════════ 步骤条渲染 ══════════ */
  function renderStepper() {
    stepper.innerHTML = STAGES.map(function (s) {
      var stt = stepState[s.id];
      var cls = stt === 'done' ? 'done' : stt === 'fail' ? 'fail' : stt === 'active' ? 'active' : '';
      var meta = stt === 'done' ? '已完成 · ' + stepElapsed[s.id] + 's'
        : stt === 'fail' ? '执行失败'
        : stt === 'active' ? '执行中 · ' + stepElapsed[s.id] + 's'
        : '待执行';
      return '<div class="step ' + cls + '"><div class="circ">' + (stt === 'done' ? '✓' : s.id) + '</div>' +
        '<div class="nm">' + s.name + '</div><div class="mt">' + meta + '</div></div>';
    }).join('');
  }

  function tick() {
    if (activeStep >= 1 && stepState[activeStep] === 'active') {
      stepElapsed[activeStep]++;
      renderStepper();
    }
  }

  /* ══════════ 面板与日志 ══════════ */
  document.querySelectorAll('.panel-h').forEach(function (h) {
    h.addEventListener('click', function () { h.parentElement.classList.toggle('collapsed'); });
  });

  function addLog(source, text, color) {
    if (logBox.querySelector('.log-empty')) logBox.innerHTML = '';
    var time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    var line = document.createElement('div');
    line.className = 'logline';
    line.innerHTML = '<span class="ts">' + time + '</span>' +
      '<span class="src" style="color:' + (color || 'var(--cyan)') + '">' + esc(source) + '</span>' +
      '<span>' + esc(text) + '</span>';
    logBox.appendChild(line);
    logBox.scrollTop = logBox.scrollHeight;
  }

  function addProduct(stepName, detail) {
    if (prodBox.querySelector('.log-empty')) prodBox.innerHTML = '';
    var item = document.createElement('div');
    item.className = 'produce-item';
    item.innerHTML = '<div class="ph"><span class="st st-done"><i class="d"></i>完成</span> ' + esc(stepName) + '</div>' +
      '<div style="color:var(--tx2)">' + esc(detail || '该阶段已顺利完成。') + '</div>';
    prodBox.appendChild(item);
  }

  function showVerdict(verdict) {
    if (!verdict) {
      verifyBox.innerHTML = '<div class="log-empty">本次任务未返回校验结论</div>';
      return;
    }
    var cls = 'ok', icon = '✓', title = '校验通过';
    if (verdict.indexOf('不通过') >= 0) { cls = 'bad'; icon = '✕'; title = '校验不通过'; }
    else if (verdict.indexOf('有条件通过') >= 0) { cls = 'warn'; icon = '!'; title = '有条件通过'; }
    verifyBox.innerHTML = '<div class="verify-row"><span class="vi ' + cls + '">' + icon + '</span>' +
      '<div><div class="vt">' + title + '</div><div class="vd">' + esc(verdict) + '</div></div></div>';
  }

  /* ══════════ 步骤 → 节点状态联动 ══════════ */
  function activateStage(stepId) {
    resetStates();
    var stage = STAGES[stepId - 1];
    if (!stage) return;
    if (stage.agents.length === 0) {
      nodeState.center = 'working';
    } else {
      stage.agents.forEach(function (k) {
        nodeState[k] = (k === 'verify_agent') ? 'verifying' : 'working';
      });
    }
    renderNetwork();
  }

  function markAllDone() {
    resetStates();
    AGENT_ORDER.forEach(function (k) { nodeState[k] = 'done'; });
    nodeState.center = 'done';
    renderNetwork();
  }

  /* ══════════ SSE 事件处理 ══════════ */
  function reportFilename(path) {
    if (!path) return '';
    var parts = String(path).split(/[\\/]/);
    return parts[parts.length - 1];
  }

  function showResultBanner(result, reportPath) {
    var fname = reportFilename(reportPath || (result && result.report_path));
    var html = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' +
      '<div><b style="font-size:14px">研究报告已生成</b><div style="font-size:12px;color:var(--tx2)">' +
      (result && result.experts_count != null ? '共 ' + result.experts_count + ' 位专家参与，' : '') +
      (result && result.elapsed != null ? '总耗时 ' + Math.round(result.elapsed) + ' 秒。' : '') +
      '</div></div><span style="flex:1"></span>';
    if (fname) {
      html += '<a class="btn btn-primary btn-sm" target="_blank" href="/reports/view/' + encodeURIComponent(fname) + '">预览报告</a>';
    }
    html += '<a class="btn btn-ghost btn-sm" href="/reports">前往报告库</a>';
    resultBanner.innerHTML = html;
    resultBanner.classList.add('show');
  }

  function showFailBanner(message) {
    failBanner.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' +
      '<div><b style="font-size:14px">任务执行失败</b><div style="font-size:12px">' + esc(message || '未知错误') + '</div></div>' +
      '<span style="flex:1"></span>' +
      '<button class="btn btn-danger btn-sm" type="button" onclick="document.getElementById(\'runBtn\').click()">重试任务</button>';
    failBanner.classList.add('show');
  }

  function fetchResult(taskId, reportPath) {
    fetch('/api/pipeline/result/' + taskId).then(function (r) { return r.json(); })
      .then(function (result) {
        if (result.status === 'done') {
          showResultBanner(result, reportPath);
          showVerdict(result.verdict);
        }
      }).catch(function () { /* 忽略 */ });
  }

  function handle(msg) {
    if (msg.event === 'progress') {
      var sid = msg.step_id;
      var stage = STAGES[sid - 1];
      var source = (stage && stage.agents.length)
        ? agentShort(stage.agents[0]) + (stage.agents.length > 1 ? ' 等 ' + stage.agents.length + ' 位专家' : ' Agent')
        : '本地编排器';
      if (msg.status === 'start') {
        if (activeStep >= 1 && stepState[activeStep] === 'active') {
          stepState[activeStep] = 'done';   // 兜底：上一步未收到 done 也标记完成
        }
        activeStep = sid;
        stepState[sid] = 'active';
        stepElapsed[sid] = 0;
        activateStage(sid);
        renderStepper();
        addLog(source, '开始执行「' + msg.step_name + '」…' + (msg.detail ? ' — ' + msg.detail : ''), 'var(--indigo)');
      } else if (msg.status === 'done') {
        stepState[sid] = 'done';
        renderStepper();
        addLog(source, '「' + msg.step_name + '」已完成。' + (msg.detail ? ' — ' + msg.detail : ''), 'var(--green)');
        addProduct(msg.step_name, msg.detail);
        if (sid === 4 && msg.detail) showVerdict(msg.detail);
      } else if (msg.status === 'error') {
        stepState[sid] = 'fail';
        renderStepper();
        addLog(source, '「' + msg.step_name + '」出错' + (msg.detail ? ' — ' + msg.detail : ''), 'var(--red)');
      } else if (msg.detail) {
        addLog(source, msg.detail);
      }
    } else if (msg.event === 'complete') {
      for (var i = 1; i <= 6; i++) { if (stepState[i] !== 'fail') stepState[i] = 'done'; }
      renderStepper();
      markAllDone();
      addLog('报告主编 Agent', '研究报告已渲染并写入报告库。', 'var(--green)');
      fetchResult(currentTask, msg.report_path);
    } else if (msg.event === 'error') {
      if (activeStep >= 1 && stepState[activeStep] === 'active') stepState[activeStep] = 'fail';
      renderStepper();
      showFailBanner(msg.message);
      addLog('编排器', '任务失败：' + (msg.message || '未知错误'), 'var(--red)');
      showToast('任务失败：' + (msg.message || '未知错误'), 'err');
    } else if (msg.event === 'end') {
      finish();
    }
  }

  function finish() {
    if (eventSource) { eventSource.close(); eventSource = null; }
    if (tickTimer) { clearInterval(tickTimer); tickTimer = null; }
    running = false;
    activeStep = -1;
    runBtn.disabled = false;
    runBtn.textContent = '▶ 开始研究';
  }

  function subscribe(taskId) {
    eventSource = new EventSource('/api/pipeline/progress/' + taskId);
    eventSource.onmessage = function (e) {
      var msg;
      try { msg = JSON.parse(e.data); } catch (err) { return; }
      if (!msg || !msg.event) return;   // 心跳包
      handle(msg);
    };
    eventSource.onerror = function () {
      // 连接中断兜底：主动查询一次结果
      if (eventSource) { eventSource.close(); eventSource = null; }
      fetchResult(taskId);
      if (running) finish();
    };
  }

  function resetUI() {
    stepState = [null, 'idle', 'idle', 'idle', 'idle', 'idle', 'idle'];
    stepElapsed = [null, 0, 0, 0, 0, 0, 0];
    renderStepper();
    resetStates();
    renderNetwork();
    logBox.innerHTML = '<div class="log-empty">等待任务启动…<br>日志将按来源智能体实时滚动</div>';
    prodBox.innerHTML = '<div class="log-empty">暂无阶段产出</div>';
    verifyBox.innerHTML = '<div class="log-empty">校验尚未开始</div>';
    resultBanner.classList.remove('show');
    resultBanner.innerHTML = '';
    failBanner.classList.remove('show');
    failBanner.innerHTML = '';
  }

  async function start() {
    var topic = topicInput.value.trim();
    if (!topic) { showToast('请先填写研究课题', 'warn'); return; }
    if (running) return;
    running = true;
    runBtn.disabled = true;
    runBtn.textContent = '研究中…';
    resetUI();
    addLog('编排器', '研究任务已启动：' + topic, 'var(--indigo)');
    try {
      var data = await api('/api/pipeline/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic })
      });
      currentTask = data.task_id;
      addLog('编排器', '任务已创建（' + data.task_id + '），开始实时跟踪进度…');
      tickTimer = setInterval(tick, 1000);
      subscribe(data.task_id);
    } catch (e) {
      showFailBanner(e.message);
      addLog('编排器', '启动失败：' + e.message, 'var(--red)');
      showToast(e.message, 'err');
      finish();
    }
  }

  /* ── 初始化 ── */
  resetStates();
  renderStepper();
  renderNetwork();
  animateNetwork();
  runBtn.addEventListener('click', start);
  topicInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); start(); }
  });
})();
