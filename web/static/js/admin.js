/* ==========================================================
   设置页 — 平台接入 + Agent 注册表 读写
   ========================================================== */
(function () {
  var original = null;   // 最近一次加载的完整配置（保存时合并，避免丢字段）

  function load() {
    fetch('/api/admin/config').then(function (r) { return r.json(); })
      .then(function (cfg) {
        original = cfg;
        var p = cfg.platform || {};
        document.getElementById('f-baseUrl').value = p.baseUrl || '';
        document.getElementById('f-appKey').value = p.appKey || '';
        document.getElementById('f-timeout').value = p.requestTimeout || 300;
        document.getElementById('f-sse').value = p.sseReadTimeout || 300;
        renderAgents(cfg.agents || {});
      })
      .catch(function (e) { showToast('加载配置失败：' + e.message, 'err'); });
  }

  function renderAgents(agents) {
    var box = document.getElementById('agentList');
    box.innerHTML = '';
    AGENT_ORDER.forEach(function (name) {
      if (!(name in agents)) return;
      var a = agents[name] || {};
      var meta = AGENT_META[name] || { short: name };
      var block = document.createElement('div');
      block.className = 'agent-block';
      block.innerHTML =
        '<div class="agent-head"><b>' + meta.icon + ' ' + esc(meta.short) + ' Agent</b>' +
        '<span>' + esc(name) + (a.description ? ' · ' + esc(a.description) : '') + '</span></div>' +
        '<div class="form-grid">' +
        '<div class="field"><label>智能体编码 agentCode</label><input data-agent="' + esc(name) + '" data-k="agentCode" value="' + esc(a.agentCode || '') + '"></div>' +
        '<div class="field"><label>版本 agentVersion</label><input data-agent="' + esc(name) + '" data-k="agentVersion" value="' + esc(a.agentVersion || '') + '"></div>' +
        '<div class="field span2"><label>知识库 kbIds（多个用英文逗号分隔，可留空）</label>' +
        '<input data-agent="' + esc(name) + '" data-k="kbIds" value="' + esc((a.kbIds || []).join(',')) + '"></div>' +
        '</div>';
      box.appendChild(block);
    });
  }

  function collect() {
    var data = JSON.parse(JSON.stringify(original || { platform: {}, agents: {} }));
    data.platform = data.platform || {};
    data.platform.baseUrl = document.getElementById('f-baseUrl').value.trim();
    data.platform.appKey = document.getElementById('f-appKey').value.trim();
    data.platform.requestTimeout = parseInt(document.getElementById('f-timeout').value, 10) || 300;
    data.platform.sseReadTimeout = parseInt(document.getElementById('f-sse').value, 10) || 300;

    document.querySelectorAll('#agentList input[data-agent]').forEach(function (inp) {
      var name = inp.getAttribute('data-agent');
      var k = inp.getAttribute('data-k');
      data.agents[name] = data.agents[name] || {};
      if (k === 'kbIds') {
        data.agents[name].kbIds = inp.value.split(',')
          .map(function (s) { return s.trim(); })
          .filter(function (s) { return s; });
      } else {
        data.agents[name][k] = inp.value.trim();
      }
    });
    return data;
  }

  async function save() {
    try {
      await api('/api/admin/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(collect())
      });
      showToast('配置已保存并生效', 'ok');
      load();
    } catch (e) {
      showToast('保存失败：' + e.message, 'err');
    }
  }

  /* 密钥显示 / 隐藏 */
  var pwToggle = document.getElementById('pwToggle');
  if (pwToggle) {
    pwToggle.addEventListener('click', function () {
      var inp = document.getElementById('f-appKey');
      inp.type = inp.type === 'password' ? 'text' : 'password';
    });
  }

  document.getElementById('saveBtn').addEventListener('click', save);
  document.getElementById('reloadBtn').addEventListener('click', function () {
    load();
    showToast('已重新加载配置', 'ok');
  });

  load();
})();
