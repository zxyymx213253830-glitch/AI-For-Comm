# web/ —— Web 应用层（Flask 多页面前端 + 接口路由）

启动入口 `app.py`（默认 7860 端口），页面全部中文界面：

- `templates/` —— 6 个页面：对话（index）、科研流水线（pipeline）、报告库（reports）、
  智能体监控（monitor）、设置（admin）、公共骨架（base）
- `static/css/` —— 全站样式（深海军蓝/琥珀金主题、波形动画、步骤进度条）
- `static/js/` —— 各页脚本：app（公共工具）、chat（SSE 流式对话）、pipeline（实时研究执行 + 3D 协作网络）、
  admin（配置增删改查）、library（报告库）、monitor（监控看板）
- `static/img/` —— 图标资源（logo 等）
- `routes/` —— 后端路由：chat（对话）、pipeline（研究任务 SSE）、report（报告列表/查看/下载）、
  admin（配置管理/监控数据）、helpers（智能体实例缓存）
