# -*- coding: utf-8 -*-
"""
Web 应用共用工具 — Agent 初始化与路由关键词匹配
"""
import re
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.agent_node import AgentNode
from core.message_bus import MessageBus
from core.orchestrator import Orchestrator
from core.pipeline import ResearchPipeline
from core.config import AGENTS

try:
    from agents.lit_review_agent import LitReviewAgent
except ImportError:
    LitReviewAgent = None

# 模块级缓存（避免每次请求重新初始化）
_agents_cache = None
_bus_cache = None
_orch_cache = None
_pipeline_cache = None

# 快问快答关键词路由
ROUTE_KEYWORDS = {
    "math_agent": ["AWGN", "SNR", "BER", "香农", "信道容量", "互信息", "熵",
                   "编码", "调制", "公式", "推导", "计算"],
    "comm_agent": ["GTP", "S1AP", "NAS", "3GPP", "协议", "信令", "组网",
                   "RRC", "切换", "5G", "4G", "LTE"],
    "hw_agent": ["Verilog", "FPGA", "Vivado", "硬件", "时序", "综合",
                 "RTL", "模块"],
    "sim_agent": ["仿真", "蒙特卡洛", "模拟", "曲线", "BER仿真",
                  "误码率仿真"],
}


def get_agents():
    """获取或初始化全部 Agent（模块级缓存）"""
    global _agents_cache, _bus_cache
    if _agents_cache is not None:
        return _agents_cache

    bus = MessageBus()
    agents = {}
    for name, cfg in AGENTS.items():
        agent_code = cfg.get("agentCode", "")
        agent_version = cfg.get("agentVersion", "")
        if not (agent_code and agent_version):
            continue
        try:
            if name == "lit_review_agent" and LitReviewAgent is not None:
                agents[name] = LitReviewAgent(bus=bus)
            else:
                agents[name] = AgentNode(name, agent_code, agent_version,
                                         bus=bus, kb_ids=cfg.get("kbIds", []))
        except Exception:
            pass

    _agents_cache = agents
    _bus_cache = bus
    return agents


def get_orchestrator():
    global _orch_cache
    if _orch_cache is None:
        _orch_cache = Orchestrator(get_agents())
    return _orch_cache


def get_pipeline():
    global _pipeline_cache
    if _pipeline_cache is None:
        _pipeline_cache = ResearchPipeline(get_orchestrator(), get_agents())
    return _pipeline_cache


def route_question(question: str) -> str:
    """根据关键词将问题路由到最合适的 Agent"""
    scores = {}
    for agent_name, keywords in ROUTE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in question.lower())
        if score > 0:
            scores[agent_name] = score

    if not scores:
        return "comm_agent"  # 默认路由
    return max(scores, key=scores.get)
