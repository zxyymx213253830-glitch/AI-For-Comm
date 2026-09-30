# -*- coding: utf-8 -*-
"""问题拆解覆盖度回归：保证报告不会只有一两位专家在论证。

不依赖平台，用假 Agent 节点喂规划者输出，验证：
  1. 拆解合格（≥3 题且 ≥3 类专家）时不额外重问；
  2. 拆解只给 2 题时会带补正指令重问，仍不足则本地回填到 3 类；
  3. 5 题全挤在同一类专家时，顶掉重复题换视角；
  4. 规划者不可用时，纯本地回填也能凑够 3 类。
运行：python tests/test_plan_coverage.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pipeline import ResearchPipeline, MIN_ANGLES, MIN_EXPERT_TYPES  # noqa: E402

PASSED = [0, 0]


def check(name, cond, detail=""):
    if cond:
        PASSED[0] += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        PASSED[1] += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


class FakePlanner:
    """按脚本依次返回预设回复，并记录收到的提示词。"""

    name = "comm_agent"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def think(self, prompt, **kw):
        self.calls.append(prompt)
        return self.replies.pop(0) if self.replies else ""


def angles_json(items):
    return json.dumps({"topic": "T", "angles": [{"question": q, "expert": e}
                                                for q, e in items]}, ensure_ascii=False)


def run(topic, replies):
    planner = FakePlanner(replies)
    pipe = ResearchPipeline.__new__(ResearchPipeline)   # 跳过 __init__ 的真实依赖
    pipe.agents = {"comm_agent": planner}
    pipe.steps = []
    pipe.lit = None
    pipe.orch = None
    plan = pipe._plan(topic)
    return plan, pipe, planner


def types_of(plan):
    return sorted({a["expert"] for a in plan["angles"]})


print("\n── case1 拆解一次合格 ──")
plan, _, planner = run("LDPC 编码方案", [angles_json([
    ("LDPC 译码复杂度如何推导", "math"),
    ("5G NR 数据信道编码规范如何规定", "comm"),
    ("译码器并行度与吞吐的工程权衡", "hw"),
])])
check("合格拆解只调用 1 次规划", len(planner.calls) == 1, f"实际 {len(planner.calls)} 次")
check("3 题 3 类专家保留", len(plan["angles"]) == 3 and types_of(plan) == ["comm", "hw", "math"],
      str(types_of(plan)))

print("\n── case2 只拆 2 题：重问 + 回填 ──")
plan, _, planner = run("BPSK 误码率", [
    angles_json([("BPSK 误码率公式推导", "math"), ("AWGN 下 BER 蒙特卡洛验证", "sim")]),
    angles_json([("BPSK 误码率公式推导", "math"), ("AWGN 下 BER 蒙特卡洛验证", "sim")]),
])
check("不合格时带补正指令重问", len(planner.calls) == 2, f"调用 {len(planner.calls)} 次")
check("重问提示词含硬性要求", "至少 3 个" in planner.calls[-1] or "3~5 个" in planner.calls[-1])
check("回填后 ≥3 类专家", len(set(types_of(plan))) >= MIN_EXPERT_TYPES, str(types_of(plan)))
check("回填后 ≥3 题", len(plan["angles"]) >= MIN_ANGLES, f"{len(plan['angles'])} 题")
check("回填题都带 question 文本", all(a["question"].strip() for a in plan["angles"]))

print("\n── case3 5 题全挤同一类 ──")
plan, _, _ = run("帧结构分析", [angles_json([(f"子问题{i}", "comm") for i in range(5)])])
check("单类 5 题被补齐到 ≥3 类", len(set(types_of(plan))) >= MIN_EXPERT_TYPES, str(types_of(plan)))
check("总题数不超上限", len(plan["angles"]) <= 5, f"{len(plan['angles'])} 题")
check("同类多题时 comm 仍保留一题",
      sum(1 for a in plan["angles"] if a["expert"] == "comm") >= 1)

print("\n── case4 规划者不可用 ──")
pipe = ResearchPipeline.__new__(ResearchPipeline)
pipe.agents = {}
pipe.steps = []
plan = pipe._plan("纯本地兜底课题")
check("无规划者仍产出 ≥3 类", len({a["expert"] for a in plan["angles"]}) >= MIN_EXPERT_TYPES,
      str(sorted({a["expert"] for a in plan["angles"]})))
check("planner 标记为 (none)", plan["planner"] == "(none)", plan["planner"])

print("\n── case5 非法输出与消息轨迹 ──")
plan, pipe5, _ = run("非法回复", ["我不会拆，只给你一段散文"])
check("非法输出仍回填到 ≥3 类",
      len({a["expert"] for a in plan["angles"]}) >= MIN_EXPERT_TYPES,
      str(sorted({a["expert"] for a in plan["angles"]})))
check("每题都记入 steps 且类型为 angle@专家",
      len([s for s in pipe5.steps if s["type"].startswith("angle@")]) == len(plan["angles"]),
      f"steps={len(pipe5.steps)} angles={len(plan['angles'])}")
check("回填题的归属专家合法",
      all(a["expert"] in ("math", "comm", "hw", "sim") for a in plan["angles"]))

print("\n" + "=" * 56)
print(f"总计: {PASSED[0]}/{PASSED[0] + PASSED[1]} 项通过")
sys.exit(0 if PASSED[1] == 0 else 1)
