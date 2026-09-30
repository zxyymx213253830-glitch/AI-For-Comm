# -*- coding: utf-8 -*-
"""
工具驱动器 —— "伪工具调用"协议的本地执行循环

背景：OpenTrek 平台 Agent 是远程 HTTP 调用、无法自己当 MCP 客户端；
且平台的 Agent 每次 think() 都是新会话（无记忆）。因此本驱动实现：

  1. 提示词附加工具说明书（〔工具请求〕标记格式，不用代码围栏——平台围栏会截断 SSE）
  2. Agent 回复中提取工具请求 → 本地注册层执行
  3. 把"原始问题 + Agent 上一条回答 + 工具真实结果"整体回填，再次调用 Agent
  4. 循环至多 MAX_TOOL_ROUNDS 轮；Agent 不再申请工具即定稿

另有一条不依赖模型自觉的通道 —— **确定性预跑（preflight）**：
驱动器先按"专家类型 + 子问题关键词"本地真跑 1~2 个工具，把真实数值压进首轮
提示词，要求模型引用而非心算（详见 preflight_calls 的注释）。

对上层（pipeline/chat）只有一个函数：
    ask_with_tools(agent, prompt, on_event=None, preflight_ctx="")
"""
import json
import re

from core.logger import log
from tools import catalog_for, execute as tool_execute, tools_for

TOOL_MARK_RE = re.compile(r"〔工具请求〕")
# 容错提取工具名：兼容单/双引号、键未加引号、全角冒号
NAME_FALLBACK_RE = re.compile(
    r'''['"]?name['"]?\s*[:：]\s*['"]?([A-Za-z_][A-Za-z0-9_]*)['"]?''')
MAX_TOOL_ROUNDS = 2      # 每个问题最多 2 轮工具回环
MAX_CALLS_PER_ROUND = 3  # 单轮最多执行 3 个工具请求
RESULT_MAX_CHARS = 2500  # 单个工具结果注入提示词的上限

# 工具说明书之后的“工具优先”指令：明确告诉模型可以先申请工具、后给终答，
# 避免上游拼接的“一次性输出完整回答”后缀把工具回环压死。
_TOOL_FIRST_HINT = (
    "\n\n【工具优先】上面这些本地工具能给出真实计算/检索/仿真结果，比你心算可靠。"
    "若本次回答需要真实数值、公式化简、恒等式复核、仿真运行或协议条款，"
    "请先单独一行按格式申请工具（本轮允许不写最终结论）；系统执行后会"
    "把真实结果发给你，你再基于结果给出完整最终回答，并把工具结果写进结论。"
    "若确实不需要工具，则直接一次性给出完整回答。"
)

# ═══════════════════════════════════════════════════════════════
#  确定性工具预跑（preflight）
#
#  为什么要有这一层：2026-09-02 用户反馈“几个 agent 输出的都是纯文本”。
#  查 logs/session.jsonl：tool.catalog.injected 有 5 条、tool.executed 为 0 条 ——
#  说明书确实发到了，但模型一律凭记忆心算作答，从不申请工具（说明书里
#  “能直接答的不要申请”反而给了它台阶）。光靠提示词邀请不可靠，因此改为：
#  驱动器先本地真跑，把真实数值摆在模型面前，再要求它引用。
#
#  预跑只挑“参数可由驱动器自己确定”的离线工具（comm_lib / protocol_lookup）；
#  run_python / run_verilog 必须模型给代码，预跑无法凭空造，仍走自愿申请通道。
# ═══════════════════════════════════════════════════════════════
MAX_PREFLIGHT = 2        # 每次提问最多预跑 2 个工具

_CAPACITY_KW = ("香农", "shannon", "信道容量", "容量", "capacity",
                "频谱效率", "峰值速率", "吞吐")
_BER_KW = ("误码", "ber", "bler", "误块", "误符号", "调制", "星座",
           "编码增益", "eb/n0", "ebno", "门限", "链路预算", "覆盖")
_SCHEME_ALIAS = {
    "64qam": ("64qam", "64-qam"),
    "16qam": ("16qam", "16-qam"),
    "8psk":  ("8psk", "8-psk"),
    "qpsk":  ("qpsk", "4psk", "正交相移键控"),
    "bpsk":  ("bpsk", "2psk", "二进制相移键控"),
}
_RAYLEIGH_ALIAS = ("rayleigh", "瑞利", "衰落", "fading")
_BW_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ghz|mhz|khz|hz)", re.I)
_SNR_RE = re.compile(r"(?:snr|sinr|信噪比)[^\d\-]{0,6}(-?\d+(?:\.\d+)?)\s*db", re.I)
_QUERY_PREFIXES = ("你负责的子问题：", "你的子问题：", "子问题：", "研究课题：")

