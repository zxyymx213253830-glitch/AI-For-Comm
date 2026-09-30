# -*- coding: utf-8 -*-
"""综合性多智能体验收：三道跨领域课题，验证七智能体协作、工具回环与报告质量。

设计要点（2026-09-02 用户要求"弄一些综合性的问题测试，调用多个 agent"）：
  1. 每道课题都天然横跨 原理推导/规范依据/硬件落地/数值验证 四类视角，
     配合拆解质量门（≥3 题且 ≥3 类专家）保证多位专家真实参与；
  2. 逐题 try/except：单题失败只记 FAIL 继续下一题，绝不中途退出；
  3. 全程 flush 输出并落盘 _multi_out.txt，随时可查看进度；
  4. 硬校验：专家覆盖、工具回环是否触发、统稿正文量、报告是否带本地排版兜底。

用法: .venv/Scripts/python.exe tests/run_multi_agent_check.py           # 三题全跑（约 1.5 小时）
      .venv/Scripts/python.exe tests/run_multi_agent_check.py 2         # 只跑课题二（约 28 分钟）
      .venv/Scripts/python.exe tests/run_multi_agent_check.py 1 3       # 跑课题一与课题三
退出码: 0=全部硬校验通过  1=存在失败项
"""
import os
import sys
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus          # noqa: E402
from core.orchestrator import Orchestrator       # noqa: E402
from core.pipeline import ResearchPipeline       # noqa: E402
from main import build_agents                    # noqa: E402

TOPICS = [
    "5G NR 上行共享信道（PUSCH）链路预算与覆盖分析：香农容量理论界、"
    "3GPP 规范中的功率与调制参数、蒙特卡洛覆盖仿真、射频前端硬件约束",
    "Massive MIMO 信道估计：MMSE 与 LS 算法的误差理论、3GPP 参考信号规定、"
    "FPGA 实现复杂度与资源开销、估计精度仿真对照",
    "eMBB 场景 Polar 码与 LDPC 码选型：纠错性能理论界、3GPP 标准化现状、"
    "译码器硬件开销与时序、误码率仿真验证",
]

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "_multi_out.txt")
CHECKS = []


def slog(msg=""):
    print(msg, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    slog(f"      [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def main():
    # 命令行给题号则只跑指定课题（演示与回归时可单题快跑），不给则三题全跑
    picked = [int(a) for a in sys.argv[1:] if a.strip().isdigit()]
    picked = [i for i in picked if 1 <= i <= len(TOPICS)]
    plan = ([(i, TOPICS[i - 1]) for i in dict.fromkeys(picked)]
            if picked else list(enumerate(TOPICS, 1)))

    open(OUT, "w", encoding="utf-8").write("")
    slog("=" * 66)
    slog(f"综合性多智能体验收  {datetime.now():%Y-%m-%d %H:%M:%S}  "
         f"本次跑 {len(plan)}/{len(TOPICS)} 道课题（题号 {[i for i, _ in plan]}）")
    slog("=" * 66)

    bus = MessageBus()
    agents = build_agents(bus)
    slog(f"[0] 已加载 {len(agents)} 个智能体：{', '.join(agents)}")
    orch = Orchestrator(agents)

    union_types, union_tools, reports = set(), set(), []

    for idx, topic in plan:
        slog("\n" + "─" * 66)
        slog(f"[课题 {idx}/{len(TOPICS)}] {topic}")
        slog("─" * 66)
        try:
            pipe = ResearchPipeline(orch, agents)
            r = pipe.run(topic)
        except Exception as e:
            slog(f"      [FAIL] 流水线异常：{e}")
            traceback.print_exc()
            CHECKS.append(False)
            continue

        angles = r["plan"]["angles"]
        types = sorted({a["expert"] for a in angles})
        exps = r["experts"]
        etypes = sorted({e["expert"] for e in exps})
        tools = sorted({t for e in exps for t in (e.get("tools_used") or [])})
        draft = r.get("draft") or {}
        findings = draft.get("findings") or []
        fchars = sum(len(str(f.get("content", ""))) for f in findings)
        rp = r.get("report_path") or ""
        size = os.path.getsize(rp) if rp and os.path.exists(rp) else 0
        html = open(rp, encoding="utf-8").read() if rp and os.path.exists(rp) else ""

        union_types |= set(etypes)
        union_tools |= set(tools)
        if rp:
            reports.append(rp)

        slog(f"      拆解 {len(angles)} 题 → 专家类型 {types}")
        slog(f"      实际作答专家 {etypes}；本地工具 {tools or '（本次未触发）'}")
        slog(f"      综述 {len(r['literature'])} 字；校验 {len(r['verdict'])} 字；"
             f"统稿核心发现 {len(findings)} 节共 {fchars} 字")
        slog(f"      报告 {os.path.basename(rp) or '（无）'} {size/1024:.0f} KB，耗时 {r['elapsed']}s")

        check(f"课题{idx} 拆解覆盖 ≥3 类专家", len(types) >= 3, ",".join(types))
        check(f"课题{idx} 实际作答专家 ≥3 类", len(etypes) >= 3, ",".join(etypes))
        check(f"课题{idx} 每位专家论证 ≥200 字",
              all(len(e.get("answer", "")) >= 200 for e in exps),
              "; ".join(f"{e['expert']}:{len(e.get('answer', ''))}" for e in exps))
        check(f"课题{idx} 校验结论含三级评级",
              any(k in r["verdict"] for k in ("【通过】", "【有条件通过】", "【不通过】")))
        check(f"课题{idx} 统稿核心发现 ≥3 节且 ≥1500 字",
              len(findings) >= 3 and fchars >= 1500, f"{len(findings)} 节 {fchars} 字")
        check(f"课题{idx} 报告存在且带本地排版兜底",
              size > 2048 and "localMarkdown" in html, f"{size/1024:.0f} KB")

    slog("\n" + "=" * 66)
    slog("汇总")
    slog(f"  本次课题合计覆盖专家类型：{sorted(union_types) or '（无）'}")
    slog(f"  本次课题合计触发本地工具：{sorted(union_tools) or '（无）'}")
    check("四类专业专家全部真实参与过", {"math", "comm", "hw", "sim"} <= union_types,
          ",".join(sorted(union_types)))
    check("工具回环至少触发一次", bool(union_tools), ",".join(sorted(union_tools)))
    check("每道课题都产出报告", len(reports) == len(plan),
          f"{len(reports)}/{len(plan)} 份")

    n = sum(CHECKS)
    slog(f"\n总计：{n}/{len(CHECKS)} 项通过  {datetime.now():%H:%M:%S}")
    slog("=" * 66)
    return 0 if all(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
