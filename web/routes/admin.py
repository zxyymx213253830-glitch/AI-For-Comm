# -*- coding: utf-8 -*-
"""配置管理路由 — Agent 配置读写"""
from flask import Blueprint, request, jsonify, render_template
from core.config_manager import ConfigManager

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/settings")
def settings_page():
    return render_template("admin.html")


@admin_bp.route("/monitor")
def monitor_page():
    """智能体监控页"""
    return render_template("monitor.html")


@admin_bp.route("/api/admin/config", methods=["GET"])
def get_config():
    """读取全部配置"""
    mgr = ConfigManager()
    return jsonify(mgr.to_dict())


@admin_bp.route("/api/admin/config", methods=["PUT"])
def save_config():
    """保存配置"""
    mgr = ConfigManager()
    data = request.get_json(force=True)

    # 更新 platform 配置
    if "platform" in data:
        platform = data["platform"]
        if "baseUrl" in platform:
            mgr.set("platform.baseUrl", platform["baseUrl"])
        if "appKey" in platform:
            mgr.set("platform.appKey", platform["appKey"])
        if "requestTimeout" in platform:
            mgr.set("platform.requestTimeout", int(platform["requestTimeout"]))
        if "sseReadTimeout" in platform:
            mgr.set("platform.sseReadTimeout", int(platform["sseReadTimeout"]))

    # 更新 agents 配置
    if "agents" in data:
        for agent_name, agent_cfg in data["agents"].items():
            mgr.set(f"agents.{agent_name}", agent_cfg)

    # 校验并保存
    errors = mgr.validate()
    if errors:
        return jsonify({"errors": errors}), 400

    mgr.save()
    return jsonify({"success": True})


@admin_bp.route("/api/admin/agents", methods=["GET"])
def get_agents_config():
    """获取 Agent 列表配置"""
    mgr = ConfigManager()
    return jsonify(mgr.agents)


@admin_bp.route("/api/admin/agents", methods=["PUT"])
def save_agents_config():
    """保存 Agent 列表配置"""
    mgr = ConfigManager()
    data = request.get_json(force=True)
    mgr.set("agents", data)
    errors = mgr.validate()
    if errors:
        return jsonify({"errors": errors}), 400
    mgr.save()
    return jsonify({"success": True})
