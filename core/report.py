# -*- coding: utf-8 -*-
"""
HTML 报告生成器 —— 把双 Agent 协作结果渲染为可视化页面
"""

import os
import re
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
#  LaTeX 转义救援
#
#  JSON 的合法转义首字母 b/f/n/r/t/u，恰好也是一大批 LaTeX 命令的首字母：
#  \text \times \theta \to \frac \rho \bar \beta \nu \nabla \begin ……
#  模型把公式直写进结构化统稿的 JSON 字符串时，"\t" 会被 json.loads 当成
#  制表符吃掉，$P_{\text{eff}}$ 于是变成 $P_{<TAB>ext{eff}}$ —— KaTeX 解析失败，
#  页面按 throwOnError:false 把公式原样标红，看起来就是「露出 text 源码」。
#  这里按命令名白名单把被吃掉的反斜杠还原：命令名后不能跟字母/汉字，
#  单字母命令（\to \nu \ne \rm）额外要求后面是数学语境字符，
#  因此正文的真换行、真制表符、"e.g." 这类英文都不会被误伤。
#  （大写开头的 \Rightarrow \neq 之类不在风险集内：它们本就是非法 JSON 转义，
#   由 pipeline._fix_escapes 在解析前双写反斜杠救回。）
# ══════════════════════════════════════════════════════════════════════
_CTRL_OF = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
_HEAD_OF_CTRL = {v: k for k, v in _CTRL_OF.items()}

# 值 = 首字母被吃掉后剩下的部分（匹配时按长度降序，避免 \text 抢走 \textbf）
_LATEX_TAILS = {
    "b": ("oldsymbol", "egin", "oxed", "mod", "eta", "ot", "ar"),
    "f": ("orall", "lat", "rac"),
    "n": ("abla", "otin", "eq", "u", "e"),
    "r": ("ightarrow", "floor", "ight", "ho", "m"),
    "t": ("herefore", "riangle", "extbf", "extit", "extrm", "imes", "heta",
          "ilde", "anh", "iny", "ext", "ag", "au", "op", "o"),
}

# 命令名到此为止：后面不能再跟字母或汉字，否则说明那是普通英文单词（如 "e.g."）
_TAIL_STOP = r"(?![A-Za-z\u4e00-\u9fff])"
# 单字母命令再要求后一个字符是数学语境（不含换行，避免段落开头孤字母被误伤）
_MATH_NEXT = r"(?=[ \t_^{}\[\]()$\\,;:=<>+\-*/|!0-9])"

_CTRL_ANY = re.compile("[" + "".join(re.escape(c) for c in _CTRL_OF.values()) + "]")


def _build_restore():
    alts = []
    for head, tails in _LATEX_TAILS.items():
        ctrl = re.escape(_CTRL_OF[head])
        for t in sorted(tails, key=len, reverse=True):
            guard = _MATH_NEXT if len(t) == 1 else ""
            alts.append(f"{ctrl}{re.escape(t)}{guard}{_TAIL_STOP}")
    return re.compile("|".join(alts))


_RESTORE = _build_restore()


def _undo_eaten(m):
    s = m.group(0)
    return "\\" + _HEAD_OF_CTRL[s[0]] + s[1:]


def restore_latex_ctrl(text) -> str:
    """把被 JSON 转义吃掉的 LaTeX 反斜杠还原回来（渲染前的最后一道文本卫生）。"""
    s = str(text if text is not None else "")
    if not _CTRL_ANY.search(s):
        return s
    return _RESTORE.sub(_undo_eaten, s)


# KaTeX 的文本模式不接受下划线/脱字符：模型常写 \text{PAPR_Margin}，
# 渲染时报 ParseError（throwOnError:false 会把整条公式标红并原样显示）。
_TEXT_CMD = re.compile(r"\\(text(?:rm|bf|it)?|mbox)\s*\{([^{}]*)\}")


def _escape_in_text(m):
    inner = m.group(2).replace("_", r"\_").replace("^", r"\textasciicircum ")
    return "\\" + m.group(1) + "{" + inner + "}"


def sanitize_math(text) -> str:
    """渲染前的公式卫生：先还原被 JSON 吃掉的反斜杠，再把 \text{} 里的
    下划线转成 KaTeX 能接受的写法，最后配平公式定界符。不碰正文其余部分。"""
    s = restore_latex_ctrl(text)
    s = s.replace(r"\\_", r"\_").replace(r"\\%", r"\%")   # 模型常多写一层反斜杠
    s = _TEXT_CMD.sub(_escape_in_text, s) if ("\\text" in s or "\\mbox" in s) else s
    return balance_math(s)


# 模型输出被平台截断时，常留下没闭合的 $$ / $。KaTeX 的 auto-render 会顺着
# 往下找下一个定界符，把中间整段正文当公式吞掉——表现就是字变成斜体数学字体、
# 10~13dB 的波浪号消失、\text{SNR} 这类源码裸露。这里把非法定界符直接去掉，
# 只让正文以普通文本呈现。注意不能转义成 \$——浏览器端的 marked 会把它反转义
# 回 $，等于没修。
_FENCE_CODE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_DISP_MATH = re.compile(r"\$\$(?:(?!\$\$)[\s\S])*?\$\$")
_INLINE_MATH = re.compile(r"(?<!\$)\$(?:(?!\$)[^\n])*?\$(?!\$)")
_PH = "\u0000M%d\u0000"
_PH_BAD = {"D": "\u0000MBD\u0000", "I": "\u0000MBI\u0000"}
_MAX_DISP = 300               # 真公式不会长过这个数，超了说明是跨段误配
_MAX_INLINE = 200
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]{4,}")   # 连续四个汉字＝那是正文，不是公式


def _valid_disp(g):
    inner = g[2:-2]
    return (len(g) <= _MAX_DISP and "\n\n" not in inner
            and not _CJK_RUN.search(inner))


def _valid_inline(g):
    return len(g) <= _MAX_INLINE and not _CJK_RUN.search(g)


def _stash(s, pat, store):
    """把命中的片段搬进 store，原地留占位符，后续处理不会误伤它。"""
    def repl(m):
        store.append(m.group(0))
        return _PH % (len(store) - 1)
    return pat.sub(repl, s)


def _keep_math(s, pat, store, valid):
    """合法公式占位保留；非法的只拆定界符，内文必须留下。"""
    def repl(m):
        seg = m.group(0)
        if valid(seg):
            store.append(seg)
            return _PH % (len(store) - 1)
        bad = _PH_BAD["D" if seg.startswith("$$") else "I"]
        inner = seg[2:-2] if seg.startswith("$$") else seg[1:-1]
        return bad + inner + bad
    return pat.sub(repl, s)


