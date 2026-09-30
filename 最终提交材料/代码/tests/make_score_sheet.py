#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
direct 题人工评分工作表生成器

把 eval_*.html 里 direct 题的实际输出，与 evals/tasks.json 的 answer_points
标准答案要点对齐，生成一张可交互打分的 HTML 工作表（浏览器里勾要点、打总分）。

用法:
    python tests/make_score_sheet.py \
        evals/results/eval_20260831_004332.html

输出:
    evals/results/score_sheet_YYYYMMDD_HHMMSS.html
"""
import datetime
import html
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_tasks():
    with open(os.path.join(BASE, "evals", "tasks.json"), encoding="utf-8") as f:
        return json.load(f)


def parse_rows(html_path):
    """从 run_eval 生成的 HTML 解析表格行 → [{id, kind, agent, level, time, auto, preview}]"""
    doc = open(html_path, encoding="utf-8").read()
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", doc, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 7:
            continue
        clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
        rows.append({
            "id": clean(tds[0]),
            "kind": clean(tds[1]),
            "agent": clean(tds[2]),
            "level": clean(tds[3]),
            "time": clean(tds[4]),
            "auto": clean(tds[6]),
            "preview": clean(tds[7]) if len(tds) > 7 else "",
        })
    return rows


def main():
    if len(sys.argv) < 2:
        print("用法: python tests/make_score_sheet.py <eval_direct.html>")
        sys.exit(1)

    html_path = sys.argv[1]
    if not os.path.isabs(html_path):
        html_path = os.path.join(BASE, html_path)

    tasks = load_tasks()
    by_id = {t["id"]: t for t in tasks["tasks"]}

    rows = [r for r in parse_rows(html_path) if r["kind"] == "direct"]
    print(f"解析到 {len(rows)} 道 direct 题")

    cards = ""
    for r in rows:
        t = by_id.get(r["id"], {})
        points = t.get("answer_points", [])
        criteria = t.get("criteria", [])
        pts_html = "".join(
            f"<li><label class='pt'><input type='checkbox' class='pt-cb' "
            f"onchange='updateScore(this)'>{html.escape(p)}</label></li>"
            for p in points
        )
        cri_html = "、".join(html.escape(c) for c in criteria)
        preview = html.escape(r["preview"])
        cards += f"""
<div class="card" id="{r['id']}">
  <div class="card-head">
    <span class="badge">{r['id']}</span>
    <span class="tag">{r['agent']}</span>
    <span class="tag lv{html.escape(r['level'])}">{html.escape(r['level'])}</span>
    <span class="tag">{html.escape(r['time'])}</span>
    <span class="score-box">得分 <input type="number" class="score" min="0" max="3" step="0.5" value="0"
      onchange="updateScoreFromNum(this)" oninput="syncCb(this)"> / 3</span>
  </div>
  <div class="q"><b>题目：</b>{html.escape(t.get('question', ''))}</div>
  <div class="cols">
    <div class="col pts">
      <div class="col-title">✅ 标准要点（勾选命中项）</div>
      <ul>{pts_html}</ul>
      <div class="criteria">评分维度：{cri_html}</div>
    </div>
    <div class="col out">
      <div class="col-title">🤖 Agent 实际输出（前 300 字）</div>
      <pre>{preview}</pre>
      <details><summary>备注</summary>
        <textarea class="note" rows="2" placeholder="人工备注..."></textarea>
      </details>
    </div>
  </div>
