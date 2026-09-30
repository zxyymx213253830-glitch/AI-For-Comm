/* ==========================================================
   智能体监控页 — 真实配置驱动的注册与健康总览
   ========================================================== */
(function () {
  var statGrid = document.getElementById('statGrid');
  var agentGrid = document.getElementById('agentGrid');

  function hostOf(url) {
    try { return new URL(url, location.href).host; } catch (e) { return url || '—'; }
  }

  function renderStats(cfg, reportCount) {
    var agents = (cfg && cfg.agents) || {};
    var platform = (cfg && cfg.platform) || {};
    var ready = AGENT_ORDER.filter(function (k) {
      var a = agents[k];
      return a && a.agentCode && a.agentVersion;
    }).length;
    var kbTotal = AGENT_ORDER.reduce(function (n, k) {
      return n + (((agents[k] || {}).kbIds || []).length);
    }, 0);
    statGrid.innerHTML =
      '<div class="glass stat-card"><div class="lb">已注册智能体</div><div class="vl">' + ready + ' <small>/ 7</small></div><div class="tr">编码与版本配置齐全即视为就绪</div></div>' +
      '<div class="glass stat-card"><div class="lb">知识库绑定</div><div class="vl">' + kbTotal + ' <small>个</small></div><div class="tr">全部智能体累计</div></div>' +
      '<div class="glass stat-card"><div class="lb">已生成研究报告</div><div class="vl">' + reportCount + '</div><div class="tr">报告库累计成果</div></div>' +
      '<div class="glass stat-card"><div class="lb">平台接入地址</div><div class="vl" style="font-size:16px">' + esc(hostOf(platform.baseUrl)) + '</div><div class="tr">请求超时 ' + (platform.requestTimeout || 300) + ' 秒</div></div>';
  }

  function renderAgents(cfg) {
    var agents = (cfg && cfg.agents) || {};
    agentGrid.innerHTML = AGENT_ORDER.map(function (k) {
      var a = agents[k] || {};
      var meta = AGENT_META[k];
      var ready = !!(a.agentCode && a.agentVersion);
      var kb = a.kbIds || [];
      return '<div class="glass agent-card card ' + (ready ? '' : 'off') + '">' +
        '<div class="aic">' + meta.icon + '</div>' +
        '<div style="flex:1;min-width:0">' +
        '<h4>' + esc(meta.short) + ' Agent <span class="st ' + (ready ? 'st-online' : 'st-offline') + '"><i class="d"></i>' + (ready ? '已注册' : '未配置') + '</span></h4>' +
        '<div class="ds">' + esc(a.description || meta.desc) + '</div>' +
        '<div class="kb-tags">' + (kb.length
          ? kb.map(function (id) { return '<span class="tag">知识库 ' + esc(id) + '</span>'; }).join('')
          : '<span class="tag">未绑定知识库</span>') + '</div>' +
        '<div class="ft"><span>' + esc(a.agentVersion ? '版本 ' + a.agentVersion : '—') + '</span><span>知识库 ' + kb.length + ' 个</span></div>' +
        '</div></div>';
    }).join('');
  }

  Promise.all([
    api('/api/admin/config').catch(function () { return {}; }),
    fetch('/api/reports').then(function (r) { return r.json(); }).catch(function () { return []; })
  ]).then(function (res) {
    renderStats(res[0], (res[1] || []).length);
    renderAgents(res[0]);
  });
})();