# 截断残骸里的 LaTeX 直接丢在页面上会很难看，转成人能读的写法：
# \text{...} 取内文、\frac{a}{b} 变 (a)/(b)、希腊字母与上下标走 Unicode。
_GREEK = {
    "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ", "\\epsilon": "ε",
    "\\varepsilon": "ε", "\\zeta": "ζ", "\\eta": "η", "\\theta": "θ", "\\kappa": "κ",
    "\\lambda": "λ", "\\mu": "μ", "\\nu": "ν", "\\rho": "ρ", "\\sigma": "σ", "\\tau": "τ",
    "\\phi": "φ", "\\varphi": "φ", "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω",
    "\\Delta": "Δ", "\\Sigma": "Σ", "\\Omega": "Ω", "\\Phi": "Φ", "\\Lambda": "Λ",
    "\\infty": "∞", "\\partial": "∂", "\\nabla": "∇", "\\emptyset": "∅",
    "\\to": "→", "\\rightarrow": "→", "\\leftarrow": "←", "\\Rightarrow": "⇒",
    "\\approx": "≈", "\\equiv": "≡", "\\sim": "∼", "\\propto": "∝",
    "\\le": "≤", "\\leq": "≤", "\\ge": "≥", "\\geq": "≥", "\\neq": "≠", "\\ne": "≠",
    "\\times": "×", "\\cdot": "·", "\\div": "÷", "\\pm": "±", "\\in": "∈", "\\sum": "∑",
    "\\prod": "∏", "\\int": "∫", "\\ldots": "…", "\\cdots": "…",
    "\\quad": " ", "\\qquad": "  ", "\\,": " ", "\\;": " ", "\\ ": " ",
}
# Unicode 上下标只覆盖部分字母，故用字典 + 原样回退，不用 maketrans。
_SUB = dict(zip("0123456789+-=",
                "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u207a\u207b\u207c"))
_SUB.update({"a": "\u2090", "e": "\u2091", "h": "\u2095", "i": "\u1d62", "k": "\u2096", "l": "\u2097", "m": "\u2098", "n": "\u2099", "o": "\u2092", "p": "\u209a", "s": "\u209b", "t": "\u209c", "u": "\u1d64", "x": "\u2093"})
_SUP = dict(zip("0123456789+-=()",
                "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b\u207c\u207d\u207e"))
_SUP.update({"a": "\u1d43", "b": "\u1d47", "c": "\u1d9c", "d": "\u1d48", "e": "\u1d49", "f": "\ua7a0", "g": "\u1d4d", "h": "\u02b0", "i": "\u2071", "j": "\u02b2", "k": "\u1d4f", "l": "\u02e1", "m": "\u1d50", "n": "\u207f", "o": "\u1d52", "p": "\u1d53", "r": "\u02b3", "s": "\u02e2", "t": "\u1d57", "u": "\u1d58", "v": "\u1d5b", "w": "\u02b7", "x": "\u02e3", "y": "\u02b8", "z": "\u1dbb"})


def _tr(s, table):
    """逐字符转 Unicode 上下标，表里没有的原样保留。"""
    return "".join(table.get(c, c) for c in s)
_TEXTLIKE = re.compile(r"\\(?:text|textrm|textbf|textit|mathrm|mathit|mathbf"
                       r"|mathsf|mbox|operatorname)\s*\{([^{}]*)\}")
