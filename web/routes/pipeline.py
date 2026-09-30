# -*- coding: utf-8 -*-
"""科研任务路由 — 流水线启动 + SSE 实时进度"""
import json
import uuid
import threading
import time
from queue import Queue, Empty
from flask import Blueprint, request, jsonify, render_template, Response
from web.routes.helpers import get_pipeline

pipeline_bp = Blueprint("pipeline", __name__)

# 任务存储：{task_id: {"queue": Queue, "result": dict|None, "status": str}}
_tasks = {}


@pipeline_bp.route("/research")
def research_page():
    return render_template("pipeline.html")


@pipeline_bp.route("/api/pipeline/start", methods=["POST"])
def start_pipeline():
    """启动科研流水线任务"""
    data = request.get_json(force=True)
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "课题不能为空"}), 400

    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        "queue": Queue(),
        "result": None,
        "status": "running",
        "started_at": time.time(),
    }

    # 后台线程运行流水线
    def run_task():
        task = _tasks[task_id]
        q = task["queue"]

        def on_progress(step_id, step_name, status, detail=""):
            q.put({
                "event": "progress",
                "step_id": step_id,
                "step_name": step_name,
                "status": status,
                "detail": detail,
            })

        try:
            pipeline = get_pipeline()
            result = pipeline.run(topic, on_progress=on_progress)
            task["result"] = result
            task["status"] = "done"
            q.put({"event": "complete", "report_path": result.get("report_path", "")})
        except Exception as e:
            task["status"] = "error"
            q.put({"event": "error", "message": str(e)[:300]})
        finally:
            q.put({"event": "end"})

    t = threading.Thread(target=run_task, daemon=True)
    t.start()

    return jsonify({"task_id": task_id})


@pipeline_bp.route("/api/pipeline/progress/<task_id>")
def pipeline_progress(task_id):
    """SSE 端点：实时推送进度事件"""
    task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    def generate():
        q = task["queue"]
        while True:
            try:
                msg = q.get(timeout=120)
            except Empty:
                # 超时心跳
                yield "data: {}\n\n"
                continue

            if msg.get("event") == "end":
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@pipeline_bp.route("/api/pipeline/result/<task_id>")
def pipeline_result(task_id):
    """获取任务结果"""
    task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    if task["status"] == "running":
        return jsonify({"status": "running"})
    elif task["status"] == "error":
        return jsonify({"status": "error"})
    else:
        result = task["result"]
        return jsonify({
            "status": "done",
            "topic": result.get("topic"),
            "verdict": result.get("verdict", "")[:200],
            "elapsed": result.get("elapsed"),
            "report_path": result.get("report_path", ""),
            "experts_count": len(result.get("experts", [])),
        })
