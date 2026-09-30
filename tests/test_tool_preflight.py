# -*- coding: utf-8 -*-
"""本地工具"确定性预跑"回归：保证专家回答里有真实工具数值，而不是纯文本心算。

背景（2026-09-02 用户反馈"几个 agent 输出的都是纯文本"）：
会话日志里 tool.catalog.injected 有 5 条、tool.executed 为 0 条 —— 工具说明书发到了，
模型却从不申请。本测试不依赖平台，用假 Agent 验证驱动器自己会把工具真跑一遍：
  1. 关键词识别：调制方式 / 信道 / 带宽 / 信噪比；
  2. preflight_calls 选型正确、数量受限、无权限 Agent 不预跑；
  3. ask_with_tools 把预跑结果压进首轮提示词并以 round=0 上报；
  4. 预跑与"模型自愿申请"两条通道可以共存，互不干扰。
运行：python tests/test_tool_preflight.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_driver import (                    # noqa: E402
    MAX_PREFLIGHT, _detect_bandwidth, _detect_channel, _detect_scheme,
    _detect_snr_db, _lookup_query, ask_with_tools, preflight_calls,
)

PASSED = [0, 0]


def check(name, cond, detail=""):
    if cond:
        PASSED[0] += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        PASSED[1] += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


class FakeAgent:
    """按脚本依次返回预设回复，并记录每次收到的提示词。"""

    def __init__(self, name, replies):
        self.name = name
        self.replies = list(replies)
        self.prompts = []

    def think(self, prompt, **kw):
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else ""


def only(calls, name):
    return [c for c in calls if c["name"] == name]


# ── 1. 关键词识别 ──────────────────────────────────────────────
def case_detect():
    print("\n[1] 关键词识别")
    check("认出 64QAM（长名优先）",
          _detect_scheme("64QAM 与 QPSK 混合组网") == "64qam")
    check("认出中文别名 正交相移键控",
          _detect_scheme("正交相移键控的误码率") == "qpsk")
    check("无调制信息时返回空串", _detect_scheme("链路预算与覆盖") == "")
    check("瑞利/衰落 → rayleigh", _detect_channel("瑞利衰落信道") == "rayleigh")
    check("默认信道 → awgn", _detect_channel("AWGN 下的门限") == "awgn")
    check("20 MHz → 2e7 Hz", _detect_bandwidth("载波带宽 20 MHz") == 2e7)
    check("100MHz 无空格也可识别", _detect_bandwidth("100MHz 带宽") == 1e8)
    check("3.5GHz 小数带宽", abs(_detect_bandwidth("3.5GHz 频段") - 3.5e9) < 1)
    check("没写带宽时返回 0（由调用方给默认值）",
          _detect_bandwidth("链路预算分析") == 0.0)
    check("信噪比 15 dB → 15.0", _detect_snr_db("信噪比 15 dB 时") == 15.0)
    check("SNR=-3dB 负值", _detect_snr_db("SNR = -3dB") == -3.0)
    check("没写信噪比时默认 10 dB", _detect_snr_db("覆盖分析") == 10.0)
    q = _lookup_query("研究课题：X。你负责的子问题：PUSCH 功率控制参数取值范围。补充：略")
    check("查询串优先取子问题本体且 ≤60 字",
          q.startswith("PUSCH") and len(q) <= 60, q)


# ── 2. 预跑选型 ────────────────────────────────────────────────
def case_plan():
    print("\n[2] 预跑工具选型")
    cap = preflight_calls("math_agent",
                          "研究课题：香农容量与频谱效率 子问题：20 MHz 带宽、SNR 12 dB 下的容量")
    sh = only(cap, "comm_lib")
    check("容量类问题 → comm_lib shannon", bool(sh))
    check("带宽与信噪比按题干取值",
          sh and sh[0]["arguments"]["bandwidth"] == 2e7
          and sh[0]["arguments"]["snr_db"] == 12.0,
          str(sh[0]["arguments"]) if sh else "")
    check("同时带一次本地知识库查询", bool(only(cap, "protocol_lookup")))
    check("预跑数量不超过上限", len(cap) <= MAX_PREFLIGHT, f"{len(cap)} 个")

    ber = preflight_calls("sim_agent", "BPSK 在瑞利衰落信道下的误码率仿真")
    tb = only(ber, "comm_lib")
    check("误码类问题 → comm_lib theo_ber",
          tb and tb[0]["arguments"]["action"] == "theo_ber")
    check("调制与信道按题干识别",
          tb and tb[0]["arguments"]["scheme"] == "bpsk"
          and tb[0]["arguments"]["channel"] == "rayleigh")

    hw = preflight_calls("hw_agent", "16QAM 在瑞利信道下的译码器资源开销")
    tb2 = only(hw, "comm_lib")
    check("瑞利不支持 16QAM 时降级到 qpsk",
          tb2 and tb2[0]["arguments"]["scheme"] == "qpsk",
          str(tb2[0]["arguments"]) if tb2 else "")
    check("hw_agent 现在也有预跑能力（此前只有 run_verilog）", bool(hw))

    check("无工具权限的 Agent 不预跑",
          preflight_calls("lit_review_agent", "误码率与香农容量") == [])
    check("上下文为空时不预跑", preflight_calls("math_agent", "") == [])
    plain = preflight_calls("comm_agent", "PUSCH 的调度流程是怎样的")
    check("关键词不匹配时仍留一次知识库查询",
          not only(plain, "comm_lib") and bool(only(plain, "protocol_lookup")))


# ── 3. 预跑真的执行并注入提示词 ────────────────────────────────
def case_inject():
    print("\n[3] 预跑执行与提示词注入")
    agent = FakeAgent("math_agent", ["【结论】香农容量为 …"])
    events = []
    ans = ask_with_tools(
        agent, "请回答子问题。",
        on_event=lambda r, c, b: events.append((r, [x["name"] for x in c])),
        preflight_ctx="研究课题：香农容量 子问题：20 MHz 带宽、SNR 12 dB 的理论容量")
    p0 = agent.prompts[0]
    check("首轮提示词含预跑段落标题", "【本地工具预跑结果" in p0)
    check("预跑结果带真实执行标记", "〔工具结果 comm_lib｜执行成功〕" in p0)
    check("预跑数值真的算出来了（容量非空）", "信道容量_bps" in p0)
    check("附带引用要求，防模型覆盖真实数值", "以工具结果为准" in p0)
    check("预跑结果压在工具说明书之前，说明书仍在末尾",
          p0.index("【本地工具预跑结果") < p0.index("【本地工具】")
          and p0.rstrip().endswith("则直接一次性给出完整回答。"))
    check("以 round=0 上报工具事件", events and events[0][0] == 0,
          str(events))
    check("上报的工具名含 comm_lib", events and "comm_lib" in events[0][1])
    check("模型不再申请工具时直接定稿", ans.startswith("【结论】")
          and len(agent.prompts) == 1)

    # 无工具权限：完全退化成普通 think
    rep = FakeAgent("report_agent", ["{}"])
    ans2 = ask_with_tools(rep, "统稿", preflight_ctx="香农容量 误码率")
    check("无工具权限的 Agent 不做预跑、不加说明书",
          ans2 == "{}" and "【本地工具预跑结果" not in rep.prompts[0])

    # 关闭预跑：只保留自愿申请通道
    off = FakeAgent("math_agent", ["答"])
    ask_with_tools(off, "问", preflight_ctx="")
    check("preflight_ctx 为空时不预跑", "【本地工具预跑结果" not in off.prompts[0])


# ── 4. 两条通道共存 ────────────────────────────────────────────
def case_coexist():
    print("\n[4] 预跑 + 模型自愿申请共存")
    req = '〔工具请求〕{"name": "sympy_compute", "arguments": ' \
          '{"op": "simplify", "expression": "x+x"}}〔/工具请求〕'
    agent = FakeAgent("math_agent", [req, "【结论】2x（已由符号工具化简）"])
    events = []
    ans = ask_with_tools(
        agent, "请化简 x+x。",
        on_event=lambda r, c, b: events.append((r, [x["name"] for x in c])),
        preflight_ctx="研究课题：误码率 子问题：BPSK 的误码率门限")
    rounds = [r for r, _ in events]
    check("先预跑（round=0）再执行模型申请（round=1）",
          rounds[:2] == [0, 1], str(rounds))
    check("第二轮提示词同时带预跑结果与工具真实结果",
          "【本地工具预跑结果" in agent.prompts[1]
          and "〔工具结果 sympy_compute｜执行成功〕" in agent.prompts[1])
    check("最终返回模型定稿", ans.startswith("【结论】2x"))
    check("工具请求标记已从定稿中剥掉", "〔工具请求〕" not in ans)


if __name__ == "__main__":
    case_detect()
    case_plan()
    case_inject()
    case_coexist()
    print(f"\n总计：{PASSED[0]} 通过 / {PASSED[1]} 失败")
    sys.exit(1 if PASSED[1] else 0)
