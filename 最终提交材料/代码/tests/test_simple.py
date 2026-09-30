# -*- coding: utf-8 -*-
"""
双节点最小闭环测试 —— 阶段三验收脚本

前提：已在 OpenTrek 控制台创建 math_agent 和 verify_agent，
      并将 agentCode + agentVersion 填入 core/config.py

运行方式：
  终端：   python tests/test_simple.py
  同学：   在文件夹双击 run_test.bat
"""
import sys
import os
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from core.agent_node import AgentNode
from core.message_bus import MessageBus
from core.config import AGENTS
from core.report import generate_report

# ── 日志文件路径 ───────────────────────────────────
LOG_DIR  = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def slog(msg):
    """同时打印到终端和写入日志文件"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

# ── 启动日志 ───────────────────────────────────────
slog("=" * 60)
slog(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
slog(f"  日志文件: {LOG_FILE}")
slog("=" * 60)

# ── 检查配置 ───────────────────────────────────────
math_cfg   = AGENTS.get("math_agent", {})
verify_cfg = AGENTS.get("verify_agent", {})

if not math_cfg.get("agentCode") or not math_cfg.get("agentVersion"):
    slog("[ERROR] math_agent not configured. Please fill agentCode & agentVersion in core/config.py")
    exit(1)
if not verify_cfg.get("agentCode") or not verify_cfg.get("agentVersion"):
    slog("[ERROR] verify_agent not configured. Please fill agentCode & agentVersion in core/config.py")
    exit(1)

# ── 创建消息总线 ───────────────────────────────────
bus = MessageBus()

# ── 加载已在控制台创建好的 Agent ───────────────────
math_agent   = AgentNode("math_agent",   math_cfg["agentCode"],   math_cfg["agentVersion"],   bus=bus)
verify_agent = AgentNode("verify_agent", verify_cfg["agentCode"], verify_cfg["agentVersion"], bus=bus)

# ── 测试题目 ──────────────────────────────────────
task = "AWGN信道，带宽B=20MHz，信噪比SNR=30dB，求信道容量。请逐步推导。"

slog("=" * 60)
slog("  Test: Dual-Agent Closed Loop")
slog(f"  Task: {task}")
slog("=" * 60)

_start = time.time()

# 1. 数学 Agent 推导
slog("\n[1/4] Math Agent deriving...")
derivation = math_agent.think(task)
if len(derivation) < 50:
    slog("  [WARN] Reply too short, retrying...")
    derivation = math_agent.think(task)
slog(f"  [OK] Done ({len(derivation)} chars)")

# 2. MessageBus 路由
slog("[2/4] MessageBus routing...")
math_agent.send(verify_agent, "derivation", derivation)
slog("  [OK] Sent")

# 3. 验证 Agent 检查
slog("[3/4] Verify Agent checking...")
msgs = verify_agent.fetch_messages()
msg  = msgs[0] if msgs else {}
feedback = verify_agent.think(
    f"请检查以下推导是否正确：\n{msg.get('content', derivation)}"
)
slog("  [OK] Done")

# 4. 回发
verify_agent.send(math_agent, "feedback", feedback)

_elapsed = int(time.time() - _start)

# ── 输出结果 ──────────────────────────────────────
slog(f"\n{'='*30} Derivation {'='*30}")
slog(derivation)
slog(f"\n{'='*30} Feedback {'='*30}")
slog(feedback)

# ── HTML 报告 + 日志 ─────────────────────────────
report_path = generate_report(derivation, feedback, total_time=str(_elapsed))
slog(f"\n{'='*30} Files {'='*30}")
slog(f"  HTML Report: {report_path}")
slog(f"  Terminal Log: {LOG_FILE}")

try:
    os.startfile(report_path)
    slog("  Browser opened with HTML report")
except Exception:
    slog(f"  Please open manually: {report_path}")

slog(f"\n-- Checklist --")
slog("  - Should contain: log2(1+1000)")
slog("  - Expected result: ~199.5 Mbps")
slog(f"  - Total time: {_elapsed}s")
slog("  - Logs: logs/session.jsonl")
slog("  - Messages routed via MessageBus")

# ── 完成后自动弹出终端窗口，显示日志 ──────────────
try:
    os.system(f'start "AI-for-Comm Results" cmd /k type "{LOG_FILE}"')
except Exception:
    pass
