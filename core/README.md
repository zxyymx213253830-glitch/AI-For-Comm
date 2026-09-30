# core/ —— 核心框架层（与业务无关的底座）

- `agent_node.py` —— 智能体通用节点：建会话、发起调用、解析 SSE 流式回复、空回复重试
- `config.py` / `config_manager.py` —— 读取根目录 `config.json`（平台地址、密钥、各 Agent 编号/版本/知识库挂载）
- `pipeline.py` —— 六步科研流水线：规划拆题 → 文献调研 → 并行咨询专家 → 交叉校验 → 闭环修正 → 统稿成报
- `orchestrator.py` —— 双智能体协作编排与消息路由
- `message_bus.py` —— 本地内存消息总线（Agent 间传信不走网络）
- `tool_driver.py` —— 工具回环驱动器：把 tools/ 的工具清单注入提示词，解析智能体的调用请求并回灌结果
- `report.py` —— 研究报告 HTML 渲染引擎（靛蓝瓷主题排版规范）
- `lit_search.py` —— 文献检索公共实现
- `logger.py` —— 结构化日志（写入 logs/session.jsonl）
