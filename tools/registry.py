# -*- coding: utf-8 -*-
"""
工具注册中心：名称/描述/参数/执行函数 四要素统一登记。

- @tool 装饰器自注册，新增工具只需新写一个带装饰器的函数
- catalog_for(agent_name) 生成给 Agent 看的中文工具说明书（注入提示词用）
- execute(name, arguments) 统一分发执行，任何异常都转成中文错误结果，
  保证工具永远有回复，不会把流水线卡死
"""
import json
import traceback

# 全局注册表：{tool_name: {"desc": str, "params": dict, "handler": callable}}
_REGISTRY = {}

# Agent → 可用工具白名单（最小权限：只给每个 Agent 真正用得上的）
# 2026-09-02 扩容说明：comm_lib（标准算法库）与 protocol_lookup（本地知识库）
# 对全部专家开放。两者都是离线、无副作用的“取真实数值/取规范摘录”工具，
# 是驱动器确定性预跑（core/tool_driver.preflight_calls）的必需手段 ——
# 此前只靠模型自愿申请，实测 tool.executed 为 0，专家回答退化成纯文本心算。
TOOL_PERMISSIONS = {
    "math_agent":      ["sympy_compute", "sympy_check_equality", "comm_lib",
                        "protocol_lookup", "search_papers"],
    "sim_agent":       ["run_python", "comm_lib", "sympy_compute",
                        "protocol_lookup", "search_papers"],
    "hw_agent":        ["run_verilog", "comm_lib", "sympy_compute",
                        "protocol_lookup", "search_papers"],
    "comm_agent":      ["protocol_lookup", "comm_lib", "sympy_compute",
                        "search_papers"],
    "verify_agent":    ["sympy_check_equality", "sympy_compute", "run_python",
                        "comm_lib", "protocol_lookup", "search_papers"],
    "lit_review_agent": [],  # 文献Agent本身即检索器，内部已直调工具，无需再挂
}

# 工具中文短名（给前端/日志展示用，长描述见 desc）
TOOL_LABELS = {
    "sympy_compute":        "符号数学推演",
    "sympy_check_equality": "恒等式复核",
    "search_papers":        "公网文献检索",
    "run_python":           "Python 仿真执行",
    "comm_lib":             "通信算法库",
    "run_verilog":          "Verilog 编译仿真",
    "protocol_lookup":      "协议知识查询",
}


def label(name: str) -> str:
    """工具中文名，未登记的直接回原名。"""
    return TOOL_LABELS.get(name, name)


def tool(name: str, desc: str, params: dict):
    """注册一个工具。params: {参数名: 中文说明（含取值示例）}"""
    def deco(func):
        _REGISTRY[name] = {"desc": desc, "params": params, "handler": func}
        return func
    return deco


def all_tool_names():
    return sorted(_REGISTRY)


def tools_for(agent_name: str) -> list:
    """该 Agent 可用的工具名列表（未登记的 Agent 返回空 = 无工具）。"""
    return [t for t in TOOL_PERMISSIONS.get(agent_name, []) if t in _REGISTRY]


def has_tools(agent_name: str) -> bool:
    return bool(tools_for(agent_name))


def catalog_for(agent_name: str) -> str:
    """生成注入提示词的中文工具说明书。无权限工具时返回空串。"""
    names = tools_for(agent_name)
    if not names:
        return ""
    lines = [
        "【本地工具】你可以调用以下本地工具来获取真实计算/检索结果。",
        "申请方法：在你的回答中单独一行写出下面格式（JSON 写在标记内，不要加其他符号）：",
        '〔工具请求〕{"name": "工具名", "arguments": {"参数名": "参数值"}}〔/工具请求〕',
        "规则：",
        "1) 一次回答最多申请 3 个工具；系统执行后会把结果发给你，你继续完成回答；",
        "2) 只申请确实需要的工具，能直接答的不要申请；",
        "3) 严禁自己编造工具的返回结果；",
        "4) 表达式一律用 Python 语法（如 exp(-x**2/2)、sqrt(pi)、sin(2*pi*f)）。",
        "可用工具：",
    ]
    for n in names:
        t = _REGISTRY[n]
        ptxt = "；".join(f"{k}={v}" for k, v in t["params"].items())
        lines.append(f"- {n}：{t['desc']}" + (f"（参数：{ptxt}）" if ptxt else ""))
    return "\n".join(lines)


def execute(name: str, arguments: dict) -> dict:
    """执行工具，返回 {"ok": bool, "result": ...}。任何异常均转为中文错误。"""
    t = _REGISTRY.get(name)
    if not t:
        return {"ok": False, "result": f"未知工具「{name}」，可用工具：{', '.join(all_tool_names())}"}
    if not isinstance(arguments, dict):
        return {"ok": False, "result": "工具参数必须是 JSON 对象"}
    try:
        out = t["handler"](**arguments)
        if isinstance(out, dict) and "ok" in out:
            return out
        return {"ok": True, "result": out}
    except TypeError as e:
        return {"ok": False, "result": f"参数不对：{e}。本工具参数：{json.dumps(t['params'], ensure_ascii=False)}"}
    except ValueError as e:
        # 工具内部主动抛出的"用法不合法"，直接给模型看中文原因，不打栈
        return {"ok": False, "result": f"无法执行：{e}"}
    except Exception as e:
        traceback.print_exc()
        return {"ok": False, "result": f"工具执行失败：{type(e).__name__}: {e}"}
