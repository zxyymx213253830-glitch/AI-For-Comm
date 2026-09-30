# -*- coding: utf-8 -*-
"""
AI for Comm 集中配置管理 —— OpenTrek 平台版（JSON 外部化）

学校平台是 OpenTrek（非百炼公有云），API 走 HTTP 直接调用。
配置数据存储在项目根目录 config.json，通过 ConfigManager 读取。

API 文档（详见项目根目录 PDF）：
  1. createSession    → 创建 Agent 会话，返回 uniqueCode
  2. /run（stream）    → 发起对话，SSE 流式返回
  3. createNewChannel → SSE 长连接（复杂场景用，本项目暂不需要）
  4. 知识库检索        → 直接检索知识库内容
"""
from typing import Dict
from core.config_manager import ConfigManager

# 初始化配置管理器（单例）
_mgr = ConfigManager()

# ── OpenTrek API 端点（从 config.json 读取）─────────────────
OPENTREK_BASE_URL: str = _mgr.base_url
APP_KEY: str = _mgr.app_key

# ── 超时配置 ────────────────────────────────────────────
REQUEST_TIMEOUT: int = _mgr.request_timeout
SSE_READ_TIMEOUT: int = _mgr.sse_read_timeout

# ── Agent 注册表（从 config.json 读取）──────────────────────
AGENTS: Dict[str, dict] = _mgr.agents
