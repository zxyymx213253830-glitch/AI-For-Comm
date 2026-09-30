# -*- coding: utf-8 -*-
"""对话路由 — 快问快答（带本地工具回环）"""
from flask import Blueprint, request, jsonify, render_template
from web.routes.helpers import get_agents, route_question
from core.tool_driver import ask_with_tools
from tools import label as tool_label

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def index():
    return render_template("index.html")


@chat_bp.route("/api/chat", methods=["POST"])
def api_chat():
    """快问快答接口：自动路由到专家 Agent，Agent 可自主调用本地工具"""
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    agents = get_agents()
    if not agents:
        return jsonify({"error": "未配置任何 Agent，请先在设置页完成配置"}), 503

    # 路由
    target = route_question(question)
    if target not in agents:
        target = next(iter(agents))

    tools_used = []

    def _on_event(rnd, calls, blocks):
        # rnd=0 是驱动器预跑（本地先真跑 comm_lib / protocol_lookup），rnd>=1 是 Agent 自主申请
        tools_used.extend(c["name"] for c in calls)

    try:
        answer = ask_with_tools(agents[target], question, on_event=_on_event,
                                preflight_ctx=question)
        return jsonify({
            "answer": answer,
            "agent": target,
            "agent_desc": agents[target].description if hasattr(agents[target], "description") else target,
            "tools_used": tools_used,
            "tools_text": "、".join(tool_label(n) for n in dict.fromkeys(tools_used)),
        })
    except Exception as e:
        return jsonify({"error": f"Agent 调用失败: {str(e)[:200]}"}), 500
