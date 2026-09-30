# -*- coding: utf-8 -*-
"""报告路由 — 报告列表、在线查看、下载"""
import os
import glob
from datetime import datetime
from flask import Blueprint, render_template, send_file, abort, jsonify

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

report_bp = Blueprint("report", __name__)


@report_bp.route("/reports")
def reports_page():
    """报告列表页"""
    reports = []
    pattern = os.path.join(OUTPUTS_DIR, "research_*.html")
    for fp in sorted(glob.glob(pattern), reverse=True):
        fname = os.path.basename(fp)
        size_kb = os.path.getsize(fp) / 1024
        mtime = os.path.getmtime(fp)
        reports.append({
            "filename": fname,
            "size_kb": round(size_kb, 1),
            "mtime": mtime,
            "time_str": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return render_template("reports.html", reports=reports)


@report_bp.route("/reports/view/<filename>")
def view_report(filename):
    """在线查看报告（新标签页打开）"""
    # 安全检查：防止路径穿越
    if ".." in filename or "/" in filename or "\\" in filename:
        abort(400)
    filepath = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath, mimetype="text/html")


@report_bp.route("/reports/download/<filename>")
def download_report(filename):
    """下载报告"""
    if ".." in filename or "/" in filename or "\\" in filename:
        abort(400)
    filepath = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True, download_name=filename)


@report_bp.route("/api/reports")
def api_reports():
    """报告列表 API"""
    reports = []
    pattern = os.path.join(OUTPUTS_DIR, "research_*.html")
    for fp in sorted(glob.glob(pattern), reverse=True)[:20]:
        fname = os.path.basename(fp)
        size_kb = os.path.getsize(fp) / 1024
        reports.append({
            "filename": fname,
            "size_kb": round(size_kb, 1),
            "url": f"/reports/view/{fname}",
        })
    return jsonify(reports)