_FRAC = re.compile(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_SQRT = re.compile(r"\\sqrt\s*(?:\[(\d+)\])?\{([^{}]*)\}")
_SUBSCRIPT = re.compile(r"_\{([^{}]*)\}")
_SUPERSCRIPT = re.compile(r"\^\{([^{}]*)\}")
_LATEX_HINT = re.compile(r"\\(?:text|frac|sqrt|mathrm|mathbf|mathcal)")


def latex_to_plain(text) -> str:
    """把一段 LaTeX 转成可读的纯文本（公式没渲染成式子时的降级通道）。"""
    s = str(text if text is not None else "")
    if "\\" not in s and "_" not in s and "^" not in s:
        return s
    s = _TEXTLIKE.sub(r"\1", s)
    s = _FRAC.sub(r"(\1)/(\2)", s)
    s = _SQRT.sub(lambda m: ("∛" if m.group(1) == "3" else "√") + "(" + m.group(2) + ")", s)
    for k in sorted(_GREEK, key=len, reverse=True):
        s = s.replace(k, _GREEK[k])
    s = _SUBSCRIPT.sub(lambda m: "_" + _tr(m.group(1), _SUB), s)
    s = _SUPERSCRIPT.sub(lambda m: "^" + _tr(m.group(1), _SUP), s)
    s = re.sub(r"_([A-Za-z0-9])", lambda m: "_" + _tr(m.group(1), _SUB), s)
    s = re.sub(r"\^([A-Za-z0-9])", lambda m: "^" + _tr(m.group(1), _SUP), s)
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace(r"\%", "%").replace(r"\_", "_").replace(r"\{", "{").replace(r"\}", "}")
    s = re.sub(r"\\[a-zA-Z]+", lambda m: m.group(0)[1:], s)
    s = s.replace("\\", "").replace("{", "").replace("}", "")
    return re.sub(r"[ 	]{2,}", " ", s).strip()


def _plainize_line(m):
    seg = m.group(0)
    return latex_to_plain(seg.replace("$", "")) if _LATEX_HINT.search(seg) else seg


def balance_math(text) -> str:
    """配平公式定界符：未闭合或误配的 $$ / $ 去掉，残骸转成可读文本，
    既不让它吞正文，也不把一堆反斜杠丢在页面上。"""
    s = str(text if text is not None else "")
    if "$" not in s and "\\" not in s:
        return s
    store = []
    s = _stash(s, _FENCE_CODE, store)          # 代码块里的 $ 不是定界符
    s = _stash(s, _INLINE_CODE, store)
    if "$" in s:
        s = _keep_math(s, _DISP_MATH, store, _valid_disp)
        while "$$" in s:                        # 没闭合的 display：残骸转纯文本
            i = s.index("$$")
            j = s.find("\n\n", i)
            j = len(s) if j < 0 else j
            s = s[:i] + latex_to_plain(s[i + 2:j]) + s[j:]
        s = _keep_math(s, _INLINE_MATH, store, _valid_inline)
        while "$" in s:                         # 同上，行内
            i = s.index("$")
            j = s.find("\n", i)
            j = len(s) if j < 0 else j
            s = s[:i] + latex_to_plain(s[i + 1:j]) + s[j:]
    s = re.sub(r"[^\n]*\\(?:text|frac|sqrt|mathrm|mathbf)[{\\][^\n]*", _plainize_line, s)
    s = s.replace(_PH_BAD["D"], "").replace(_PH_BAD["I"], "")
    for i, seg in enumerate(store):
        s = s.replace(_PH % i, seg)
    return s


def _esc_html(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f5f7fa; color: #2c3e50; line-height: 1.8; }
.header { background: linear-gradient(135deg, #1a237e, #283593); color: #fff; padding: 40px 60px; }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header .meta { opacity: 0.8; font-size: 14px; }
.container { max-width: 1000px; margin: 0 auto; padding: 30px 20px; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 24px; overflow: hidden; }
.card-header { padding: 16px 24px; font-weight: 700; font-size: 16px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 10px; }
.card-body { padding: 24px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.badge-math { background: #e3f2fd; color: #1565c0; }
.badge-verify { background: #e8f5e9; color: #2e7d32; }
.badge-pass { background: #c8e6c9; color: #1b5e20; }
.badge-warn { background: #fff3e0; color: #e65100; }
.badge-bus { background: #f3e5f5; color: #7b1fa2; }
.flow { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 24px; flex-wrap: wrap; }
.flow-node { background: #fff; border: 2px solid #e0e0e0; border-radius: 10px; padding: 16px 24px; text-align: center; min-width: 140px; }
.flow-node .icon { font-size: 28px; margin-bottom: 4px; }
.flow-node .label { font-weight: 700; font-size: 14px; }
.flow-arrow { font-size: 24px; color: #9e9e9e; }
.derivation-box, .feedback-box { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 20px; font-size: 14px; line-height: 1.8; }
.derivation-box h1, .derivation-box h2, .derivation-box h3, .feedback-box h1, .feedback-box h2, .feedback-box h3 { margin: 12px 0 6px; color: #1a237e; }
.derivation-box h1 { font-size: 20px; } .derivation-box h2 { font-size: 17px; } .derivation-box h3 { font-size: 15px; }
.derivation-box p, .feedback-box p { margin: 6px 0; }
.derivation-box ul, .derivation-box ol, .feedback-box ul, .feedback-box ol { padding-left: 24px; margin: 6px 0; }
.derivation-box code, .feedback-box code { background: #e8eaf6; padding: 1px 5px; border-radius: 3px; font-size: 13px; }
.derivation-box pre, .feedback-box pre { background: #263238; color: #e0e0e0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 10px 0; }
.derivation-box pre code, .feedback-box pre code { background: none; padding: 0; color: inherit; }
.derivation-box table, .feedback-box table { border-collapse: collapse; margin: 10px 0; width: 100%%; }
.derivation-box th, .derivation-box td, .feedback-box th, .feedback-box td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 13px; }
.derivation-box th, .feedback-box th { background: #e8eaf6; }
.derivation-box blockquote, .feedback-box blockquote { border-left: 4px solid #1a237e; padding-left: 12px; color: #555; margin: 8px 0; }
.checklist { list-style: none; }
.checklist li { padding: 6px 0; }
.checklist li::before { content: "\\2713 "; color: #4caf50; font-weight: 700; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); padding: 20px; text-align: center; }
.stat-card .value { font-size: 32px; font-weight: 700; color: #1a237e; }
.stat-card .label { font-size: 13px; color: #999; margin-top: 4px; }
.footer { text-align: center; color: #999; font-size: 12px; padding: 30px; }
pre { white-space: pre-wrap; word-wrap: break-word; }
"""

_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI for Comm — 协作验证报告</title>
<style>
%(style)s
</style>
</head>
<body>

<div class="header">
  <h1>AI for Comm — 多 Agent 协作验证报告</h1>
  <div class="meta">
    生成时间: %(timestamp)s &nbsp;|&nbsp;
    平台: OpenTrek &nbsp;|&nbsp;
    项目: 通信领域智能问答系统
  </div>
</div>

<div class="container">

  <div class="stats">
    <div class="stat-card"><div class="value">2</div><div class="label">参与 Agent</div></div>
    <div class="stat-card"><div class="value">%(total_time)s</div><div class="label">总耗时（秒）</div></div>
    <div class="stat-card"><div class="value">%(verdict)s</div><div class="label">验证结论</div></div>
    <div class="stat-card"><div class="value">%(rounds)s</div><div class="label">消息交换轮次</div></div>
  </div>

  <div class="card">
    <div class="card-header">🔄 协作流程</div>
    <div class="flow">
      <div class="flow-node">
        <div class="icon">🧮</div>
        <div class="label">数学 Agent</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">信息论推导</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node" style="border-color:#7b1fa2;background:#faf5fc;">
        <div class="icon">📡</div>
        <div class="label">MessageBus</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">消息路由</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node">
        <div class="icon">✅</div>
        <div class="label">验证 Agent</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">正确性检查</div>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node" style="border-color:#7b1fa2;background:#faf5fc;">
        <div class="icon">📡</div>
        <div class="label">MessageBus</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">结果回传</div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="badge badge-math">math_agent</span> 数学推导结果</div>
    <div class="card-body"><div class="derivation-box">%(derivation)s</div></div>
  </div>

  <div class="card">
    <div class="card-header"><span class="badge badge-verify">verify_agent</span> 验证反馈</div>
    <div class="card-body"><div class="feedback-box">%(feedback)s</div></div>
  </div>

  <div class="card">
    <div class="card-header">📋 人工核对要点</div>
    <div class="card-body"><ul class="checklist">%(check_items)s</ul></div>
  </div>

</div>

<div class="footer">
  AI for Comm · 通信领域多 Agent 协作智能问答系统 · Powered by OpenTrek
</div>
</body>
</html>"""


def generate_report(
    derivation: str,
    feedback: str,
    task: str = "",
    total_time: str = "—",
    rounds: str = "3",
    output_dir: str = "outputs",
) -> str:
    """生成 HTML 验证报告，返回文件路径"""
    os.makedirs(output_dir, exist_ok=True)

    # 自动判断验证结论（三级评级）
    if "【不通过】" in feedback:
        verdict = "❌ 不通过"
    elif "【有条件通过】" in feedback:
        verdict = "⚠️ 有条件通过"
    elif "【通过】" in feedback or "通过" in feedback:
        verdict = "✅ 通过"
    elif "错误" in feedback or "失败" in feedback:
        verdict = "⚠️ 需修正"
    else:
        verdict = "🔍 查看详情"

    # 核对要点
    items = [
        "推导是否引用了正确的香农公式 C = B·log₂(1+S/N)",
        "dB 换算是否正确（30dB → S/N = 1000）",
        "数值计算是否精确（≈ 199.5 Mbps）",
        "两端 Agent 消息是否通过 MessageBus 路由",
        "logs/session.jsonl 是否记录了完整链路",
    ]
    check_html = "\n".join(f"<li>{item}</li>" for item in items)

    # HTML 安全转义（顺带做一道公式卫生）
    esc = lambda s: _esc_html(sanitize_math(s))

    html = _HTML % {
        "style": _STYLE,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_time": total_time,
        "verdict": verdict,
        "rounds": rounds,
        "derivation": esc(derivation),
        "feedback": esc(feedback),
        "check_items": check_html,
    }

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


# ═══════════════════════════════════════════════════
#  科研任务流水线报告（core.pipeline.ResearchPipeline 专用）
#  v2 高审美模板 —— "靛蓝瓷"学术扉页风（设计令牌源自 guizang-ppt-skill Style A
#  靛蓝瓷主题 + frontend-design 方法论；v1 机械拼装模板保留在下方作回退参考）
# ═══════════════════════════════════════════════════

_RESEARCH_STYLE_V2 = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --ink: #0a1f3d;          /* 靛蓝瓷主色：深靛蓝 */
  --ink-tint: #152a4a;
  --paper: #f1f3f5;        /* 瓷白 */
  --paper-tint: #e4e8ec;
  --gold: #c9973f;         /* 琥珀金强调 */
  --hairline: #d5dbe2;
  --pass: #2e7d32; --warn: #b26a00; --fail: #b03030;
  --serif: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
  --sans: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif;
}
body { font-family: var(--sans); background: var(--paper); color: var(--ink); line-height: 1.9; font-size: 15px; }

/* ── 扉页 ── */
.cover { background: var(--ink); color: var(--paper); padding: 88px 40px 64px; position: relative; overflow: hidden; }
.cover::before { content: ""; position: absolute; top: 0; right: 0; width: 42%; height: 100%;
  background: radial-gradient(ellipse at 70% 20%, rgba(201,151,63,.14), transparent 62%); pointer-events: none; }
.cover .eyebrow { font-size: 12px; letter-spacing: .45em; color: var(--gold); text-transform: uppercase; margin-bottom: 26px; }
.cover h1 { font-family: var(--serif); font-size: 40px; font-weight: 700; line-height: 1.35;
  max-width: 860px; margin: 0 auto 0; }
.cover-inner { max-width: 920px; margin: 0 auto; position: relative; }
.cover .meta-row { margin-top: 38px; display: flex; flex-wrap: wrap; gap: 0; border-top: 1px solid rgba(241,243,245,.22); }
.cover .meta-item { padding: 14px 26px 0 0; margin-right: 26px; font-size: 13px; color: rgba(241,243,245,.72); }
.cover .meta-item b { color: var(--paper); font-weight: 600; margin-left: 8px; }
.verdict-badge { display: inline-block; padding: 7px 18px; border: 1px solid; border-radius: 2px;
  font-size: 14px; font-weight: 700; letter-spacing: .1em; margin-top: 30px; }
.v-pass { color: #b9e4bd; border-color: #6fbf77; background: rgba(111,191,119,.12); }
.v-warn { color: #f5d7a3; border-color: var(--gold); background: rgba(201,151,63,.14); }
.v-fail { color: #f2b8b8; border-color: #d97b7b; background: rgba(217,123,123,.12); }
.v-info { color: rgba(241,243,245,.85); border-color: rgba(241,243,245,.4); }
.kw { margin-top: 22px; font-size: 12px; letter-spacing: .08em; color: rgba(241,243,245,.6); }
.kw span { border: 1px solid rgba(241,243,245,.25); padding: 3px 12px; margin: 0 8px 8px 0; display: inline-block; border-radius: 2px; }

/* ── 主体 ── */
.container { max-width: 920px; margin: 0 auto; padding: 56px 24px 40px; }
section.chapter { margin-bottom: 56px; animation: rise .5s ease both; }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { section.chapter { animation: none; } }
.ch-head { display: flex; align-items: baseline; gap: 16px; border-bottom: 1px solid var(--ink);
  padding-bottom: 12px; margin-bottom: 26px; }
.ch-no { font-family: var(--serif); font-size: 30px; color: var(--gold); font-weight: 700; line-height: 1; }
.ch-head h2 { font-family: var(--serif); font-size: 22px; font-weight: 700; }
.ch-src { margin-left: auto; font-size: 12px; color: #8a94a3; letter-spacing: .12em; white-space: nowrap; }
.prose h1, .prose h2, .prose h3 { font-family: var(--serif); margin: 18px 0 8px; color: var(--ink); }
.prose h1 { font-size: 20px; } .prose h2 { font-size: 17px; } .prose h3 { font-size: 15.5px; }
.prose p { margin: 8px 0; }
.prose ul, .prose ol { padding-left: 26px; margin: 8px 0; }
.prose code { background: var(--paper-tint); padding: 1px 6px; border-radius: 3px; font-size: 13px; }
.prose pre { background: var(--ink); color: #dde4ec; padding: 18px; border-radius: 6px;
  overflow-x: auto; margin: 12px 0; white-space: pre-wrap; word-wrap: break-word; }
.prose pre code { background: none; padding: 0; color: inherit; }
.prose table { border-collapse: collapse; margin: 12px 0; width: 100%; font-size: 13.5px; }
.prose th, .prose td { border: 1px solid var(--hairline); padding: 8px 12px; text-align: left; }
.prose th { background: var(--paper-tint); }
.prose blockquote { border-left: 3px solid var(--gold); padding-left: 14px; color: #4a5568; margin: 10px 0; }

/* 摘要/结论块 */
.lead { background: #fff; border-left: 4px solid var(--gold); padding: 26px 30px;
  box-shadow: 0 1px 8px rgba(10,31,61,.05); border-radius: 0 6px 6px 0; }
.lead .prose p:first-child { font-size: 16px; }

/* 协作链路时间轴（签名元素：01~06 编号对应真实六步流程） */
.timeline { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0; margin-top: 6px; }
.tl-node { position: relative; padding: 0 6px; text-align: center; }
.tl-node::before { content: ""; position: absolute; top: 15px; left: 0; right: 0; border-top: 1px solid var(--hairline); }
.tl-node:first-child::before { left: 50%; } .tl-node:last-child::before { right: 50%; }
.tl-dot { position: relative; z-index: 1; width: 30px; height: 30px; margin: 0 auto 10px; border-radius: 50%;
  background: var(--ink); color: var(--paper); font-size: 12px; font-weight: 700; line-height: 30px; font-family: var(--serif); }
.tl-node.gold .tl-dot { background: var(--gold); }
.tl-lbl { font-size: 12.5px; font-weight: 600; }
.tl-sub { font-size: 11px; color: #8a94a3; margin-top: 2px; }

/* 任务拆解表 */
table.plan { width: 100%; border-collapse: collapse; font-size: 14px; background: #fff; }
table.plan th, table.plan td { border-bottom: 1px solid var(--hairline); padding: 12px 14px; text-align: left; }
table.plan th { background: var(--paper-tint); font-size: 12.5px; letter-spacing: .06em; color: #5a6577; }
.exp-tag { display: inline-block; padding: 2px 10px; font-size: 12px; border: 1px solid var(--hairline);
  border-radius: 2px; color: var(--ink-tint); background: var(--paper); }

/* 核心发现单节 */
details.origin { margin-top: 10px; }
details.origin summary { cursor: pointer; font-size: 12.5px; color: #8a94a3; list-style: none; }
.details-tag { display: inline-block; margin-left: 8px; padding: 1px 8px; font-size: 11px;
  border: 1px dashed var(--warn); color: var(--warn); border-radius: 2px; vertical-align: 2px; }

/* 附录 */
details.appendix-item { background: #fff; border: 1px solid var(--hairline); border-radius: 6px;
  margin-bottom: 12px; overflow: hidden; }
details.appendix-item summary { cursor: pointer; padding: 14px 20px; font-size: 14px; font-weight: 600;
  list-style: none; display: flex; align-items: center; gap: 10px; }
details.appendix-item summary::before { content: "▸"; color: var(--gold); transition: transform .2s; }
details.appendix-item[open] summary::before { transform: rotate(90deg); }
details.appendix-item .ap-body { padding: 0 20px 18px; border-top: 1px dashed var(--hairline); }
.ap-meta { margin-left: auto; font-size: 12px; color: #8a94a3; font-weight: 400; }
.sim-figure { text-align: center; margin: 16px 0; }
.sim-figure img { max-width: 100%; border-radius: 6px; box-shadow: 0 2px 10px rgba(10,31,61,.12); }

.footer { text-align: center; color: #9aa3b0; font-size: 12px; padding: 36px 20px 48px;
  border-top: 1px solid var(--hairline); max-width: 920px; margin: 0 auto; }

@media print {
  body { background: #fff; }
  .cover { -webkit-print-color-adjust: exact; print-color-adjust: exact; padding: 48px 32px; }
  section.chapter { animation: none; page-break-inside: avoid; }
  .container { padding-top: 24px; }
}
@media (max-width: 760px) {
  .cover h1 { font-size: 28px; }
  .timeline { grid-template-columns: repeat(3, 1fr); gap: 14px 0; }
  .tl-node::before { display: none; }
}
"""

_LOCAL_MD_JS = r"""
/* 本地 Markdown 渲染器：外网排版库（marked）不可达时的兜底，
   保证报告正文在任何内网/离线环境都不会退化成裸文本。 */
function mdEsc(s){var d=document.createElement('div');d.textContent=(s==null?'':String(s));return d.innerHTML;}
function localMarkdown(text){
  var src=String(text==null?'':text); var fences=[];
  src=src.replace(/```([^\n`]*)\n([\s\S]*?)```/g,function(m,lang,code){
    fences.push('<pre><code class="lang-'+mdEsc(lang.trim())+'">'+mdEsc(code)+'</code></pre>');
    return '\u0000F'+(fences.length-1)+'\u0000';});
  src=mdEsc(src);
  function inline(s){return s
    .replace(/`([^`\n]+)`/g,function(m,c){return '<code>'+c+'</code>';})
    .replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g,'$1<em>$2</em>')
    .replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');}
  var lines=src.split(/\r?\n/),out=[],i=0;
  function isSep(s){return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(s)&&s.indexOf('-')>=0;}
  function cells(s){return s.split('|').map(function(c){return c.trim();})
    .filter(function(c,idx,a){return c!==''||(idx>0&&idx<a.length-1);});}
  while(i<lines.length){
    var ln=lines[i];
    if(!ln.trim()){i++;continue;}
    var fm=ln.match(/^\u0000F(\d+)\u0000\s*$/);
    if(fm){out.push(fences[+fm[1]]);i++;continue;}
    var hm=ln.match(/^(#{1,6})\s+(.*)$/);
    if(hm){out.push('<h'+hm[1].length+'>'+inline(hm[2])+'</h'+hm[1].length+'>');i++;continue;}
    if(/^\s*(-{3,}|\*{3,})\s*$/.test(ln)){out.push('<hr>');i++;continue;}
    if(ln.indexOf('|')>=0&&i+1<lines.length&&isSep(lines[i+1])){
      var head=cells(ln);i+=2;var rows=[];
      while(i<lines.length&&lines[i].indexOf('|')>=0&&lines[i].trim()){rows.push(cells(lines[i]));i++;}
      var t='<table><thead><tr>'+head.map(function(c){return '<th>'+inline(c)+'</th>';}).join('')+'</tr></thead><tbody>';
      t+=rows.map(function(r){return '<tr>'+r.map(function(c){return '<td>'+inline(c)+'</td>';}).join('')+'</tr>';}).join('');
      out.push(t+'</tbody></table>');continue;}
    if(/^\s*&gt;\s?/.test(ln)){var q=[];
      while(i<lines.length&&/^\s*&gt;\s?/.test(lines[i])){q.push(lines[i].replace(/^\s*&gt;\s?/,''));i++;}
      out.push('<blockquote>'+inline(q.join('<br>'))+'</blockquote>');continue;}
    if(/^\s*[-*+]\s+/.test(ln)){var ul=[];
      while(i<lines.length&&/^\s*[-*+]\s+/.test(lines[i])){ul.push('<li>'+inline(lines[i].replace(/^\s*[-*+]\s+/,''))+'</li>');i++;}
      out.push('<ul>'+ul.join('')+'</ul>');continue;}
    if(/^\s*\d+[.、)]\s+/.test(ln)){var ol=[];
      while(i<lines.length&&/^\s*\d+[.、)]\s+/.test(lines[i])){ol.push('<li>'+inline(lines[i].replace(/^\s*\d+[.、)]\s+/,''))+'</li>');i++;}
      out.push('<ol>'+ol.join('')+'</ol>');continue;}
    var para=[ln];i++;
    while(i<lines.length&&lines[i].trim()&&!/^(#{1,6}\s|\s*[-*+]\s|\s*\d+[.、)]\s|\s*&gt;)/.test(lines[i])&&!/^\u0000F\d+\u0000\s*$/.test(lines[i])){para.push(lines[i]);i++;}
    out.push('<p>'+inline(para.join('<br>'))+'</p>');
  }
  return out.join('\n').replace(/\u0000F(\d+)\u0000/g,function(m,n){return fences[+n];});
}

/* 公式保护：Markdown 会把 LaTeX 里的下划线当成斜体强调，
   $\text{SNR}_{\text{th}} = 2^\eta - 1$ 这种写法一旦被排版库吃掉下划线，
   整段正文会跟着变斜体、公式也废了。所以排版前先把公式摘出来占位，
   排版完放回去，再交给 KaTeX。 */
function protectMath(text){
  var store=[];
  var s=String(text==null?'':text)
    .replace(/\$\$[\s\S]+?\$\$/g,function(m){store.push(m);return '\u0000K'+(store.length-1)+'\u0000';})
    .replace(/\$(?:[^$\n])+?\$/g,function(m){store.push(m);return '\u0000K'+(store.length-1)+'\u0000';});
  // 正文里的波浪号会被排版库当成标记（6~10dB 与下一个 ~ 之间的文字会变成下标），
  // 摘完公式后先换成占位符。不能用 HTML 实体：本地兜底渲染器还会再转义一次，
  // 实体就会以 "&#126;" 的字面形态漏到页面上。
  s = s.replace(/~/g, '\u0000W\u0000');
  return [s,store];
}
function restoreMath(html,store){
  return String(html).replace(/\u0000K(\d+)\u0000/g,function(m,i){return store[+i]==null?m:store[+i];})
                     .replace(/\u0000W\u0000/g,'~');
}
"""

_RESEARCH_HTML_V2 = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI for Comm — 科研任务报告</title>
<!-- Markdown 渲染 -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<!-- 数学公式渲染 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<!-- 代码高亮 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9/build/styles/atom-one-dark.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9/build/highlight.min.js"></script>
<style>
%(style)s
</style>
</head>
<body>

<div class="cover">
  <div class="cover-inner">
    <div class="eyebrow">AI FOR COMM · 科研任务报告</div>
    <h1>%(topic)s</h1>
    <div class="verdict-badge %(verdict_cls)s">%(verdict_short)s</div>
    %(kw_html)s
    <div class="meta-row">
      <div class="meta-item">生成时间<b>%(timestamp)s</b></div>
      <div class="meta-item">参与 Agent<b>%(n_agents)s</b></div>
      <div class="meta-item">子问题<b>%(n_angles)s</b></div>
      <div class="meta-item">总耗时（秒）<b>%(total_time)s</b></div>
      <div class="meta-item">平台<b>OpenTrek</b></div>
    </div>
  </div>
</div>

<div class="container">
%(summary_section)s

  <section class="chapter">
    <div class="ch-head"><span class="ch-no">Ⅰ</span><h2>协作链路</h2>
      <span class="ch-src">拆解→调研→专家→校验→统稿→渲染</span></div>
    <div class="timeline">
      <div class="tl-node"><div class="tl-dot">01</div><div class="tl-lbl">问题拆解</div><div class="tl-sub">%(planner)s</div></div>
      <div class="tl-node"><div class="tl-dot">02</div><div class="tl-lbl">文献调研</div><div class="tl-sub">公网 + 平台KB</div></div>
      <div class="tl-node"><div class="tl-dot">03</div><div class="tl-lbl">并行专家</div><div class="tl-sub">%(experts_line)s</div></div>
      <div class="tl-node"><div class="tl-dot">04</div><div class="tl-lbl">综合校验</div><div class="tl-sub">verify_agent</div></div>
      <div class="tl-node gold"><div class="tl-dot">05</div><div class="tl-lbl">报告统稿</div><div class="tl-sub">report_agent</div></div>
      <div class="tl-node gold"><div class="tl-dot">06</div><div class="tl-lbl">渲染交付</div><div class="tl-sub">本页</div></div>
    </div>
    <div style="margin-top:34px;">
      <table class="plan">
        <tr><th style="width:36px">#</th><th>子问题</th><th style="width:110px">负责专家</th></tr>
        %(plan_rows)s
      </table>
    </div>
  </section>

  <section class="chapter">
    <div class="ch-head"><span class="ch-no">Ⅱ</span><h2>研究背景与文献综述</h2>
      <span class="ch-src">lit_review_agent</span></div>
%(background_html)s
    <details class="appendix-item"><summary>文献综述全文</summary>
      <div class="ap-body"><div class="prose md-src">%(literature)s</div></div>
    </details>
  </section>

  <section class="chapter">
    <div class="ch-head"><span class="ch-no">Ⅲ</span><h2>核心发现</h2>
      <span class="ch-src">领域专家论证</span></div>
%(findings_html)s
  </section>

%(cross_section)s

  <section class="chapter">
    <div class="ch-head"><span class="ch-no">Ⅴ</span><h2>校验意见</h2>
      <span class="ch-src">verify_agent</span></div>
    <div class="prose md-src">%(verdict)s</div>
  </section>

%(conclusion_section)s

  <section class="chapter">
    <div class="ch-head"><span class="ch-no">附录</span><h2>协作过程留痕</h2>
      <span class="ch-src">星型拓扑消息轨迹</span></div>
%(appendix_html)s
  </section>

</div>

<div class="footer">
  AI for Comm · 通信领域多智能体协作科研平台 · 六步流水线（拆解→调研→专家→校验→统稿→渲染）· Powered by OpenTrek
</div>

<script>
%(local_md_js)s
// 渲染 Markdown + 数学公式 + 代码高亮（外网排版库缺失时自动改用上面的本地渲染器）
document.addEventListener('DOMContentLoaded', function() {
  var parseMd = (window.marked && window.marked.parse)
    ? function(t){ return marked.parse(t); } : localMarkdown;
  if (window.marked && window.marked.setOptions) {
    try { marked.setOptions({ breaks: true, gfm: true }); } catch(e) {}
  }
  document.querySelectorAll('.md-src').forEach(function(el) {
    var raw = el.textContent;
    if (!raw || !raw.trim()) return;
    var guarded;
    try {
      guarded = protectMath(raw);
      el.innerHTML = restoreMath(parseMd(guarded[0]), guarded[1]);
    } catch(e) { el.style.whiteSpace = 'pre-wrap'; return; }
    if (window.hljs) {
      el.querySelectorAll('pre code').forEach(function(b) {
        try { hljs.highlightElement(b); } catch(e) {}
      });
    }
    try {
      renderMathInElement(el, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false},
          {left: '\\\\(', right: '\\\\)', display: false},
          {left: '\\\\[', right: '\\\\]', display: true}
        ],
        throwOnError: false
      });
    } catch(e) {}
  });
});
</script>
</body>
</html>"""


def generate_research_report(
    topic: str,
    plan: dict,
    literature: str,
    experts: list,
    verdict: str,
    total_time: str = "—",
    output_dir: str = "outputs",
    draft: dict = None,
    steps: list = None,
) -> str:
    """渲染科研任务流水线 HTML 报告（v2 靛蓝瓷高审美模板），返回文件路径。

    Args:
        plan:       ResearchPipeline._plan() 的输出 dict（含 planner / angles）
        literature: lit_review_agent 的综述文本（全文，不截断）
        experts:    [{question, extra, expert, agent, answer, images?, tools_used?}, ...]
        verdict:    verify_agent 综合校验文本
        draft:      report_agent 统稿结果（可为 None，降级为机械拼装）
        steps:      流水线星型拓扑消息轨迹（渲染到附录“协作过程留痕”）
    """
    os.makedirs(output_dir, exist_ok=True)
    # 渲染前的唯一文本收口：HTML 转义 + 公式卫生（见文件头 sanitize_math 注释）
    esc = lambda s: _esc_html(sanitize_math(s))

    # ── 三级评级（扉页徽章与文字共用）──
    if "【不通过】" in verdict:
        verdict_short, verdict_cls = "❌ 不通过", "v-fail"
    elif "【有条件通过】" in verdict:
        verdict_short, verdict_cls = "⚠️ 有条件通过", "v-warn"
    elif "【通过】" in verdict or "通过" in verdict:
        verdict_short, verdict_cls = "✅ 通过", "v-pass"
    elif "需修正" in verdict:
        verdict_short, verdict_cls = "⚠️ 需修正", "v-warn"
    else:
        verdict_short, verdict_cls = "🔍 待评审", "v-info"

    planner = plan.get("planner", "—") or "—"
    n_agents = 1 + (1 if literature and not literature.startswith("(") else 0) \
               + len(experts) + (1 if verdict and not verdict.startswith("(") else 0) \
               + (1 if draft else 0)
    experts_line = esc(", ".join(e["expert"] for e in experts) or "—")

    plan_rows = "\n".join(
        f"<tr><td>{i}</td><td>{esc(a['question'])}</td>"
        f"<td><span class=\"exp-tag\">{esc(a['expert'])}</span></td></tr>"
        for i, a in enumerate(plan.get("angles", []), 1)
    ) or "<tr><td colspan='3'>—</td></tr>"

    kw_html = ""
    if draft and draft.get("keywords"):
        kw_html = '<div class="kw">' + "".join(
            f"<span>{esc(k)}</span>" for k in draft["keywords"]) + "</div>"

    # ── 执行摘要（置顶章节，统稿缺失时降级为课题信息）──
    if draft and draft.get("summary"):
        summary_section = (
            '\n  <section class="chapter">\n'
            '    <div class="ch-head"><span class="ch-no">00</span><h2>执行摘要</h2>'
            '<span class="ch-src">report_agent 统稿</span></div>\n'
            f'    <div class="lead"><div class="prose md-src">{esc(draft["summary"])}</div></div>\n'
            '  </section>\n')
    else:
        summary_section = ""

    # ── 背景：统稿提炼优先，综述全文收进折叠附录 ──
    background_html = ""
    if draft and draft.get("background"):
        background_html = f'    <div class="prose md-src" style="margin-bottom:18px;">{esc(draft["background"])}</div>'

    # ── 核心发现：分节统稿正文（600~800 字/节，公式与数值不删）+ 仿真图表直接入正文
    #              + 可展开的专家原文全貌（2026-09-02 内容量恢复）──
    by_expert = {e.get("expert"): e for e in experts}
    findings_parts = []
    if draft and draft.get("findings"):
        for i, f in enumerate(draft["findings"], 1):
            ekey = str(f.get("expert", "")).replace("_agent", "").strip()
            src = by_expert.get(ekey) or (experts[i - 1] if i - 1 < len(experts) else {})
            degrade_tag = ('<span class="details-tag">本节为原文直录，未经主编提炼</span>'
                           if f.get("degraded") else "")
            findings_parts.append(
                f'<div style="margin-bottom:32px;">'
                f'<h3 style="font-family:var(--serif);font-size:17px;margin-bottom:6px;">'
                f'{i}. {esc(f.get("title", "") or src.get("question", ""))} '
                f'<span class="exp-tag" style="font-size:11px;vertical-align:2px;">{esc(ekey or "专家")}</span>'
                f'{degrade_tag}</h3>'
                f'<div class="prose md-src">{esc(f.get("content", ""))}</div>'
                + _sim_images_html(src.get("images"))
                + _origin_details_html(src, esc)
                + '</div>')
    else:
        for i, e in enumerate(experts, 1):
            findings_parts.append(
                f'<div style="margin-bottom:32px;">'
                f'<h3 style="font-family:var(--serif);font-size:17px;margin-bottom:6px;">'
                f'{i}. {esc(e["question"])} '
                f'<span class="exp-tag" style="font-size:11px;vertical-align:2px;">{esc(e["expert"])}</span>'
                f'<span class="details-tag">未统稿，正文为专家原文</span></h3>'
                f'<div class="prose md-src">{esc(e["answer"])}</div>'
                + _sim_images_html(e.get("images")) + '</div>')
    findings_html = "\n".join(findings_parts)

    # ── 交叉分析（仅统稿存在时展示，章节编号随动）──
    cross_section = ""
    if draft and draft.get("cross_analysis"):
        cross_section = (
            '\n  <section class="chapter">\n'
            '    <div class="ch-head"><span class="ch-no">Ⅳ</span><h2>交叉分析</h2>'
            '<span class="ch-src">report_agent</span></div>\n'
            f'    <div class="prose md-src">{esc(draft["cross_analysis"])}</div>\n'
            '  </section>\n')

    # ── 综合结论与展望 ──
    conclusion_section = ""
    if draft and (draft.get("conclusion") or draft.get("outlook")):
        conclusion_section = (
            '\n  <section class="chapter">\n'
            '    <div class="ch-head"><span class="ch-no">Ⅵ</span><h2>综合结论与展望</h2>'
            '<span class="ch-src">report_agent</span></div>\n'
            f'    <div class="lead" style="margin-bottom:18px;"><div class="prose md-src">{esc(draft.get("conclusion", ""))}</div></div>'
            + (f'<div class="prose md-src"><h3>后续展望</h3><p>{esc(draft["outlook"])}</p></div>'
               if draft.get("outlook") else "")
            + '\n  </section>\n')

    # ── 附录：星型拓扑消息轨迹 + 各环节材料体量清单（过程可追溯、原文可定位）──
    appendix_html = _process_trace_html(steps, experts, literature, verdict, draft, esc)

    html = _RESEARCH_HTML_V2 % {
        "style": _RESEARCH_STYLE_V2,
        "local_md_js": _LOCAL_MD_JS,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": esc(topic),
        "verdict_short": verdict_short,
        "verdict_cls": verdict_cls,
        "kw_html": kw_html,
        "n_agents": n_agents,
        "n_angles": len(plan.get("angles", [])),
        "total_time": total_time,
        "summary_section": summary_section,
        "planner": esc(planner),
        "experts_line": experts_line,
        "plan_rows": plan_rows,
        "background_html": background_html,
        "literature": esc(literature),
        "findings_html": findings_html,
        "cross_section": cross_section,
        "verdict": esc(verdict),
        "conclusion_section": conclusion_section,
        "appendix_html": appendix_html,
    }

    filename = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def _sim_images_html(images: list) -> str:
    """仿真图表区块（base64 PNG 嵌入）"""
    if not images:
        return ""
    items = "\n".join(
        f'<div class="sim-figure"><img src="data:image/png;base64,{b64}" alt="仿真图表"></div>'
        for b64 in images)
    return f'<h3 style="font-family:var(--serif);margin:14px 0 6px;color:var(--pass);">📊 仿真图表</h3>{items}'


def _origin_details_html(src: dict, esc) -> str:
    """核心发现每节末尾的“专家原文全貌”折叠区：默认收起，点开即见未删减论证。"""
    raw = (src.get("answer") or "").strip()
    if not raw:
        return ""
    meta = [f"{len(raw)} 字"]
    if src.get("extra"):
        meta.append(f"含 {len(src['extra'])} 个补充子问题")
    if src.get("tools_used"):
        meta.append("本地工具：" + "、".join(src["tools_used"]))
    return ('<details class="appendix-item origin"><summary>展开本专家原文全貌'
            f'<span class="ap-meta">{" · ".join(meta)}</span></summary>'
            f'<div class="ap-body"><div class="prose md-src">{esc(raw)}</div></div></details>')


_STEP_NAMES = {"plan": "问题拆解", "literature": "文献调研", "experts": "专家论证",
               "correction": "闭环修正", "verify": "综合校验", "compile": "报告统稿"}


def _process_trace_html(steps, experts, literature, verdict, draft, esc) -> str:
    """附录：星型拓扑消息轨迹表 + 各环节材料体量与全文位置。"""
    parts = []
    rows = "\n".join(
        f"<tr><td>{i}</td><td>{esc(_STEP_NAMES.get(s.get('step'), s.get('step', '')))}</td>"
        f"<td>{esc(s.get('from', ''))}</td><td>{esc(s.get('to', ''))}</td>"
        f"<td>{esc(s.get('type', ''))}</td>"
        f"<td style='text-align:right'>{s.get('chars', 0)}</td></tr>"
        for i, s in enumerate(steps or [], 1))
    if rows:
        parts.append(
            '<p style="font-size:13px;color:#5a6577;margin-bottom:10px;">'
            f'本次研究共 {len(steps or [])} 条星型拓扑消息（所有中转方均为 '
            'orchestrator，智能体之间不直接对话）。</p>'
            '<div style="overflow-x:auto;"><table class="plan" style="font-size:13px;">'
            '<tr><th>#</th><th>环节</th><th>发送方</th><th>接收方</th>'
            '<th>消息类型</th><th style="text-align:right">字符数</th></tr>'
            + rows + "</table></div>")

    mat_rows = []

    def add(label, text, note=""):
        n = len(text or "")
        if n:
            mat_rows.append(f"<tr><td>{esc(label)}</td>"
                            f"<td style='text-align:right'>{n} 字</td>"
                            f"<td>{esc(note)}</td></tr>")

    add("文献综述", literature, "全文见第Ⅱ章“文献综述全文”")
    for e in experts:
        add(f"{e.get('expert')}_agent 论证原文", e.get("answer"),
            "全文见第Ⅲ章对应小节“原文全貌”")
    add("综合校验意见", verdict, "全文见第Ⅴ章")
    if draft:
        add("统稿正文（核心发现合计）",
            "".join(f.get("content", "") for f in draft.get("findings", [])),
            f"{len(draft.get('findings', []))} 节·第Ⅲ章")
    if mat_rows:
        parts.append('<div style="margin-top:20px;overflow-x:auto;">'
                     '<table class="plan" style="font-size:13px;">'
                     '<tr><th>材料</th><th style="text-align:right">体量</th>'
                     '<th>全文位置</th></tr>' + "\n".join(mat_rows) + "</table></div>")
    return "\n".join(parts) or '<p style="color:#9aa3b0;">无过程记录</p>'


# ═══════════════════════════════════════════════════
#  v1 机械拼装模板（历史版本，仅作回退参考，不再被调用）
# ═══════════════════════════════════════════════════

_RESEARCH_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI for Comm — 科研任务报告</title>
<!-- Markdown 渲染 -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<!-- 数学公式渲染 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<!-- 代码高亮 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9/build/styles/atom-one-dark.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9/build/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9/build/languages/verilog.min.js"></script>
<style>
%(style)s
.badge-lit { background: #fff8e1; color: #f57f17; }
.badge-planner { background: #ede7f6; color: #4527a0; }
.badge-exp { background: #e3f2fd; color: #1565c0; }
.badge-sim { background: #e8f5e9; color: #2e7d32; }
.expert-answer, .lit-box { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 20px; font-size: 14px; line-height: 1.8; }
.expert-answer h1, .expert-answer h2, .expert-answer h3, .lit-box h1, .lit-box h2, .lit-box h3 { margin: 12px 0 6px; color: #1a237e; }
.expert-answer h1 { font-size: 20px; } .expert-answer h2 { font-size: 17px; } .expert-answer h3 { font-size: 15px; }
.expert-answer p, .lit-box p { margin: 6px 0; }
.expert-answer ul, .expert-answer ol, .lit-box ul, .lit-box ol { padding-left: 24px; margin: 6px 0; }
.expert-answer code, .lit-box code { background: #e8eaf6; padding: 1px 5px; border-radius: 3px; font-size: 13px; }
.expert-answer pre, .lit-box pre { background: #263238; color: #e0e0e0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 10px 0; }
.expert-answer pre code, .lit-box pre code { background: none; padding: 0; color: inherit; }
.expert-answer table, .lit-box table { border-collapse: collapse; margin: 10px 0; width: 100%%; }
.expert-answer th, .expert-answer td, .lit-box th, .lit-box td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 13px; }
.expert-answer th, .lit-box th { background: #e8eaf6; }
.expert-answer blockquote, .lit-box blockquote { border-left: 4px solid #1a237e; padding-left: 12px; color: #555; margin: 8px 0; }
.sim-figure { text-align: center; margin: 16px 0; }
.sim-figure img { max-width: 100%%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
table.plan { width: 100%%; border-collapse: collapse; font-size: 14px; }
table.plan th, table.plan td { border-bottom: 1px solid #eee; padding: 10px 12px; text-align: left; }
table.plan th { background: #f5f7fa; color: #555; }
</style>
</head>
<body>

<div class="header">
  <h1>AI for Comm — 科研任务协作报告</h1>
  <div class="meta">
    生成时间: %(timestamp)s &nbsp;|&nbsp;
    平台: OpenTrek &nbsp;|&nbsp;
    模式: 科研任务流水线（拆解→调研→专家→校验→统稿→渲染）
  </div>
</div>

<div class="container">

  <div class="stats">
    <div class="stat-card"><div class="value">%(n_agents)s</div><div class="label">参与 Agent</div></div>
    <div class="stat-card"><div class="value">%(n_angles)s</div><div class="label">子问题数</div></div>
    <div class="stat-card"><div class="value">%(total_time)s</div><div class="label">总耗时（秒）</div></div>
    <div class="stat-card"><div class="value">%(verdict_short)s</div><div class="label">校验结论</div></div>
  </div>

  <div class="card">
    <div class="card-header">🎯 研究课题</div>
    <div class="card-body"><b>%(topic)s</b>&nbsp;<span class="badge badge-planner">规划者 %(planner)s</span></div>
  </div>

  <div class="card">
    <div class="card-header">🔄 协作流程</div>
    <div class="flow">
      <div class="flow-node"><div class="icon">🗺️</div><div class="label">问题拆解</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">%(planner)s</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node" style="border-color:#f57f17;background:#fffbf0;">
        <div class="icon">📚</div><div class="label">文献调研</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">公网 + 平台KB</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="icon">🧑‍🔬</div><div class="label">并行专家</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">%(experts_line)s</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="icon">✅</div><div class="label">综合校验</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">verify_agent</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="icon">📄</div><div class="label">HTML 报告</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">本页</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">🗂️ 任务拆解</div>
    <div class="card-body">
      <table class="plan">
        <tr><th>#</th><th>子问题</th><th>负责专家</th></tr>
        %(plan_rows)s
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="badge badge-lit">lit_review_agent</span> 文献综述</div>
    <div class="card-body"><div class="lit-box">%(literature)s</div></div>
  </div>

%(expert_cards)s

  <div class="card">
    <div class="card-header"><span class="badge badge-verify">verify_agent</span> 综合校验意见</div>
    <div class="card-body"><div class="feedback-box">%(verdict)s</div></div>
  </div>

</div>

<div class="footer">
  AI for Comm · 通信领域多 Agent 协作智能问答系统 · Powered by OpenTrek
</div>

<script>
// 渲染 Markdown + 数学公式 + 代码高亮
document.addEventListener('DOMContentLoaded', function() {
  marked.setOptions({ breaks: true, gfm: true,
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try { return hljs.highlight(code, { language: lang }).value; } catch(e) {}
      }
      return hljs.highlightAuto(code).value;
    }
  });
  ['.expert-answer', '.lit-box', '.feedback-box', '.derivation-box'].forEach(function(sel) {
    document.querySelectorAll(sel).forEach(function(el) {
      var raw = el.textContent;
      if (!raw || !raw.trim()) return;
      try { el.innerHTML = marked.parse(raw); } catch(e) { el.style.whiteSpace = 'pre-wrap'; return; }
      try {
        renderMathInElement(el, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\\\(', right: '\\\\)', display: false},
            {left: '\\\\[', right: '\\\\]', display: true}
          ],
          throwOnError: false
        });
      } catch(e) {}
    });
  });
});
</script>
</body>
</html>"""