</div>"""

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(BASE, "evals", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"score_sheet_{stamp}.html")

    doc = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>AI for Comm direct 题人工评分表</title>
<style>
body{{font-family:'Microsoft YaHei',sans-serif;margin:20px;background:#f5f5f5}}
h1{{color:#8B0000}} .meta{{color:#666;font-size:13px;margin-bottom:16px}}
.card{{background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.12);
      margin-bottom:16px;padding:14px 18px}}
.card-head{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}}
.badge{{background:#8B0000;color:#fff;font-weight:bold;padding:3px 10px;border-radius:12px}}
.tag{{background:#eee;color:#333;padding:3px 10px;border-radius:12px;font-size:12px}}
.lvS{{background:#e3f2e3}}.lvM{{background:#fff3d6}}.lvH{{background:#fde2e2}}
.score-box{{margin-left:auto;font-size:13px;color:#333}}
.score{{width:52px;font-size:15px;text-align:center;border:1px solid #ccc;border-radius:6px;padding:2px}}
.q{{color:#333;margin-bottom:10px;font-size:14px}}
.cols{{display:flex;gap:16px;flex-wrap:wrap}}
.col{{flex:1;min-width:280px}}
.col-title{{font-weight:bold;color:#555;margin-bottom:8px;font-size:13px}}
.pt{{display:block;padding:4px 0;font-size:13px;color:#333;cursor:pointer}}
.pt input{{margin-right:8px;transform:scale(1.2)}}
.criteria{{color:#888;font-size:12px;margin-top:8px}}
pre{{background:#fafafa;border:1px solid #e8e8e8;border-radius:6px;padding:10px;
    font-size:12px;white-space:pre-wrap;word-break:break-all;max-height:260px;overflow:auto;color:#333}}
.note{{width:100%;border:1px solid #ccc;border-radius:6px;padding:6px;font-size:13px}}
summary{{cursor:pointer;color:#8B0000;font-size:13px}}
.progress{{position:sticky;top:0;background:#fff;border-bottom:2px solid #8B0000;
          padding:10px 20px;z-index:10;display:flex;gap:16px;align-items:center}}
.progress b{{color:#8B0000;font-size:18px}}
#saveBtn{{background:#8B0000;color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:14px}}
</style></head><body>
<div class="progress">
  <b>direct 题人工评分（{len(rows)} 题）</b>
  <span>已勾选：<span id="doneCount">0</span>/{len(rows)}</span>
  <button id="saveBtn" onclick="saveSheet()">💾 导出评分 JSON</button>
</div>
<h1>✅ AI for Comm — direct 题人工评分工作表</h1>
<div class="meta">对照 tasks.json 的 answer_points 逐题勾选命中要点，得分 0-3（错/部分对/对/对且完整）。
勾选全部要点后自动记 3 分。页面底部点"导出评分 JSON"下载打分结果。</div>

{cards}

<div style="text-align:center;margin:20px">
  <button onclick="saveSheet()" style="background:#8B0000;color:#fff;border:none;
    border-radius:8px;padding:10px 30px;font-size:16px;cursor:pointer">💾 导出评分 JSON</button>
</div>

<script>
function cbCount(card){{
  const cbs = card.querySelectorAll('.pt-cb');
  let n = 0; cbs.forEach(c => {{ if (c.checked) n++; }});
  return n;
}}
function updateScore(elm){{
  const card = elm.closest('.card');
  const total = card.querySelectorAll('.pt-cb').length;
  const hit = cbCount(card);
  const num = card.querySelector('.score');
  if (hit === total) {{ num.value = 3; }}
  else if (hit > 0) {{ num.value = num.value || 1; }}
  else {{ num.value = 0; }}
  refreshDone();
}}
function updateScoreFromNum(elm){{
  const card = elm.closest('.card');
  const hit = cbCount(card), total = card.querySelectorAll('.pt-cb').length;
  const v = parseFloat(elm.value) || 0;
  if (v === 3 && hit < total) {{
    card.querySelectorAll('.pt-cb').forEach(c => c.checked = true);
  }}
  if (v === 0) {{ card.querySelectorAll('.pt-cb').forEach(c => c.checked = false); }}
  refreshDone();
}}
function syncCb(elm){{ /* 数字输入实时同步到勾选状态 */ }}
function refreshDone(){{
  const cards = document.querySelectorAll('.card');
  let n = 0;
  cards.forEach(c => {{ if (parseFloat(c.querySelector('.score').value) > 0) n++; }});
  document.getElementById('doneCount').textContent = n;
}}
function saveSheet(){{
  const cards = document.querySelectorAll('.card');
  const out = {{}};
  cards.forEach(c => {{
    const id = c.id;
    const score = parseFloat(c.querySelector('.score').value) || 0;
    const note = c.querySelector('.note') ? c.querySelector('.note').value : '';
    const hit = [];
    c.querySelectorAll('.pt-cb').forEach(cb => {{ if (cb.checked) hit.push(cb.closest('.pt').textContent.trim()); }});
    out[id] = {{ score: score, hit: hit, note: note }};
  }});
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'score_result_' + new Date().toISOString().slice(0,10) + '.json';
  a.click();
}}
</script>
</body></html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"✅ 评分工作表已生成：{out_path}")


if __name__ == "__main__":
    main()
