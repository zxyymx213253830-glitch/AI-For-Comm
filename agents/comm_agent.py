# -*- coding: utf-8 -*-
"""
通信工程 Agent —— 3GPP 协议、信令流程、信道分析

继承 core.agent_node.AgentNode，封装 comm_agent 的 OpenTrek 凭证。

⚠️ 注意：comm_agent 尚未在 OpenTrek 控制台创建。
创建步骤：
  1. 控制台 → Agent 管理 → 新建 Agent
  2. 名称：comm_agent
  3. 模型：qwen-plus（实践手册 5.4 约定）
  4. System Prompt：从 prompts/comm_system.md 复制
  5. 知识库：挂载"通信协议库"（3GPP TS 29.274 / 36.413 / 38.413 等）
  6. 拿到 agentCode + agentVersion 后填入 core/config.py 的 AGENTS['comm_agent']
"""
from core.agent_node import AgentNode
from core.config import AGENTS


class CommAgent(AgentNode):
    """通信工程 Agent

    覆盖：3GPP 协议族（GTPv2/S1AP/NGAP/NAS）、信令流程、
            信道分析、GPPP 协议 IE 字段。
    """

    DOMAIN = "通信工程（3GPP 协议、信令流程）"

    def __init__(self, bus=None):
        cfg = AGENTS.get("comm_agent", {})
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "comm_agent 未配置 agentCode/agentVersion。\n"
                "请先在 OpenTrek 控制台创建 comm_agent（参考本文件顶部注释），\n"
                "然后将 agentCode + agentVersion 填入 core/config.py 的 AGENTS['comm_agent']。"
            )
        super().__init__(
            name="comm_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def query_protocol(self, question: str) -> str:
        """查询 3GPP 协议相关问题（需配合 RAG 知识库）"""
        task = (
            f"问题：{question}\n"
            f"要求：\n"
            f"  1. 引用具体规范编号（如 TS 29.274 V17.x.x）\n"
            f"  2. 引用章节号（如 5.5.1.2.1）\n"
            f"  3. 如有必选/可选 IE，列出字段名\n"
            f"  4. 不确定时明说'不确定'，禁止编造"
        )
        return self.think(task)

    def explain_ie(self, protocol: str, ie_name: str) -> str:
        """解释某个协议 IE 字段"""
        task = (
            f"请解释 {protocol} 协议中的 {ie_name} 字段：\n"
            f"  - 所在消息\n  - 取值范围\n  - 必选/可选\n  - 典型场景"
        )
        return self.think(task)