_PREFLIGHT_HEADER = "\n\n【本地工具预跑结果（系统已真实执行，非模型生成）】\n"
_PREFLIGHT_RULE = (
    "\n上述数值与条目来自本地工具的真实运行结果。请在回答中直接引用它们"
    "（写明工具名与具体数字/出处），不要用自己记忆里的近似值覆盖；"
    "若与你的推导冲突，以工具结果为准并说明差异原因。"
)


def _detect_scheme(text: str) -> str:
    """从文本里认出调制方式；先长后短匹配，防 16qam 被 qpsk 之类的短名抢走。"""
    low = (text or "").lower()
    for scheme in ("64qam", "16qam", "8psk", "qpsk", "bpsk"):
        if any(a in low for a in _SCHEME_ALIAS[scheme]):
            return scheme
    return ""


def _detect_channel(text: str) -> str:
    low = (text or "").lower()
    return "rayleigh" if any(a in low for a in _RAYLEIGH_ALIAS) else "awgn"


def _detect_bandwidth(text: str) -> float:
    """认出 '20 MHz' / '100MHz' / '3.5GHz' 一类带宽写法，返回 Hz；没写则 0。"""
    m = _BW_RE.search(text or "")
    if not m:
        return 0.0
    mult = {"hz": 1, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}[m.group(2).lower()]
    return float(m.group(1)) * mult


def _detect_snr_db(text: str) -> float:
    m = _SNR_RE.search(text or "")
    return float(m.group(1)) if m else 10.0


def _lookup_query(text: str) -> str:
    """从提问上下文里挑一段最适合查本地知识库的主题串（≤60 字）。"""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    for p in _QUERY_PREFIXES:            # 优先取子问题本体，跳过前缀样板
        i = t.find(p)
        if i >= 0:
            t = t[i + len(p):]
            break
    t = re.split(r"[。\n]", t)[0]
    return t[:60].strip()


def preflight_calls(agent_name: str, ctx: str) -> list:
    """按专家权限 + 关键词，给出至多 MAX_PREFLIGHT 个“确定能跑”的工具调用。

    返回 [{"name":..., "arguments":{...}}]；无可预跑工具时返回空列表。
    """
    names = set(tools_for(agent_name))
    text = str(ctx or "")[:1500]
    low = text.lower()
    calls = []

    if "comm_lib" in names:
        if any(k in low for k in _CAPACITY_KW):
            calls.append({"name": "comm_lib", "arguments": {
                "action": "shannon",
                "bandwidth": _detect_bandwidth(text) or 20e6,
                "snr_db": _detect_snr_db(text)}})
        elif any(k in low for k in _BER_KW) or _detect_scheme(text):
            # 只要题干点了调制方式，就把标准误码率曲线当基准送上去
            scheme = _detect_scheme(text) or "bpsk"
            channel = _detect_channel(text)
            if channel == "rayleigh" and scheme not in ("bpsk", "qpsk"):
                scheme = "qpsk"          # 瑞利只内置 bpsk/qpsk 精确式
            calls.append({"name": "comm_lib", "arguments": {
                "action": "theo_ber", "scheme": scheme, "channel": channel,
                "ebn0_db": "0,2,4,6,8,10"}})

    if "protocol_lookup" in names and len(calls) < MAX_PREFLIGHT:
        q = _lookup_query(text)
        if q:
            calls.append({"name": "protocol_lookup",
                          "arguments": {"query": q, "top_k": 2}})
    return calls[:MAX_PREFLIGHT]


def _run_preflight(agent, ctx: str, on_event=None) -> tuple:
    """执行预跑，返回 (注入提示词的文本, 成功执行的工具名列表)。

    失败的结果不进提示词（免得误导模型），但照常写日志便于排查。
    以 round=0 上报 on_event，与模型自愿申请（round≥1）区分开。
    """
    calls = preflight_calls(agent.name, ctx)
    if not calls:
        return "", []
    blocks, ok_calls = [], []
    for c in calls:
        res = tool_execute(c["name"], c["arguments"])
        ok = bool(res.get("ok"))
        log.info("tool.executed", agent=agent.name, tool=c["name"],
                 ok=ok, round=0, mode="preflight")
        if ok:
            blocks.append(_fmt_result(c["name"], res))
            ok_calls.append(c)
    if not blocks:
        return "", []
    log.info("tool.preflight", agent=agent.name,
             tools=[c["name"] for c in ok_calls])
    if on_event:
        try:
            on_event(0, ok_calls, blocks)
        except Exception:
            pass
    return _PREFLIGHT_HEADER + "\n".join(blocks) + _PREFLIGHT_RULE, \
        [c["name"] for c in ok_calls]


