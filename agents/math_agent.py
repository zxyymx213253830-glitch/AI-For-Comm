# -*- coding: utf-8 -*-
"""
数学理论 Agent —— 信息论与通信数学

继承 core.agent_node.AgentNode，封装 math_agent 的 OpenTrek 凭证。
除通用 .think(task) 外，提供几个领域便捷方法。
"""
from core.agent_node import AgentNode
from core.config import AGENTS


class MathAgent(AgentNode):
    """数学理论 Agent

    覆盖领域：香农定理、信道容量、信源/信道编码（LDPC/Polar）、
            调制解调数学推导、典型例题。
    """

    DOMAIN = "信息论与通信数学"

    def __init__(self, bus=None):
        cfg = AGENTS["math_agent"]
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "math_agent 未配置 agentCode/agentVersion。\n"
                "请在 OpenTrek 控制台 → Agent 详情中获取，"
                "并填入 core/config.py 的 AGENTS['math_agent']。"
            )
        super().__init__(
            name="math_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def solve_awgn_capacity(self, bandwidth_mhz: float, snr_db: float) -> str:
        """标准题目：AWGN 信道容量推导

        Args:
            bandwidth_mhz: 带宽（MHz）
            snr_db:       信噪比（dB）
        Returns:
            AI 的完整推导文本（含公式、换算、计算、结果）
        """
        task = (
            f"题目：AWGN 信道容量\n"
            f"已知：带宽 B = {bandwidth_mhz} MHz，信噪比 SNR = {snr_db} dB\n"
            f"要求：使用香农公式 C = B·log₂(1+S/N) 逐步推导，"
            f"含单位换算（dB→线性）、代入计算、最终结果（含单位）。"
        )
        return self.think(task)

    def derive_capacity_change(self, scenario: str) -> str:
        """进阶题：分析某参数变化对容量的影响（例：带宽加倍，容量是否加倍？）"""
        task = (
            f"题目：信道容量变化分析\n"
            f"场景：{scenario}\n"
            f"要求：用香农公式推导并给出结论，"
            f"注意纠正'线性直觉'（如带宽加倍容量是否一定加倍）。"
        )
        return self.think(task)
