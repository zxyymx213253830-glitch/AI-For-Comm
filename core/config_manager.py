# -*- coding: utf-8 -*-
"""
配置管理器 — 读写 config.json，提供校验和热重载
"""
import json
import os
import copy
from typing import Dict, Optional

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

# 默认配置（config.json 缺失时的兜底）
DEFAULT_CONFIG = {
    "platform": {
        "baseUrl": (
            "http://<platform-host>:80"
            "/sfm-agent-studio/sfm-api-gateway/gateway/agent/api"
        ),
        "appKey": "YOUR_APP_KEY",
        "requestTimeout": 300,
        "sseReadTimeout": 300,
    },
    "agents": {},
}


class ConfigManager:
    """配置管理器单例"""

    _instance: Optional["ConfigManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._config = copy.deepcopy(DEFAULT_CONFIG)
            self.load()
            self._loaded = True

    def load(self) -> dict:
        """从 config.json 加载配置"""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并默认值（JSON 中缺失的字段用默认值补全）
            self._config = self._merge_defaults(data)
        return self._config

    def save(self) -> None:
        """保存当前配置到 config.json"""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key_path: str, default=None):
        """
        用点分路径获取配置值
        例: get("platform.baseUrl"), get("agents.math_agent.kbIds")
        """
        keys = key_path.split(".")
        node = self._config
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    def set(self, key_path: str, value) -> None:
        """用点分路径设置配置值"""
        keys = key_path.split(".")
        node = self._config
        for k in keys[:-1]:
            if k not in node:
                node[k] = {}
            node = node[k]
        node[keys[-1]] = value

    @property
    def platform(self) -> dict:
        return self._config.get("platform", {})

    @property
    def agents(self) -> Dict[str, dict]:
        return self._config.get("agents", {})

    @property
    def base_url(self) -> str:
        return self.platform.get("baseUrl", DEFAULT_CONFIG["platform"]["baseUrl"])

    @property
    def app_key(self) -> str:
        return self.platform.get("appKey", DEFAULT_CONFIG["platform"]["appKey"])

    @property
    def request_timeout(self) -> int:
        return self.platform.get("requestTimeout", 300)

    @property
    def sse_read_timeout(self) -> int:
        return self.platform.get("sseReadTimeout", 300)

    def reload(self) -> dict:
        """热重载：重新从文件读取"""
        return self.load()

    def validate(self) -> list:
        """校验配置完整性，返回错误列表（空=通过）"""
        errors = []
        if not self.base_url:
            errors.append("platform.baseUrl 不能为空")
        if not self.app_key:
            errors.append("platform.appKey 不能为空")
        for name, agent in self.agents.items():
            if not agent.get("agentCode"):
                errors.append(f"agents.{name}.agentCode 缺失")
            if not agent.get("agentVersion"):
                errors.append(f"agents.{name}.agentVersion 缺失")
        return errors

    def _merge_defaults(self, data: dict) -> dict:
        """将用户配置与默认值合并"""
        merged = copy.deepcopy(DEFAULT_CONFIG)
        # 合并 platform
        if "platform" in data:
            merged["platform"].update(data["platform"])
        # 合并 agents（以数据为准）
        if "agents" in data:
            merged["agents"] = data["agents"]
        return merged

    def to_dict(self) -> dict:
        """返回完整配置副本"""
        return copy.deepcopy(self._config)
