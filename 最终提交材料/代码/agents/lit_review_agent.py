# -*- coding: utf-8 -*-
"""
文献调研 Agent —— 通信领域技术综述

继承 core.agent_node.AgentNode（已支持 kbIds 知识库挂载），封装 OpenTrek 平台上的
lit_review_agent 实例凭证（整合自同学项目 AI_agents_programme，与其共用同一平台/APP_KEY，
配置见 core/config.py 的 AGENTS['lit_review_agent']）。

增强：think 前可选做公网文献检索（arXiv + Semantic Scholar，见 core/lit_search.py），
把检索结果注入 Prompt（RAG 式）。公网不可用时不阻塞，退化为纯平台 KB。
"""
from core.agent_node import AgentNode
from core.config import AGENTS
from core.lit_search import search_literature, format_references
from core.pipeline import FULL_ANSWER_SUFFIX  # 防网关通道"终答只剩收尾语"（sim_agent 教训）


class LitReviewAgent(AgentNode):
    """文献调研 Agent

    覆盖：通信领域（3GPP 协议族、信道编码、调制、组网架构）的
    文献检索、归纳与综述生成。

    增强：think 前可选做公网文献检索（arXiv + Semantic Scholar），
    把检索结果注入 Prompt（RAG 式）。公网不可用时不阻塞，退化为纯平台 KB。
    """

    DOMAIN = "通信领域文献调研与综述"

    def __init__(self, bus=None, web_search: bool = True):
        """
        bus:        MessageBus 实例
        web_search: 是否在调研前做公网文献检索（默认开启，失败自动跳过）
        """
        cfg = AGENTS.get("lit_review_agent", {})
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "lit_review_agent 未配置 agentCode/agentVersion。\n"
                "请将平台 Agent 详情中的编号填入 core/config.py 的 AGENTS['lit_review_agent']。"
            )
        super().__init__(
            name="lit_review_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )
        self.web_search = web_search

    # ── 领域便捷方法 ─────────────────────────────────

    def survey(self, topic: str, use_web: bool | None = None, n_refs: int = 5) -> str:
        """执行一次文献调研，返回结构化综述。

        Args:
            topic:    调研主题，如 "LDPC 码在 5G NR 中的应用"
            use_web:  是否附加公网文献检索（默认取 self.web_search）
            n_refs:   每源检索条数（默认 5，双源最多 10 条）
        Returns:
            AI 的结构化综述文本（含引用来源）
        """
        use_web = self.web_search if use_web is None else use_web
        task = (
            f"文献调研任务\n"
            f"主题：{topic}\n"
            f"要求：按照执行手册的结构化格式输出综述，"
            f"每条论断标注来源（文档编号/版本/章节），最后附参考文献清单。"
        )
        if use_web:
            task = self._attach_web_refs(topic, task, n_refs=n_refs)
        return self.think(task + FULL_ANSWER_SUFFIX)

    def survey_with_angles(self, topic: str, angles: list, use_web: bool | None = None, n_refs: int = 5) -> str:
        """多角度文献调研：强制覆盖指定子问题。

        Args:
            topic:  调研主题
            angles: 子问题清单，如 ["信道编码原理", "5G 标准化现状", "硬件实现复杂度"]
            use_web: 是否附加公网文献检索（默认取 self.web_search）
            n_refs:  每源检索条数（默认 5，双源最多 10 条）
        Returns:
            AI 的综述文本，按指定角度分节
        """
        use_web = self.web_search if use_web is None else use_web
        angle_text = "\n".join(f"  - {a}" for a in angles)
        task = (
            f"文献调研任务\n"
            f"主题：{topic}\n"
            f"必须覆盖以下子问题：\n{angle_text}\n"
            f"要求：按照执行手册的结构化格式输出综述，"
            f"每条论断标注来源，最后附参考文献清单。"
        )
        if use_web:
            task = self._attach_web_refs(topic, task, n_refs=n_refs)
        return self.think(task + FULL_ANSWER_SUFFIX)

    # ── 内部：公网检索注入 ──────────────────────────

    def _attach_web_refs(self, topic: str, task: str, n_refs: int = 5) -> str:
        """检索公网文献并注入 Prompt；失败时原样返回 task。"""
        try:
            papers = search_literature(topic, max_results=n_refs)
            refs = format_references(papers)
            if refs:
                return f"{refs}\n{task}"
            return task
        except Exception as e:
            print(f"[lit_review] 公网检索失败，跳过注入: {e}")
            return task
