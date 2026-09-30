# -*- coding: utf-8 -*-
"""
AI for Comm 本地工具层 —— Agent 的"手和脚"

设计说明：
- OpenTrek 平台上的 Agent 是远程 HTTP 调用，无法自己当 MCP 客户端；
  因此工具全部在本地注册、本地执行，由 core/tool_driver 以
  "伪工具调用"协议接入流水线：Agent 输出工具请求 → 本地执行 → 结果回传 → Agent 继续。
- 每个工具都做成"未来可平移到平台工具中心"的形态：统一的
  名称/描述/参数/执行函数 四要素，注册层不动、执行位置可换。
- 工具内部界面文字与返回信息全部中文。
"""
from tools.registry import (  # noqa: F401
    tool, execute, catalog_for, tools_for, has_tools, all_tool_names, label,
)

# 以下导入仅为触发各模块的 @tool 自注册，请勿删除
import tools.math_tools       # noqa: F401,E402
import tools.lit_tools        # noqa: F401,E402
import tools.sim_tools        # noqa: F401,E402
import tools.comm_tools       # noqa: F401,E402
import tools.hw_tools         # noqa: F401,E402
import tools.protocol_tools   # noqa: F401,E402
