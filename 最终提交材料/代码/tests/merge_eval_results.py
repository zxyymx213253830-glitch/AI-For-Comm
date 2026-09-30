#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评测结果合并器 — 把多批 eval_*.csv 合并成一张全量评分总表（HTML/CSV）

用法:
    python tests/merge_eval_results.py \
        evals/results/eval_20260831_004332.csv \
        evals/results/eval_20260902_090509.csv \
        evals/results/eval_xxxx.csv

输出:
    evals/results/eval_summary_YYYYMMDD_HHMMSS.html / .csv
"""
import csv
import datetime
import html
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KIND_ORDER = {"direct": 0, "judge": 1, "collab": 2}


def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def main():
    if len(sys.argv) < 2:
        print("用法: python tests/merge_eval_results.py <eval1.csv> [eval2.csv ...]")
        sys.exit(1)

    all_rows = []
    for p in sys.argv[1:]:
        full = os.path.join(BASE, p) if not os.path.isabs(p) else p
        rows = load_csv(full)
        print(f"  + {os.path.basename(full)}: {len(rows)} 题")
        all_rows.extend(rows)

    # 去重（同 id 保留最新/后者）
    seen = {}
    for r in all_rows:
        seen[r["id"]] = r
    rows = list(seen.values())

    # 排序：kind（direct/judge/collab）→ id
    rows.sort(key=lambda r: (KIND_ORDER.get(r.get("kind", "direct"), 9), r["id"]))

    def _auto_pass(a):
        a = str(a)
        return ("通过" in a or "命中" in a) and "未通过" not in a

    n_direct = sum(1 for r in rows if r["kind"] == "direct")
    n_judge = sum(1 for r in rows if r["kind"] == "judge")
    n_collab = sum(1 for r in rows if r["kind"] == "collab")
    n_pass = sum(1 for r in rows if _auto_pass(r["auto"]))

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(BASE, "evals", "results")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"eval_summary_{stamp}.csv")
    html_path = os.path.join(out_dir, f"eval_summary_{stamp}.html")

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kind", "agent", "level", "auto", "ok", "time", "len"])
        w.writeheader()
        w.writerows(rows)

    rows_html = ""
    for r in rows:
        auto = str(r["auto"])
        if ("命中" in auto or "通过" in auto) and "未通过" not in auto:
            color = "#0a7d32"
        elif auto == "待人工评分":
            color = "#b26a00"
        else:
            color = "#b00020"
        kind_cn = {"direct": "直答", "judge": "判定", "collab": "协作"}.get(r["kind"], r["kind"])
        rows_html += (
            f"<tr><td>{r['id']}</td><td>{kind_cn}</td><td>{r['agent']}</td>"
            f"<td>{r['level']}</td><td>{r['time']}s</td><td>{r['len']}</td>"
            f"<td style='color:{color};font-weight:bold'>{html.escape(auto)}</td></tr>"
        )

    doc = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>AI for Comm 全量评测总表 {stamp}</title>
<style>
body{{font-family:'Microsoft YaHei',sans-serif;margin:20px;background:#fafafa}}
table{{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
th{{background:#8B0000;color:#fff;padding:8px;text-align:left}}
td{{padding:8px;font-size:13px;border-bottom:1px solid #eee}}
h1{{color:#8B0000}} .meta{{color:#666;font-size:13px;margin-bottom:12px}}
.summary{{display:flex;gap:12px;margin:12px 0}}
.card{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px 20px}}
.card b{{font-size:22px;color:#8B0000}}
</style></head><body>
<h1>🤖 AI for Comm 全量评测总表</h1>
<div class="meta">生成时间：{stamp} ｜ 合并 {len(sys.argv)-1} 批结果 ｜ direct 需人工评分（不计自动通过）</div>
<div class="summary">
  <div class="card">总题数 <b>{len(rows)}</b></div>
  <div class="card">直答 <b>{n_direct}</b></div>
  <div class="card">自动判定 <b>{n_judge + n_collab}</b></div>
  <div class="card">命中/通过 <b>{n_pass}</b></div>
</div>
<table>
<tr><th>ID</th><th>类型</th><th>Agent</th><th>难度</th><th>耗时</th><th>字数</th><th>判定</th></tr>
{rows_html}
</table>
</body></html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)

    print("=" * 60)
    print(f"✅ 合并完成：总 {len(rows)} 题（direct {n_direct} / judge {n_judge} / collab {n_collab}）")
    print(f"   自动命中/通过 {n_pass} 题")
    print(f"  CSV:  {csv_path}")
    print(f"  HTML: {html_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
