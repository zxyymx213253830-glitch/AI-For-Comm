# -*- coding: utf-8 -*-
"""
Agent 节点 —— OpenTrek 平台版

核心流程：
  1. __init__ → createSession → 获得 sessionId（uniqueCode）
  2. think()  → /run (stream=true) → 解析 SSE → 拼接 message.delta → 返回文本

一个 AgentNode = 1 个 OpenTrek Agent + 1 个独立 Session + 本地消息收件箱
Agent 间的消息传递（send/fetch）走本地 MessageBus → 纯内存，不走网络
"""
import codecs
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime

from core.config import OPENTREK_BASE_URL, APP_KEY, REQUEST_TIMEOUT, SSE_READ_TIMEOUT
from core.logger import log


class AgentNode:
    """一个 Agent 节点 = OpenTrek 控制台已创建好的 Agent"""

    def __init__(self, name: str, agent_code: str, agent_version: str, bus=None, kb_ids=None):
        """
        name:          Agent 名称（如 "math_agent"）
        agent_code:    OpenTrek 控制台的 Agent 编号（UUID）
        agent_version: OpenTrek 控制台的版本编码（数字字符串）
        bus:           MessageBus 实例（填了则 send() 通过总线路由）
        kb_ids:        KB ID 列表（如 ["jka3mxb19y08"]）；填了则 /run 时自动挂载知识库检索
                       （设计参考同学项目 AI_agents_programme/core/agent_node.py）
        """
        if not agent_code or not agent_version:
            raise ValueError(
                f"Agent '{name}' 缺少 agent_code 或 agent_version。"
                "请在 OpenTrek 控制台 → Agent 详情中获取，并填入 core/config.py"
            )

        self.name = name
        self.agent_code = agent_code
        self.agent_version = agent_version
        self.bus = bus
        self.kb_ids = kb_ids or []  # 知识库 ID 列表
        self.inbox = []

        # ── 创建专属会话 ──
        try:
            self.session_id = self._create_session()
            log.info("agent.init",
                     agent=name,
                     agent_code=agent_code,
                     agent_version=agent_version,
                     session_id=self.session_id)
        except Exception as e:
            log.error("agent.init.failed", agent=name, error=str(e))
            raise

        if self.bus:
            self.bus.register(name)

    # ═══════════════════════════════════════════════════
    #  HTTP 工具
    # ═══════════════════════════════════════════════════

    def _request(self, path: str, body: dict, timeout: int = REQUEST_TIMEOUT) -> dict:
        """向 OpenTrek 发送 POST 请求，返回解析后的 JSON"""
        url = f"{OPENTREK_BASE_URL}/{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {APP_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"HTTP {e.code} {e.reason} — {body_text[:300]}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}") from e

    def _request_sse(self, path: str, body: dict,
                     timeout: int = SSE_READ_TIMEOUT,
                     *, collect_thought: bool = False) -> str:
        """
        向 OpenTrek 发送 POST（stream 模式），读取 SSE 流并返回完整响应。

        SSE 格式（新版 OpenTrek）:
          data:{"object":"thought.delta","content":{"data":"思考","type":"text"},...}
          data:{"object":"text.delta",  "content":{"data":"回答","type":"text"},...}
          data:{"object":"message.delta","content":[{"text":{"value":"回答"}}],...}  ← 旧版兼容

        返回: 拼接后的完整回答文本（text.delta + message.delta，不含 thought.delta）
        """
        url = f"{OPENTREK_BASE_URL}/{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {APP_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return self._parse_sse(resp, collect_thought=collect_thought)
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"HTTP {e.code} {e.reason} — {body_text[:300]}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"SSE 网络错误: {e.reason}") from e

    @staticmethod
    def _parse_sse(resp, *, collect_thought: bool = False) -> str:
        """解析 SSE 流，提取最终回答（message.delta / text.delta）。

        SSE 对象类型:
          thought.delta  → 思考过程（默认忽略；collect_thought=True 时缓存作兆底）
          message.delta  → 渲染中的回答文本（累计）
          text.delta     → 新版回答文本（累计）
          complete       → 流结束信号（立即退出）

        collect_thought: 为 True 时同时收集 thought.delta 内容。
            若最终 message 太短（<200字符），自动回退到思考链内容。
            适用场景：sim_agent 等已知“终答只剩收尾语”问题的 Agent。

        加上最大行数保护，防止平台异常时无限等待。
        """
        answer_parts = []
        thought_parts = [] if collect_thought else None
        buffer = ""
        # SSE 按 TCP 分片到达，一个汉字的三个字节可能被切在两个分片上。逐片独立
        # decode(errors="replace") 会把残缺字节变成替换符 ，报告里的乱码就是这么来的；
        # 改用增量解码器，没解完的字节序列留到下一片再解。
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        line_count = 0
        MAX_LINES = 50000  # 安全上限：超过5万行SSE视为异常
        event_types = {}   # 统计各事件类型出现次数（调试用）
        end_reason = "unknown"  # 流结束原因

        while True:
            chunk = resp.read(8192)
            if not chunk:
                buffer += decoder.decode(b"", final=True)
                end_reason = "connection_closed"
                break
            buffer += decoder.decode(chunk)

            lines = buffer.split("\n")
            buffer = lines.pop()  # 最后一行可能不完整

            for line in lines:
                line_count += 1
                if line_count > MAX_LINES:
                    end_reason = "max_lines_exceeded"
                    log.warning("agent.sse.max_lines", lines=line_count)
                    return "".join(answer_parts)  # 异常保护，直接返回已收到的内容

                line = line.strip()
                if not line.startswith("data:"):
                    continue

                json_str = line[5:].strip()
                if not json_str:
                    continue

                # ── [DONE] 信号 ──
                if json_str == "[DONE]":
                    end_reason = "done_signal"
                    log.debug("agent.sse.events", types=event_types, end=end_reason)
                    return "".join(answer_parts)

                try:
                    obj = json.loads(json_str)
                except json.JSONDecodeError:
                    continue

                obj_type = obj.get("object", "")
                content  = obj.get("content", {})

                # 统计事件类型
                event_types[obj_type] = event_types.get(obj_type, 0) + 1

                # ── complete → 流结束，立即退出 ──
                if obj_type == "complete":
                    end_reason = "complete_signal"
                    log.debug("agent.sse.events", types=event_types, end=end_reason)
                    break  # 跳出循环，在后面统一处理兆底逻辑

                # ── thought.delta → 思考过程（可选收集）──
                if obj_type == "thought.delta":
                    if thought_parts is not None:
                        if isinstance(content, dict):
                            thought_parts.append(content.get("data", ""))
                        elif isinstance(content, list) and len(content) > 0:
                            first = content[0]
                            if isinstance(first, dict):
                                text_obj = first.get("text", {})
                                if isinstance(text_obj, dict):
                                    thought_parts.append(text_obj.get("value", ""))

                # ── message.delta → content[0].text.value（主要渲染输出）──
                elif obj_type == "message.delta":
                    if isinstance(content, list) and len(content) > 0:
                        first = content[0]
                        if isinstance(first, dict):
                            text_obj = first.get("text", {})
                            if isinstance(text_obj, dict):
                                answer_parts.append(text_obj.get("value", ""))

                # ── 新版 text.delta → content.data ──
                elif obj_type == "text.delta":
                    if isinstance(content, dict):
                        answer_parts.append(content.get("data", ""))

                # ── 未知事件类型 → 记录调试日志 ──
                elif obj_type not in ("thought.delta",):
                    log.debug("agent.sse.unknown_event", type=obj_type,
                              content_snippet=str(content)[:200])
                    # ── 平台显式错误事件 → 抛出并保留原始 errorMsg（如
                    #    "current agent has been offline"），避免被“空回复”掩盖 ──
                    if obj_type == "error" or (
                            isinstance(content, dict)
                            and (content.get("errorMsg") or content.get("errorName"))):
                        msg = str(content.get("errorMsg")
                                  or content.get("errorName")
                                  or content)[:200]
                        raise RuntimeError(f"平台返回错误（{obj_type}）: {msg}")

        # ── 思考链兆底：当终答太短且思考链有实质内容时，回退到思考链 ──
        answer_text = "".join(answer_parts)
        if (collect_thought and thought_parts
                and len(answer_text.strip()) < 200
                and len("".join(thought_parts)) > 500):
            fallback = "".join(thought_parts)
            log.warning("agent.sse.thought_fallback",
                        answer_len=len(answer_text),
                        thought_len=len(fallback),
                        types=event_types)
            return fallback

        if end_reason != "complete_signal" and end_reason != "done_signal":
            log.warning("agent.sse.ended_unexpectedly", types=event_types,
                         end=end_reason, lines=line_count,
                         answer_len=len(answer_text))
        return answer_text

    # ═══════════════════════════════════════════════════
    #  会话管理
    # ═══════════════════════════════════════════════════

    def _create_session(self) -> str:
        """创建 Agent 会话，返回 uniqueCode（即 sessionId）"""
        resp = self._request("createSession", {
            "agentCode": self.agent_code,
            "agentVersion": self.agent_version,
        })

        if not resp.get("success"):
            raise RuntimeError(f"createSession 失败: {resp}")

        unique_code = resp["data"]["uniqueCode"]
        log.info("agent.session.created",
                 agent=self.name,
                 unique_code=unique_code)
        return unique_code

    # ═══════════════════════════════════════════════════
    #  核心方法
    # ═══════════════════════════════════════════════════

    # sim_agent 等已知“终答只剩收尾语”问题的 Agent，启用思考链兆底
    COLLECT_THOUGHT_AGENTS = {"sim_agent"}

    def think(self, task: str, max_retries: int = 2) -> str:
        """把任务发给 OpenTrek Agent，返回 AI 的最终回复。

        每次调用（含每次重试）都开独立会话：一是避免旧 session 状态污染，
        二是平台对同一会话加了并发锁（errorCode 90010 PROCESS_CONCURRENCY_LOCK
        “当前会话正在处理上个请求,请稍后”）——分段统稿会用 2 个线程并发调同一个
        report_agent，共用会话时两边会互相打死。空回复自动重试最多 max_retries 次。
        """
        log.info("agent.think.start", agent=self.name, task=task[:100])
        last_error = None

        for attempt in range(1, max_retries + 2):
            try:
                # 会话 ID 用局部变量，多线程并发调同一 Agent 时不会互相踩到
                session_id = self._create_session()
                self.session_id = session_id      # 仅作观测，请求本体不依赖它
                log.info("agent.think.new_session", agent=self.name,
                         attempt=attempt, session_id=session_id)

                body = {
                    "sessionId": session_id,
                    "stream": True,
                    "delta": True,
                    "message": {
                        "text": task,
                        "metadata": {},
                        "attachments": [],
                    },
                }
                # ── 挂载知识库检索 ──
                if self.kb_ids:
                    body["knowledge"] = {"baseIds": self.kb_ids}
                    log.debug("agent.think.with_kb", agent=self.name, kb_ids=self.kb_ids)
                text = self._request_sse(
                    "run", body,
                    collect_thought=(self.name in self.COLLECT_THOUGHT_AGENTS))

                if not text or not text.strip():
                    log.warning("agent.think.empty_reply",
                                agent=self.name, attempt=attempt)
                    last_error = RuntimeError(
                        f"Agent '{self.name}' 返回空回复（第 {attempt} 次）"
                    )
                    continue  # 重试

                log.info("agent.think.done", agent=self.name,
                         reply_len=len(text), reply=text[:100])
                return text

            except Exception as e:
                log.error("agent.think.failed", agent=self.name,
                          attempt=attempt, error=str(e))
                last_error = e
                # 网络抖动/网关限流时指数退避（2/4 秒），避免连续猛打加剧连接被重置（WinError 10054/10051）
                if attempt < max_retries + 1:
                    time.sleep(2 ** attempt)
                continue  # 重试

        # 所有重试都失败
        raise last_error

    # ═══════════════════════════════════════════════════
    #  消息传递（本地，不走网络）
    # ═══════════════════════════════════════════════════

    def send(self, to_agent: "AgentNode", msg_type: str, content: str):
        """向另一个节点发消息

        有 bus → 走总线路由；无 bus → 直写对方 inbox
        """
        msg = {
            "from": self.name,
            "to": to_agent.name,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if self.bus:
            self.bus.post(msg)
        else:
            to_agent.inbox.append(msg)

        log.info(
            "agent.message",
            sender=msg["from"],
            receiver=msg["to"],
            type=msg_type,
            via="bus" if self.bus else "direct",
        )
        return msg

    def fetch_messages(self) -> list:
        """从总线取回发给自己的消息"""
        if self.bus:
            return self.bus.fetch(self.name)
        return []