def extract_tool_calls(text: str) -> list:
    """从 Agent 回答中提取 [{"name":..., "arguments":{...}}]，容忍格式偏差。"""
    calls = []
    pos = 0
    decoder = json.JSONDecoder()
    while len(calls) < MAX_CALLS_PER_ROUND:
        m = TOOL_MARK_RE.search(text, pos)
        if not m:
            break
        rest = text[m.end():].lstrip()
        parsed = None
        if rest.startswith("{"):
            try:
                obj, _ = decoder.raw_decode(rest)
                if isinstance(obj, dict) and obj.get("name"):
                    parsed = obj
            except (json.JSONDecodeError, ValueError):
                parsed = None
        if parsed is None:
            # 容错：模型写了非法 JSON（单引号/裸键/全角冒号），至少把工具名抠出来，
            # 参数缺失交给注册层的中文"参数不对"提示去引导模型重试
            m2 = NAME_FALLBACK_RE.search(rest[:600])
            if m2:
                parsed = {"name": m2.group(1), "arguments": {}}
            else:
                pos = m.end()
                continue
        args = parsed.get("arguments")
        if not isinstance(args, dict):
            args = {}
        calls.append({"name": str(parsed["name"]), "arguments": args})
        pos = m.end() + 1
    return calls


def _fmt_result(name: str, res: dict) -> str:
    """工具结果压缩成注入提示词的中文文本（图片 base64 一律剔除）。"""
    payload = res.get("result", res)
    if isinstance(payload, dict):
        payload = {k: v for k, v in payload.items() if k not in ("images",)}
    try:
        txt = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        txt = str(payload)
    if len(txt) > RESULT_MAX_CHARS:
        txt = txt[:RESULT_MAX_CHARS] + "…（结果过长已截断）"
    prefix = "执行成功" if res.get("ok") else "执行失败"
    return f"〔工具结果 {name}｜{prefix}〕{txt}〔/工具结果〕"


def ask_with_tools(agent, prompt: str, on_event=None, preflight_ctx: str = "") -> str:
    """带工具回环的 Agent 提问。on_event(round, calls, results) 可用于进度上报
    （round=0 为驱动器预跑，round≥1 为模型自愿申请）。

    preflight_ctx：用于推导预跑工具的上下文（一般传课题+子问题）；
    传空串则关闭预跑，只保留模型自愿申请通道。
    无工具权限的 Agent 直接退化为普通 think()。
    """
    catalog = catalog_for(agent.name)
    if not catalog:
        return agent.think(prompt)

    head = prompt
    if preflight_ctx:
        injected, _names = _run_preflight(agent, preflight_ctx, on_event)
        if injected:
            head = prompt + injected

    # 工具说明书必须压在“一次性输出完整回答”后缀之后：否则模型会把后缀当最高
    # 指令、直接给纯文本终答而从不申请工具（2026-09-02 实测：会话日志里工具事件为 0）。
    current = head + "\n\n" + catalog + _TOOL_FIRST_HINT
    log.info("tool.catalog.injected", agent=agent.name,
             tools=tools_for(agent.name))
    last_answer = ""
    for rnd in range(1, MAX_TOOL_ROUNDS + 1):
        answer = agent.think(current)
        if not answer or not answer.strip():
            break
        last_answer = answer
        calls = extract_tool_calls(answer)
        if not calls:
            return _strip_marks(answer)  # 不再申请工具 → 定稿
        blocks = []
        for c in calls:
            res = tool_execute(c["name"], c["arguments"])
            blocks.append(_fmt_result(c["name"], res))
            log.info("tool.executed", agent=agent.name, tool=c["name"],
                     ok=bool(res.get("ok")), round=rnd)
        if on_event:
            try:
                on_event(rnd, calls, blocks)
            except Exception:
                pass
        # 会话无记忆：把上下文完整重建（预跑结果一并带上，否则第二轮就丢了真实数值）
        current = (
            head + "\n\n" + catalog
            + "\n\n【上一轮你的回答（其中工具请求已被系统执行）】\n"
            + _strip_marks(answer)[:4000]
            + "\n\n【工具真实执行结果】\n" + "\n".join(blocks)
            + "\n\n请基于上述真实结果继续完成回答。还需要补充工具可再申请（"
              "格式同上，仅在本轮确实必要时）；不需要工具时，直接给出完整最终回答，"
              "并把工具结果写进结论。"
        )
    # 轮次耗尽：若最后一次仍带工具请求，剥掉标记返回（含中间信息，好过空回答）
    return _strip_marks(last_answer) if last_answer else "(工具回环耗尽，未获得最终回答)"


def _strip_marks(text: str) -> str:
    """从定稿回答中剔除工具请求标记段/残留标记符。"""
    out = re.sub(r"〔工具请求〕.*?〔/工具请求〕", "", text, flags=re.S)
    out = re.sub(r"〔/?工具请求〕", "", out)
    # 剔除标记后若尾部 JSON 残片悬挂（模型忘写闭合标记），按行清掉含 name/arguments 的裸行
    lines = [ln for ln in out.splitlines()
             if not re.match(r'''^\s*[{}\[\]",]*['"]?(name|arguments)['"]?\s*[:：]''', ln)]
    return "\n".join(lines).strip()
