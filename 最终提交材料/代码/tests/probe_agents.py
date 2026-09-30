# -*- coding: utf-8 -*-
"""单 Agent 平台连通性探测 —— 区分平台暂时性故障 vs 本地代码问题。

用法: .venv/Scripts/python.exe tests/probe_agents.py [comm|lit|all]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus
from main import build_agents

TARGET = sys.argv[1] if len(sys.argv) > 1 else "all"


def probe_comm(agents):
    print("== probe comm_agent（快问快答，无 KB）=", flush=True)
    try:
        a = agents["comm_agent"].think("用一句话说明香农信道容量公式 C=B*log2(1+S/N) 的物理含义。")
        print(f"  [OK] {len(a)} chars: {a[:100]}...")
        return len(a) >= 30
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def probe_lit(agents):
    print("== probe lit_review_agent（KB 挂载 + 公网检索）=", flush=True)
    try:
        b = agents["lit_review_agent"].survey("LDPC 码在 5G NR 中的应用", n_refs=3)
        head = b[:150].replace("\n", " ")
        has_refs = ("参考文献" in b or "[1]" in b)
        print(f"  [OK] {len(b)} chars, 含参考文献清单={has_refs}: {head}...")
        return len(b) >= 200
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    bus = MessageBus()
    agents = build_agents(bus)
    ok = True
    if TARGET in ("comm", "all"):
        ok &= probe_comm(agents)
    if TARGET in ("lit", "all"):
        ok &= probe_lit(agents)
    print("\n结果:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
