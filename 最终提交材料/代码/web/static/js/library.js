/* ==========================================================
   报告库页 — 搜索过滤 + 时间排序
   ========================================================== */
(function () {
  var grid = document.getElementById('reportGrid');
  if (!grid) return;   // 空报告库时无需初始化
  var search = document.getElementById('libSearch');
  var sort = document.getElementById('libSort');
  var empty = document.getElementById('libEmpty');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.report-card'));

  function apply() {
    var q = (search.value || '').trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (c) {
      var hit = !q || c.dataset.name.indexOf(q) >= 0;
      c.style.display = hit ? '' : 'none';
      if (hit) visible++;
    });
    empty.style.display = visible ? 'none' : 'block';

    var ordered = cards.slice().sort(function (a, b) {
      var d = parseFloat(b.dataset.mtime) - parseFloat(a.dataset.mtime);
      return sort.value === 'old' ? -d : d;
    });
    ordered.forEach(function (c) { grid.appendChild(c); });
  }

  search.addEventListener('input', apply);
  sort.addEventListener('change', apply);
})();
