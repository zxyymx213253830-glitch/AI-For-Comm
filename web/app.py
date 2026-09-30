# -*- coding: utf-8 -*-
"""
AI for Comm — Flask Web 应用主入口
"""
import os
import sys

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
app.config["SECRET_KEY"] = os.urandom(24).hex()

# ── 注册路由蓝图 ─────────────────────────────────────
from web.routes.chat import chat_bp
from web.routes.pipeline import pipeline_bp
from web.routes.report import report_bp
from web.routes.admin import admin_bp

app.register_blueprint(chat_bp)
app.register_blueprint(pipeline_bp)
app.register_blueprint(report_bp)
app.register_blueprint(admin_bp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"\n  AI for Comm Web 服务启动中…")
    print(f"  访问地址: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
