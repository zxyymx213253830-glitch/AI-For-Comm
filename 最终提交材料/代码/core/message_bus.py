# -*- coding: utf-8 -*-
"""
消息总线 —— 发布/订阅模式
Agent 注册邮箱 → 消息按收件人路由 → fetch 取回
纯 Python 内存操作，不走网络
"""
from collections import defaultdict
from core.logger import log


class MessageBus:
    """发布/订阅总线：节点注册邮箱，消息按收件人路由"""

    def __init__(self):
        self._mailboxes = defaultdict(list)

    def register(self, agent_name: str):
        """为一个 Agent 注册邮箱"""
        self._mailboxes[agent_name] = []
        log.info("bus.register", agent=agent_name)

    def post(self, msg: dict):
        """投递消息到指定收件人的邮箱"""
        self._mailboxes[msg["to"]].append(msg)
        log.info("bus.post", sender=msg["from"], receiver=msg["to"], type=msg["type"])

    def fetch(self, agent_name: str) -> list:
        """取出并清空指定 Agent 的收件箱"""
        msgs = self._mailboxes[agent_name]
        self._mailboxes[agent_name] = []
        return msgs
