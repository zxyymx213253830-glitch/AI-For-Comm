# -*- coding: utf-8 -*-
"""
AI for Comm —— 通信领域多智能体协作系统 CLI 入口

使用方式：
  1. 在 OpenTrek 控制台创建 Agent 并绑定知识库
  2. 将 agentCode 和 agentVersion 填入 core/config.py
  3. python main.py
"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_node import AgentNode
from core.message_bus import MessageBus
from core.orchestrator import Orchestrator
from core.pipeline import ResearchPipeline
from core.logger import log
from core.config import AGENTS
try:
    from agents.lit_review_agent import LitReviewAgent
except ImportError as _e:
    LitReviewAgent = None
    print(f"[警告] lit_review_agent 模块加载失败: {_e}")


def build_agents(bus: MessageBus) -> dict:
    """加载已在 OpenTrek 控制台创建好的 Agent 节点"""
    agents = {}

    for name, cfg in AGENTS.items():
        agent_code = cfg.get("agentCode", "")
        agent_version = cfg.get("agentVersion", "")

        if not (agent_code and agent_version):
            log.info("main.build", agent=name, status="no_config")
            continue

        try:
            # lit_review_agent 使用子类（自带公网检索增强，kbIds 在类内读取）
            if name == "lit_review_agent" and LitReviewAgent is not None:
                agents[name] = LitReviewAgent(bus=bus)
            else:
                agents[name] = AgentNode(name, agent_code, agent_version,
                                         bus=bus, kb_ids=cfg.get("kbIds", []))
            log.info("main.build", agent=name, status="loaded")
        except Exception as e:
            log.error("main.build.failed", agent=name, error=str(e))
            print(f"[警告] Agent '{name}' 初始化失败: {e}")

    return agents


def main():
    log.info("main.start")
    print("=" * 60)
    print("  AI for Comm —— 通信领域多智能体协作系统")
    print("=" * 60)

    bus = MessageBus()
    agents = build_agents(bus)

    if not agents:
        print("\n[提示] 尚未配置任何 Agent。")
        print("请先在 OpenTrek 控制台创建 Agent，然后将 agentCode 和 agentVersion 填入 core/config.py")
        return

    orch = Orchestrator(agents)
    pipeline = ResearchPipeline(orch, agents)   # 科研任务流水线
    print(f"\n已加载 {len(agents)} 个 Agent: {', '.join(agents.keys())}")
    print("─" * 60)
    print("双模式用法：")
    print("  ① 快问快答 —— 直接输入问题，按关键词自动路由到对应专家")
    print("  ② 科研任务 —— 输入 `科研: <课题>` 触发六步流水线")
    print("     （拆解→文献调研→并行专家→校验→报告统稿→靛蓝瓷渲染），约 3~8 分钟")
    print("─" * 60)
    print("输入题目开始（输入 quit 退出）\n")

    while True:
        try:
            task = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not task:
            continue
        if task.lower() == "quit":
            break

        math_kw = ["AWGN", "SNR", "dB", "信道容量", "香农", "互信息",
                   "熵", "编码", "调制", "MIMO", "数学", "推导"]
        comm_kw = ["GTP", "S1AP", "3GPP", "TS 29", "TS 36", "TS 38",
                   "协议", "信令", "IE", "Cause", "NAS"]
        hw_kw   = ["Verilog", "FPGA", "FIFO", "硬件", "时序", "clock",
                   "模块", "always", "寄存器"]
        # 注意：BER 区分大小写匹配，避免命中英文单词里的 ber 子串
        sim_kw  = ["仿真", "蒙特卡洛", "蒙特卡罗", "误码率", "BER", "Eb/N0", "星座图"]
        lit_kw  = ["综述", "文献", "调研", "survey"]

        try:
            # ── 科研任务模式：`科研:` / `research:` 前缀一键触发六步流水线 ──
            m_pipe = re.match(r"^(?:科研|研究|research)[:：]\s*(.+)", task, re.IGNORECASE)
            if m_pipe and "lit_review_agent" in agents:
                result = pipeline.run(m_pipe.group(1).strip())
                print(f"\n{'=' * 60}\n课题: {result['topic']}")
                print(f"\n── 文献综述 ──\n{result['literature']}")
                for e_ in result["experts"]:
                    print(f"\n── 专家({e_['expert']}) ── {e_['question']}\n{e_['answer']}")
                print(f"\n── 综合校验 ──\n{result['verdict']}")
                tail = f"总耗时 {result['elapsed']}s"
                if result["report_path"]:
                    tail += f"，报告: {result['report_path']}"
                print(f"\n{tail}")
                continue

            if any(kw in task for kw in lit_kw) and "lit_review_agent" in agents:
                # 单轮文献调研走子类的 survey()（带公网检索增强）
                print(agents["lit_review_agent"].survey(task))
            elif any(kw.lower() in task.lower() for kw in hw_kw) and "hw_agent" in agents:
                print(orch.route(task, "hw_agent"))
            elif any(kw in task for kw in sim_kw) and "sim_agent" in agents:
                # 追加"一次写全四章节"指令，避免网关通道只收到收尾语
                sim_task = task + AGENTS["sim_agent"].get("requireFullAnswer", "")
                print(orch.route(sim_task, "sim_agent"))
            elif any(kw in task for kw in comm_kw) and "comm_agent" in agents:
                print(orch.route(task, "comm_agent"))
            elif any(kw in task for kw in math_kw):
                if "math_agent" in agents and "verify_agent" in agents:
                    result = orch.dual_verify(task)
                    print("\n── 推导 ──")
                    print(result["derivation"])
                    print("\n── 验证 ──")
                    print(result["feedback"])
                else:
                    print("[提示] 需要 math_agent + verify_agent 才能进行双节点验证")
            else:
                if "math_agent" in agents and "verify_agent" in agents:
                    result = orch.dual_verify(task)
                    print("\n── 推导 ──")
                    print(result["derivation"])
                    print("\n── 验证 ──")
                    print(result["feedback"])
                elif "math_agent" in agents:
                    print(orch.route(task, "math_agent"))
                else:
                    print("[提示] 无法识别题目类型")
        except Exception as e:
            print(f"[错误] {e}")
            log.error("main.error", error=str(e))

    log.info("main.end")


if __name__ == "__main__":
    main()
