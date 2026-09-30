# -*- coding: utf-8 -*-
"""
科研任务流水线端到端验收脚本

用法:
    .venv/Scripts/python.exe tests/test_pipeline.py ["可选自定义课题"]

流程: build_agents → ResearchPipeline.run（拆解→文献→并行专家→校验→统稿→渲染）→ 校验落盘
退出码: 0=全部通过  1=验收失败
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus
from core.orchestrator import Orchestrator
from core.pipeline import ResearchPipeline
from main import build_agents

TOPIC = sys.argv[1] if len(sys.argv) > 1 else (
    "LDPC 码在 5G NR 中的应用：编码原理、标准化现状与硬件实现复杂度"
)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join("outputs", f"pipeline_test_{TS}.log")

CHECKS = []


def slog(msg):
    print(msg, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")


def check(name, ok, detail=""):
    CHECKS.append(ok)
    tag = "PASS" if ok else "FAIL"
    line = f"      [{tag}] {name}" + (f" — {detail}" if detail else "")
    slog(line)


def main():
    os.makedirs("outputs", exist_ok=True)
    slog("=" * 60)
    slog(f"科研任务流水线端到端验收  {datetime.now():%Y-%m-%d %H:%M:%S}")
    slog(f"课题: {TOPIC}")
    slog("=" * 60)

    bus = MessageBus()
    agents = build_agents(bus)
    slog(f"\n[0/6] 已加载 {len(agents)} 个 Agent: {', '.join(agents.keys())}")
    if "lit_review_agent" not in agents:
        slog("      [FAIL] lit_review_agent 未加载，无法验收")
        return 1

    orch = Orchestrator(agents)
    pipe = ResearchPipeline(orch, agents)

    slog("\n[1/6] 启动流水线（预计 3~8 分钟）...")
    try:
        r = pipe.run(TOPIC)
    except Exception as e:
        slog(f"      [FAIL] 流水线异常中断: {e}")
        return 1

    # ── 校验 1：问题拆解 ──
    slog("\n[2/6] 校验问题拆解")
    angles = r["plan"]["angles"]
    check("拆解出子问题 ≥1", len(angles) >= 1,
          "; ".join(a["question"][:30] for a in angles))

    # ── 校验 2：文献调研 ──
    slog("\n[3/6] 校验文献调研")
    lit = r["literature"]
    check("综述非空且非降级提示", bool(lit) and not lit.startswith("("),
          f"{len(lit)} 字符")
    check("综述含参考文献清单", ("参考文献" in lit or "[1]" in lit),
          lit[-80:].replace("\n", " "))

    # ── 校验 3：并行专家 ──
    slog("\n[4/6] 校验并行专家")
    exps = r["experts"]
    check("专家回答数 ≥1", len(exps) >= 1,
          ", ".join(e["expert"] for e in exps))
    for e in exps:
        check(f"专家({e['expert']}) 回答有效", len(e.get("answer", "")) >= 80,
              f"{len(e.get('answer', ''))} 字符")

    # ── 校验 4：综合校验结论 ──
    slog("\n[5/6] 校验综合意见")
    v = r["verdict"]
    check("verdict 含三级评级之一",
          ("【通过】" in v or "【有条件通过】" in v or "【不通过】" in v or "通过" in v or "需修正" in v),
          f"{len(v)} 字符")

    # ── 校验 5：报告统稿 ──
    slog("\n[6/7] 校验报告统稿（report_agent）")
    draft = r.get("draft")
    check("统稿 JSON 解析成功", bool(draft),
          f"summary={len(draft.get('summary', ''))} 字, findings={len(draft.get('findings', []))} 条" if draft else "降级：未生成统稿")
    if draft:
        check("统稿字段齐全", bool(draft.get("summary")) and bool(draft.get("conclusion")),
              "; ".join(k for k in draft.keys()))

    # ── 校验 6：HTML 报告 ──
    slog("\n[7/7] 校验 HTML 报告")
    rp = r["report_path"]
    size = os.path.getsize(rp) if rp and os.path.exists(rp) else 0
    check("报告文件存在且 >1KB", size > 1024, f"{rp} ({size} bytes)")
    if rp and os.path.exists(rp) and draft:
        html = open(rp, encoding="utf-8").read()
        check("报告含靛蓝瓷模板与统稿章节",
              ("执行摘要" in html and "靛蓝" in html), "扉页/执行摘要已渲染")

    n_pass = sum(CHECKS)
    slog("\n" + "=" * 60)
    slog(f"总计: {n_pass}/{len(CHECKS)} 项通过 | 耗时 {r['elapsed']}s")
    slog(f"日志: {LOG_PATH}")
    slog("=" * 60)
    return 0 if all(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
