# -*- coding: utf-8 -*-
"""
全局日志系统 —— structlog → JSONL
所有操作（init / think / message / error）统一落盘到 logs/session.jsonl
"""
import structlog
import os

# 使用绝对路径，确保无论从哪个目录运行都能正确写入
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=open(os.path.join(LOG_DIR, "session.jsonl"), "a", encoding="utf-8")
    ),
)

log = structlog.get_logger()
