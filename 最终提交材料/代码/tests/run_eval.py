#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评测集执行器 — 跑 `evals/tasks.json` 里的题目，输出评分表（HTML/CSV）

用法:
    python tests/run_eval.py                      # 跑全部
    python tests/run_eval.py --agent math_agent   # 只跑某个 Agent
    python tests/run_eval.py --mode direct        # 只跑单题直答
    python tests/run_eval.py --mode judge         # 只跑 verify 判定题
    python tests/run_eval.py --mode collab        # 只跑协作闭环
    python tests/run_eval.py --limit 5            # 限制题数（调试用）

结果:
    evals/results/eval_YYYYMMDD_HHMMSS.html / .csv

说明:
    - direct 题：自动记录输出/耗时，答案正确性标"待人工评分"（可在 HTML 里打分）
    - judge 题：自动比对 verify 输出中的【通过】/【不通过】与预期
    - collab 题：用 dual_verify 闭环，自动取 passed
"""
import argparse
import csv
import datetime
import html
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from core.config import AGENTS
from core.message_bus import MessageBus
from core.orchestrator import Orchestrator

from agents.math_agent import MathAgent
from agents.verify_agent import VerifyAgent
from agents.comm_agent import CommAgent
from agents.hw_agent import HwAgent
from agents.lit_review_agent import LitReviewAgent
from agents.sim_agent import SimAgent
from agents.report_agent import ReportAgent

AGENT_CLASSES = {
    "math_agent": MathAgent,
    "verify_agent": VerifyAgent,
    "comm_agent": CommAgent,
    "hw_agent": HwAgent,
    "lit_review_agent": LitReviewAgent,
    "sim_agent": SimAgent,
    "report_agent": ReportAgent,
}


def load_tasks(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_direct(agent_name, question, timeout):
    """单 Agent 直答；sim_agent 走真执行闭环（think_verified）"""
    t0 = time.time()
    agent = AGENT_CLASSES[agent_name]()
    try:
        if agent_name == "sim_agent" and hasattr(agent, "think_verified"):
            res = agent.think_verified(question, timeout=timeout)
            out = res["final_text"]
            # 把真执行结果附在输出头部，供评分/回看（HTML 预览取前 300 字）
            exec_ = res.get("exec") or {}
            meta = (
                f"──[真执行]────────────────────────────\n"
                f"代码提取: {'✓' if res.get('code') else '✗ 未提取到代码块'}\n"
                f"退出码:   {exec_.get('returncode', 'N/A')}\n"
                f"输出图片: {exec_.get('pngs', [])}\n"
                f"stderr:   {str(exec_.get('stderr', ''))[-200:]}\n"
                f"备注:     {res.get('note', '')}\n"
                f"──────────────────────────────────────\n"
            )
            out = meta + out
        else:
            out = agent.think(question)
        ok = True
    except Exception as e:
        out = f"[EXCEPTION] {type(e).__name__}: {str(e)[:300]}"
        ok = False
    return ok, out, time.time() - t0


def run_judge(question, timeout):
    """verify_agent 判定题"""
    t0 = time.time()
    agent = VerifyAgent()
    q = question + "\n\n请直接以【通过】或【不通过】开头给出结论，再展开分析。"
    try:
        out = agent.think(q)
        ok = True
    except Exception as e:
        out = f"[EXCEPTION] {type(e).__name__}: {str(e)[:300]}"
        ok = False
    return ok, out, time.time() - t0


def run_collab(solver_name, question, timeout):
    """solver → verify 协作闭环（dual_verify）；sim_agent 走真执行"""
    t0 = time.time()
    bus = MessageBus()
    solver = AGENT_CLASSES[solver_name](bus=bus)
    # sim_agent 在协作里也走 think_verified，verify 才能基于真实结果校验
    if solver_name == "sim_agent" and hasattr(solver, "think_verified"):
        _sim = solver
        _orig_think = solver.think  # 原始平台调用（think_verified 内部依赖 self.think）
        def _sim_think_wrapped(task):
            # think_verified 内部会调 self.think → 必须先解除覆盖，否则无限递归
            _sim.think = _orig_think
            try:
                res = _sim.think_verified(task)
            finally:
                _sim.think = _sim_think_wrapped  # 恢复 wrapper，供 orchestrator 重试再走闭环
            exec_ = res.get("exec") or {}
            meta = (
                f"\n\n──[真执行]────────────────────────────\n"
                f"代码提取: {'✓' if res.get('code') else '✗ 未提取到代码块'}\n"
                f"退出码:   {exec_.get('returncode', 'N/A')}\n"
                f"输出图片: {exec_.get('pngs', [])}\n"
                f"备注:     {res.get('note', '')}\n"
                f"──────────────────────────────────────\n"
            )
            return meta + res["final_text"]
        solver.think = _sim_think_wrapped
    verifier = VerifyAgent(bus=bus)
    orch = Orchestrator({solver_name: solver, "verify_agent": verifier})
    try:
        r = orch.dual_verify(task=question, solver=solver_name,
                             verifier="verify_agent", max_retries=2)
        out = (f"【推导】{r.get('derivation', '')[:400]}\n"
               f"【反馈】{r.get('feedback', '')[:200]}")
        passed = r.get("passed", False)
        return passed, out, time.time() - t0
    except Exception as e:
        return False, f"[EXCEPTION] {type(e).__name__}: {str(e)[:300]}", time.time() - t0


def expect_pass(task):
    """从 judge 题 answer_points 提取预期判定"""
    if task.get("mode") != "judge":
        return None
    for p in task.get("answer_points", []):
        if "应判【" in p:
            return "【通过】" in p  # True=通过, False=不通过
    return None


def judge_match(expect, output):
    """比对 verify 实际判定与预期"""
    if expect is None:
        return None
    got_pass = "【通过】" in output
    got_fail = "【不通过】" in output
    if got_pass and not got_fail:
        got = True
    elif got_fail:
        got = False
    else:
        return "无法解析判定"
    return "✅ 命中" if got == expect else "❌ 判反"


def main():
    ap = argparse.ArgumentParser(description="AI for Comm 评测集执行器")
    ap.add_argument("--agent", default=None, help="只跑某 Agent")
    ap.add_argument("--level", default=None, help="S/M/H")
    ap.add_argument("--mode", default="all", choices=["direct", "judge", "collab", "all"])
    ap.add_argument("--limit", type=int, default=0, help="最多跑 N 题")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--exclude", default="",
                    help="逗号分隔要跳过的任务 id，如 --exclude collab-03")
    args = ap.parse_args()
    excl = {x.strip() for x in args.exclude.split(",") if x.strip()}

    data = load_tasks(os.path.join(BASE, "evals", "tasks.json"))
    results = []

    def run_task(task, kind):
        if task["id"] in excl:
            return
        if args.agent and task.get("agent") != args.agent and task.get("solver") != args.agent:
            return
        if args.level and task.get("level") != args.level:
            return
        q = task["question"]
        if kind == "direct":
            ok, out, dt = run_direct(task["agent"], q, args.timeout)
            auto = "待人工评分"
        elif kind == "judge":
            ok, out, dt = run_judge(q, args.timeout)
            auto = judge_match(expect_pass(task), out) if ok else "❌ 调用失败"
        else:
            passed, out, dt = run_collab(task["solver"], q, args.timeout)
            ok = passed
            auto = "✅ 通过" if passed else "❌ 未通过"
        name = task.get("agent") or task.get("solver")
        print(f"  [{kind:6s}] {task['id']:12s} {name:16s} {dt:6.1f}s  {auto}")
        results.append({
            "id": task["id"], "kind": kind, "agent": name,
            "level": task.get("level", "-"),
            "auto": auto, "ok": ok, "time": round(dt, 1),
            "len": len(out), "output": out,
        })

    tasks = data.get("tasks", [])
    collab = data.get("collab", [])
    print("=" * 70)
    print("AI for Comm 评测集执行中 ...")
    print("=" * 70)

    if args.mode in ("all", "direct"):
        print("\n── 单题直答（direct）──")
        n = 0
        for t in tasks:
            if t.get("mode") == "judge":
                continue
            if args.limit and n >= args.limit:
                break
            run_task(t, "direct")
            n += 1
    if args.mode in ("all", "judge"):
        print("\n── verify 判定（judge）──")
        n = 0
        for t in tasks:
            if t.get("mode") != "judge":
                continue
            if args.limit and n >= args.limit:
                break
            run_task(t, "judge")
            n += 1
    if args.mode in ("all", "collab"):
        print("\n── 协作闭环（collab）──")
        n = 0
        for t in collab:
            if args.limit and n >= args.limit:
                break
            run_task(t, "collab")
            n += 1

    # ── 输出报告 ──
    if not results:
        print("没有匹配的题目。")
        return
    os.makedirs(os.path.join(BASE, "evals", "results"), exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(BASE, "evals", "results", f"eval_{stamp}.csv")
    html_path = os.path.join(BASE, "evals", "results", f"eval_{stamp}.html")

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kind", "agent", "level", "auto", "ok", "time", "len"])
        w.writeheader()
        w.writerows({k: r[k] for k in ["id", "kind", "agent", "level", "auto", "ok", "time", "len"]} for r in results)

    n_pass = sum(1 for r in results if r["ok"] and ("通过" in str(r["auto"]) or "命中" in str(r["auto"])))
    n_total = len(results)
    rows_html = ""
    for r in results:
        color = "green" if ("通过" in str(r["auto"]) and r["ok"]) else "orange" if r["auto"] == "待人工评分" else "red"
        out_preview = html.escape(r["output"][:300]).replace("\n", "<br>")
        rows_html += (
            f"<tr style='border-bottom:1px solid #eee'>"
            f"<td>{r['id']}</td><td>{r['kind']}</td><td>{r['agent']}</td><td>{r['level']}</td>"
            f"<td>{r['time']}s</td><td>{r['len']}</td>"
            f"<td style='color:{color};font-weight:bold'>{r['auto']}</td>"
            f"<td style='font-size:11px;color:#555'>{out_preview}</td></tr>"
        )
    html_doc = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>AI for Comm 评测结果 {stamp}</title>
<style>
body{{font-family:'Microsoft YaHei',sans-serif;margin:20px;background:#fafafa}}
table{{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
th{{background:#8B0000;color:#fff;padding:8px;text-align:left}}
td{{padding:8px;vertical-align:top;font-size:13px}}
h1{{color:#8B0000}} .meta{{color:#666;font-size:13px}}
</style></head><body>
<h1>🤖 AI for Comm 评测报告</h1>
<div class="meta">生成时间：{stamp} ｜ 通过 {n_pass}/{n_total}（自动判定口径）<br>
direct=待人工评分不计入通过；judge/collab=自动判定</div>
<br>
<table>
<tr><th>ID</th><th>类型</th><th>Agent</th><th>难度</th><th>耗时</th><th>字数</th><th>判定</th><th>输出预览</th></tr>
{rows_html}
</table>
</body></html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print("\n" + "=" * 70)
    print(f"✅ 完成：{n_total} 题，自动判定通过 {n_pass}")
    print(f"  CSV:  {csv_path}")
    print(f"  HTML: {html_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
