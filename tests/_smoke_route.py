# -*- coding: utf-8 -*-
"""临时冒烟：快问快答通道（orchestrator.route）走工具回环是否真触发工具。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus
from core.orchestrator import Orchestrator
from core.tool_driver import ask_with_tools
from main import build_agents

agents = build_agents(MessageBus())
o = Orchestrator(agents)

calls = []
def _ev(round_no, calls_this, buf):
    calls.extend(c["name"] for c in calls_this)

q = ("请用符号计算工具验证 BPSK 误码率公式 Pb = Q(sqrt(2*Eb/N0))，"
     "并给出 Eb/N0 = 3dB 时的数值（用 sympy_compute 工具）")

# 直接用 ask_with_tools 以便采集工具调用事件
ans = ask_with_tools(agents["math_agent"], q, on_event=_ev)
print("=== 使用的工具:", calls or "（无）")
print("=== 回答前 500 字 ===")
print(ans[:500])
