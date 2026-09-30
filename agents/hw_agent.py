# -*- coding: utf-8 -*-
"""
硬件实践 Agent —— FPGA / Verilog / 时序

继承 core.agent_node.AgentNode，封装 hw_agent 的 OpenTrek 凭证。

⚠️ 注意：hw_agent 尚未在 OpenTrek 控制台创建。
创建步骤：
  1. 控制台 → Agent 管理 → 新建 Agent
  2. 名称：hw_agent
  3. 模型：qwen-plus（实践手册 5.4 约定）
  4. System Prompt：从 prompts/hw_system.md 复制
  5. 知识库：挂载"FPGA 硬件库"（Verilog 模板、时序约束、Xilinx/Altera 手册）
  6. 拿到 agentCode + agentVersion 后填入 core/config.py 的 AGENTS['hw_agent']
"""
from core.agent_node import AgentNode
from core.config import AGENTS


class HwAgent(AgentNode):
    """硬件实践 Agent

    覆盖：FPGA 开发、Verilog/VHDL 模块、时序约束、接口协议（UART/SPI/I2C）、
            同步/异步 FIFO、状态机设计。
    """

    DOMAIN = "硬件实践（FPGA、Verilog、时序分析）"

    def __init__(self, bus=None):
        cfg = AGENTS.get("hw_agent", {})
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "hw_agent 未配置 agentCode/agentVersion。\n"
                "请先在 OpenTrek 控制台创建 hw_agent（参考本文件顶部注释），\n"
                "然后将 agentCode + agentVersion 填入 core/config.py 的 AGENTS['hw_agent']。"
            )
        super().__init__(
            name="hw_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def generate_verilog(self, spec: str) -> str:
        """根据规格生成 Verilog 模块"""
        task = (
            f"请根据以下规格生成 Verilog 模块：\n"
            f"{spec}\n"
            f"要求：\n"
            f"  1. 完整的 module/always/initial 结构\n"
            f"  2. 关键逻辑加注释\n"
            f"  3. 时序约束（如有）写在 comment 块\n"
            f"  4. 边界条件（复位、满/空、溢出）必须处理"
        )
        return self.think(task)

    def explain_timing(self, module_code: str) -> str:
        """分析一个 Verilog 模块的时序"""
        task = (
            f"请分析以下 Verilog 模块的时序：\n\n"
            f"```verilog\n{module_code}\n```\n\n"
            f"要求：\n"
            f"  1. 关键路径分析\n"
            f"  2. setup/hold 时间裕量\n"
            f"  3. 是否存在异步复位/异步信号的隐患"
        )
        return self.think(task)
