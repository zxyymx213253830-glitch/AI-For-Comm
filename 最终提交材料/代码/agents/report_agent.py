# -*- coding: utf-8 -*-
"""
汇报 Agent —— 科研汇报聚合

继承 core.agent_node.AgentNode，封装 report_agent 的 OpenTrek 凭证。

⚠️ 需要先在 OpenTrek 控制台创建 report_agent：
  1. 控制台 → 新建 Agent
  2. 名称：report_agent
  3. System Prompt：prompts/report_system.md 全文
  4. 发布后拿到 agentCode + agentVersion
  5. 填入 core/config.py 的 AGENTS['report_agent']

用法：把各 Agent 的产出收集成 {agent_name: text}，调 compile_report() 生成汇报。
"""
from core.agent_node import AgentNode
from core.config import AGENTS


class ReportAgent(AgentNode):
    """汇报 Agent —— 聚合各 Agent 产出生成科研汇报"""

    DOMAIN = "科研汇报"

    def __init__(self, bus=None):
        cfg = AGENTS.get("report_agent", {})
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "report_agent 未配置 agentCode/agentVersion。\n"
                "请先在 OpenTrek 控制台创建 report_agent"
                "（System Prompt 用 prompts/report_system.md），\n"
                "然后将 agentCode + agentVersion 填入 core/config.py 的 AGENTS['report_agent']。"
            )
        super().__init__(
            name="report_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def compile_report(self, title: str, materials: dict,
                       audience: str = "组会") -> str:
        """聚合各 Agent 产出，生成科研汇报

        Args:
            title:     汇报题目
            materials: {agent_name: 该 Agent 的原始产出文本}
            audience:  "组会" / "导师汇报"
        Returns:
            汇报 Agent 生成的完整汇报文本
        """
        if not materials:
            raise ValueError("materials 为空：至少传入一个 Agent 的产出")

        blocks = []
        for agent_name, text in materials.items():
            blocks.append(f"### 来源：{agent_name}\n{text}\n")
        materials_block = "\n".join(blocks)

        task = (
            f"请根据以下各 Agent 的产出，生成一份面向{audience}的科研汇报。\n"
            f"汇报题目：{title}\n\n"
            f"【各 Agent 原始产出】\n{materials_block}\n\n"
            f"要求：按固定结构输出（摘要/研究问题/方法/结果/结论/"
            f"局限与下一步/材料清单），数据不得编造，未覆盖的部分标注'待补充'。"
        )
        return self.think(task)
