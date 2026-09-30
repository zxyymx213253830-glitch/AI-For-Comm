# -*- coding: utf-8 -*-
"""
验证 Agent —— 检查其他 Agent 的推导/计算/代码

继承 core.agent_node.AgentNode，封装 verify_agent 的 OpenTrek 凭证。
不关心消息来源，只关心对错。回复必须二选一：【通过】/【不通过】。
"""
from core.agent_node import AgentNode
from core.config import AGENTS


class VerifyAgent(AgentNode):
    """验证 Agent

    覆盖：公式正确性、单位换算、数值精度、代码语法、时序逻辑、边界条件。
    """

    DOMAIN = "审稿与正确性验证"

    def __init__(self, bus=None):
        cfg = AGENTS["verify_agent"]
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "verify_agent 未配置 agentCode/agentVersion。\n"
                "请在 OpenTrek 控制台 → Agent 详情中获取，"
                "并填入 core/config.py 的 AGENTS['verify_agent']。"
            )
        super().__init__(
            name="verify_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def check_derivation(self, content: str, topic: str = "数学推导") -> str:
        """检查一段推导/计算/代码的正确性

        Args:
            content: 待检查的内容
            topic:   主题（数学推导 / 代码 / 协议 / 硬件）
        Returns:
            回复必须以【通过】或【不通过】开头
        """
        task = (
            f"请检查以下{topic}是否正确：\n\n"
            f"{content}\n\n"
            f"回复格式：必须以【通过】或【不通过】开头，"
            f"通过则列出核对项，不通过则指出错误位置与正确做法。"
        )
        return self.think(task)
