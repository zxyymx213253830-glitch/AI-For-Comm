# -*- coding: utf-8 -*-
"""
分段统稿离线回归测试（不联网、不调平台）

覆盖 2026-09-02 内容量恢复改造：
  1. 正常路径：每位专家各 1 次分节统稿 + 1 次全局统稿 → 合并后 findings 为 600~800 字量级
  2. 分节失败：退化为专家原文直录（degraded），正文不缩水
  3. 全局失败：仅全局字段走本地机械拼装补齐，分节内容保持
  4. 平台全挂：_compile_report 返回 None，由 run() 上层 _fallback_draft 兜底

用法: python tests/test_compile_split.py
退出码: 0=全部通过  1=有失败
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.pipeline as P

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


class FakeAgent:
    """只满足 ask_with_tools 需要的最小接口（本测试里 ask_with_tools 被打桩）。"""
    name = "report_agent"


MATH_ANSWER = "BPSK 误码率推导：设发送符号 s∈{+√Eb, -√Eb}，" + "相干判决下 Pe=Q(√(2Eb/N0))。" * 60
SIM_ANSWER = "蒙特卡洛仿真：N=1e6 比特，Eb/N0 取 0~10dB，统计误比特数除以总比特数。" * 50
PLAN = {"topic": "BPSK 在 AWGN 信道下的误码率理论推导与仿真验证",
        "planner": "comm_agent",
        "angles": [{"question": "推导 BPSK 在 AWGN 下的误码率", "expert": "math"},
                   {"question": "蒙特卡洛仿真验证误码率曲线", "expert": "sim"}]}
EXPERTS = [
    {"question": PLAN["angles"][0]["question"], "extra": [], "expert": "math",
     "agent": "math_agent", "answer": MATH_ANSWER, "tools_used": ["符号数学推演"]},
    {"question": PLAN["angles"][1]["question"], "extra": [], "expert": "sim",
     "agent": "sim_agent", "answer": SIM_ANSWER, "tools_used": ["Python 仿真执行"]},
]
LITERATURE = "香农 1948 给出信道容量框架。" * 80
VERDICT = "【通过】理论式与仿真值在 1dB 内一致，量纲核对无误。" * 20


def _draft_json(summary="", background="", findings=None, cross="", conclusion="",
                outlook="", keywords=None):
    return json.dumps({
        "summary": summary, "background": background,
        "findings": findings or [], "cross_analysis": cross,
        "conclusion": conclusion, "outlook": outlook,
        "keywords": keywords if keywords is not None else ["BPSK", "AWGN", "误码率"],
    }, ensure_ascii=False)


def make_pipeline(handler):
    """构造流水线并把 ask_with_tools 打桩为 handler(agent, prompt)。"""
    P.ask_with_tools = handler
    return P.ResearchPipeline(orch=None, agents={"report_agent": FakeAgent()})


# ════════════════════════════════════════════════════════
def case_all_ok():
    calls = []

    def handler(agent, prompt, on_event=None):
        calls.append(prompt)
        if "分节统稿子任务" in prompt:
            expert = "math" if "math_agent" in prompt.split("来源专家")[1][:20] else "sim"
            return _draft_json(findings=[{
                "title": f"{expert} 节标题", "expert": expert,
                "content": "推导要点保留公式 $P_b=Q(\\sqrt{2E_b/N_0})$ 与数值。" * 25}])
        return _draft_json(summary="摘要" * 100, background="背景" * 200,
                           cross="交叉分析" * 200, conclusion="【通过】结论" * 100,
                           outlook="展望" * 80)

    pipe = make_pipeline(handler)
    draft = pipe._compile_report(PLAN, LITERATURE, EXPERTS, VERDICT)
    digest_calls = [c for c in calls if "分节统稿子任务" in c]
    all_text = "\n===\n".join(digest_calls)
    check("正常路径产出 draft", bool(draft))
    check("调用次数 = 2 分节 + 1 全局", len(calls) == 3, f"实际 {len(calls)} 次")
    check("分节输入含专家完整原文尾部（不再被截到 1200 字）",
          all(e["answer"][-60:] in all_text for e in EXPERTS),
          f"分节输入长度={[len(c) for c in digest_calls]}")
    check("核心发现 2 节", draft and len(draft["findings"]) == 2,
          f"{len(draft['findings'])} 节" if draft else "")
    check("每节正文恢复到 300 字以上",
          draft and all(len(f["content"]) >= 300 for f in draft["findings"]),
          f"各节字数={[len(f['content']) for f in draft['findings']] if draft else ''}")
    check("全局字段齐备", draft and all(draft.get(k) for k in
                             ("summary", "background", "cross_analysis",
                              "conclusion", "outlook", "keywords")))
    check("未被标记为降级", draft and not any(f.get("degraded") for f in draft["findings"]))


def case_digest_fails():
    calls = []

    def handler(agent, prompt, on_event=None):
        calls.append(prompt)
        if "分节统稿子任务" in prompt:
            raise RuntimeError("平台返回错误：格式化流程超时")
        return _draft_json(summary="摘要" * 100, conclusion="【通过】" * 50,
                           background="背景" * 100, cross="交叉" * 100, outlook="展望" * 50)

    pipe = make_pipeline(handler)
    draft = pipe._compile_report(PLAN, LITERATURE, EXPERTS, VERDICT)
    check("分节全失败仍产出 draft", bool(draft))
    check("分节按 COMPILE_ATTEMPTS 重试",
          len([c for c in calls if "分节统稿子任务" in c]) == 4,
          f"分节调用 {len([c for c in calls if '分节统稿子任务' in c])} 次")
    check("失败节退化为原文直录",
          draft and all(f.get("degraded") for f in draft["findings"]))
    check("原文直录保留 1000 字以上",
          draft and all(len(f["content"]) >= 1000 for f in draft["findings"]),
          f"各节字数={[len(f['content']) for f in draft['findings']] if draft else ''}")


def case_global_fails():
    def handler(agent, prompt, on_event=None):
        if "分节统稿子任务" in prompt:
            return _draft_json(findings=[{"title": "节", "expert": "x",
                                          "content": "统稿正文。" * 60}])
        raise RuntimeError("网络错误: timed out")

    pipe = make_pipeline(handler)
    draft = pipe._compile_report(PLAN, LITERATURE, EXPERTS, VERDICT)
    check("全局失败仍产出 draft", bool(draft))
    check("全局字段本地补齐", draft and draft["summary"] and draft["conclusion"])
    check("分节内容不受全局失败影响",
          draft and all(not f.get("degraded") for f in draft["findings"])
          and len(draft["findings"]) == 2,
          f"{[len(f['content']) for f in draft['findings']] if draft else ''}")


def case_platform_dead():
    def handler(agent, prompt, on_event=None):
        raise RuntimeError("current agent has been offline")

    pipe = make_pipeline(handler)
    draft = pipe._compile_report(PLAN, LITERATURE, EXPERTS, VERDICT)
    check("平台全挂时返回 None 交上层兜底", draft is None, repr(draft))
    fb = pipe._fallback_draft(PLAN, LITERATURE, EXPERTS, VERDICT)
    check("本地兜底 findings 为专家原文（≥800 字）",
          all(len(f["content"]) >= 800 for f in fb["findings"]),
          f"各节字数={[len(f['content']) for f in fb['findings']]}")
    check("本地兜底带降级标记", fb.get("degraded") is True)


def case_parse_tolerant():
    pipe = make_pipeline(lambda a, p, on_event=None: "")
    good = ('```json\n'
            + json.dumps({"findings": [{"title": "t", "expert": "math",
                                        "content": "文" * 200}]}, ensure_ascii=False)
            + '\n```')
    d = pipe._parse_draft(good, require_field="findings")
    check("围栏 + 分节解析成功", d and d["findings"])
    bad = '{"summary": "非法转义 \\sqrt{x} 未双写", "findings": []}'
    d2 = pipe._parse_draft(bad)
    check("LaTeX 非法转义被修复", d2 and "\\sqrt" in d2["summary"], repr(d2)[:60] if d2 else "None")
    cut = '{"summary": "' + "摘要内容" * 40 + '", "background": "' + "背景" * 30
    d3 = pipe._parse_draft(cut)
    check("截断 JSON 可抢救出 summary", d3 and len(d3["summary"]) > 100,
          f"{len(d3['summary'])} 字" if d3 else "None")
    check("空输入返回 None", pipe._parse_draft("") is None)


def main():
    for fn in (case_all_ok, case_digest_fails, case_global_fails,
               case_platform_dead, case_parse_tolerant):
        print(f"\n── {fn.__name__} ──")
        fn()
    n_pass, n_total = sum(CHECKS), len(CHECKS)
    print(f"\n总计: {n_pass}/{n_total} 项通过")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
