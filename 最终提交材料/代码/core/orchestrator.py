# -*- coding: utf-8 -*-
"""
协调器 —— 任务分解、路由、聚合
负责将用户问题路由给正确的 Agent，编排多 Agent 协作流程

所有对外问答均经 ask_with_tools：有工具权限的 Agent 自主申请本地工具
（符号数学/仿真执行/文献检索…），无权限的 Agent 自动退化为普通 think()。
"""
from core.logger import log
from core.tool_driver import ask_with_tools


class Orchestrator:
    """协调器：任务分解 → 路由 → 聚合"""

    def __init__(self, agents: dict):
        """
        agents: {"math_agent": math, "verify_agent": verify, ...}
        """
        self.agents = agents

    def route(self, task: str, target_agent: str) -> str:
        """将任务路由到指定 Agent（带本地工具回环）"""
        agent = self.agents.get(target_agent)
        if not agent:
            raise ValueError(f"未知 Agent: {target_agent}")
        log.info("orchestrator.route", task=task[:80], target=target_agent)
        return ask_with_tools(agent, task)

    def dual_verify(self, task: str, solver: str = "math_agent",
                    verifier: str = "verify_agent",
                    max_retries: int = 3) -> dict:
        """求解 + 验证双节点协作，最多重试 3 次"""
        log.info("orchestrator.dual_verify.start", task=task[:80])
        solver_agent = self.agents[solver]
        verifier_agent = self.agents[verifier]

        # 求解方与验证方都可调本地工具：校验方会真用 sympy 复核推导，而不是"目测"
        derivation = ask_with_tools(solver_agent, task)

        for round_num in range(1, max_retries + 2):
            solver_agent.send(verifier_agent, "derivation", derivation)
            msgs = verifier_agent.fetch_messages()
            msg_content = msgs[-1]["content"] if msgs else derivation

            feedback = ask_with_tools(
                verifier_agent,
                f"请检查以下推导是否正确：\n\n{msg_content}"
            )
            verifier_agent.send(solver_agent, "feedback", feedback)

            if feedback.startswith("【通过】"):
                log.info("orchestrator.dual_verify.done",
                         passed=True, rounds=round_num)
                return {
                    "derivation": derivation,
                    "feedback": feedback,
                    "rounds": round_num,
                    "passed": True,
                }

            if round_num > max_retries:
                log.info("orchestrator.dual_verify.done",
                         passed=False, rounds=round_num)
                return {
                    "derivation": derivation,
                    "feedback": feedback,
                    "rounds": round_num,
                    "passed": False,
                }

            log.info("orchestrator.dual_verify.retry",
                     round=round_num, feedback=feedback[:100])
            derivation = ask_with_tools(
                solver_agent,
                f"你之前的推导存在问题：\n{feedback}\n\n请修正后重新给出完整推导。"
            )

        return {
            "derivation": derivation,
            "feedback": feedback,
            "rounds": round_num,
            "passed": False,
        }
