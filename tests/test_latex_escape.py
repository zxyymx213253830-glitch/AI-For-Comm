# -*- coding: utf-8 -*-
r"""LaTeX 转义救援回归：JSON 转义吃掉 LaTeX 命令首字母后必须能还原。

背景（2026-09-02 用户反馈"报告里有些地方是 text 源码"）：
report_agent 的结构化统稿走 JSON，模型把 $P_{\text{eff}}$ 直写进字符串，
"\t" 被 json.loads 当成制表符吃掉，公式变成 $P_{<TAB>ext{eff}}$，
KaTeX 解析失败、按 throwOnError:false 原样标红 —— 页面上就露出源码。
同理中招的还有 \times \theta \to \frac \rho \bar \beta \nu \nabla \begin。

本测试不依赖平台，覆盖：
  1. restore_latex_ctrl 逐命令还原；
  2. 正文真换行、真制表符不被误伤；
  3. pipeline._undo_json_escapes 递归清洗嵌套结构；
  4. _fix_escapes 修复 \underline 这类"非法 \u"导致整段 JSON 解析失败；
  5. _parse_draft 端到端出干净正文；
  6. 渲染出的 HTML 里不再有控制字符残渣。
运行：python tests/test_latex_escape.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.report import (restore_latex_ctrl, sanitize_math,            # noqa: E402
                         generate_research_report)
from core.pipeline import ResearchPipeline                             # noqa: E402

PASSED = [0, 0]
BS = chr(92)      # 反斜杠：测试里用拼接而不是字面量，避免多层转义看走眼


def check(name, ok, detail=""):
    PASSED[0 if ok else 1] += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def eaten(inner: str) -> str:
    """把 inner（形如 BS+"text x"）以单反斜杠形式塞进 JSON 再解码，
    复现模型直写公式被 json.loads 吃掉后的真实样子。"""
    return json.loads('{"s": "$' + inner + '$"}')["s"]


print("── case1 被吃掉的 LaTeX 命令逐个还原 ──")
for cmd in ("text", "textbf", "times", "theta", "to", "frac", "rho", "bar", "beta",
            "begin", "forall", "triangle", "tiny", "bmod", "nabla", "notin",
            "neq", "nu", "ne"):
    broken = eaten(BS + cmd + " x")
    got = restore_latex_ctrl(broken)
    check(f"{BS}{cmd} 还原", (BS + cmd + " x") in got, repr(got))

print("\n── case2 换行类命令（\\nu \\nabla）与正文真换行的区分 ──")
nu = eaten(BS + "nu = 3")
check("公式内 \\nu 还原", (BS + "nu = 3") in restore_latex_ctrl(nu),
      repr(restore_latex_ctrl(nu)))
nabla = eaten(BS + "nabla h")
check("公式内 \\nabla 还原", (BS + "nabla h") in restore_latex_ctrl(nabla),
      repr(restore_latex_ctrl(nabla)))
body = "第一段\n第二段：链路预算与功率回退。\n\n第三段继续。"
check("正文换行与段落原样保留", restore_latex_ctrl(body) == body,
      repr(restore_latex_ctrl(body)))
body_en = "conclusion\nend of the list\ne.g. values"
check("英文换行不被误认成 \\ne", restore_latex_ctrl(body_en) == body_en,
      repr(restore_latex_ctrl(body_en)))

print("\n── case3 真制表符与正常公式不误伤 ──")
tab_text = "指标\t数值\t单位"
check("纯表格制表符原样保留", restore_latex_ctrl(tab_text) == tab_text,
      repr(restore_latex_ctrl(tab_text)))
ok_math = "$C = B " + BS + "log_2(1+" + BS + "text{SNR})$"
check("本来正确的公式零改动", restore_latex_ctrl(ok_math) == ok_math)
check("空值安全", restore_latex_ctrl(None) == "" and restore_latex_ctrl(123) == "123")

print("\n── case4 pipeline 递归清洗嵌套结构 ──")
# 模型直写的统稿 JSON：\text 的 \t 会被吃掉，\log 则是非法转义（要靠 _fix_escapes）
raw_json = ('{"summary": "容量 $C = B ' + BS + 'log_2(1+' + BS + 'text{SNR})$",'
            ' "findings": [{"title": "链路预算", "content": "$P_{' + BS + 'text{eff}}'
            ' = P_{' + BS + 'text{sat}} - ' + BS + 'text{OBO}$"}],'
            ' "keywords": ["' + BS + 'text{NR}"]}')
data = json.loads(ResearchPipeline._fix_escapes(raw_json))
check("_fix_escapes 后 \\log 完整", (BS + "log_2") in data["summary"], repr(data["summary"]))
check("解析结果确实带制表符损伤", "\t" in data["summary"], repr(data["summary"]))
clean = ResearchPipeline._undo_json_escapes(data)
check("summary 内 \\text 还原", (BS + "text{SNR}") in clean["summary"], repr(clean["summary"]))
check("嵌套 findings 内还原", (BS + "text{eff}") in clean["findings"][0]["content"],
      repr(clean["findings"][0]["content"]))
check("列表字段同样清洗", clean["keywords"] == [BS + "text{NR}"], str(clean["keywords"]))
check("清洗后无控制字符",
      not any(c in json.dumps(clean, ensure_ascii=False) for c in "\t\b\f\r"))

print("\n── case5 _fix_escapes 处理非法 \\u ──")
frag = '{"s": "$' + BS + 'underline{x} + ' + BS + 'sqrt{2}$"}'
try:
    json.loads(frag)
    direct = True
except ValueError:
    direct = False
fixed = ResearchPipeline._fix_escapes(frag)
check("原文直接解析会失败", not direct)
check("修复后可解析", isinstance(json.loads(fixed), dict))
check("修复后 \\underline 与 \\sqrt 完整",
      (BS + "underline{x}") in json.loads(fixed)["s"]
      and (BS + "sqrt{2}") in json.loads(fixed)["s"], repr(json.loads(fixed)["s"]))

print("\n── case6 _parse_draft 端到端出干净正文 ──")
draft_raw = ('{"summary": "本报告给出 $P_{' + BS + 'text{eff}}$ 与 $R ' + BS
             + 'times 1024$ 的关系。", "findings": [{"title": "功率", "expert": "hw",'
             ' "content": "$P_{' + BS + 'text{eff}}(' + BS + 'text{dBm}) = P_{' + BS
             + 'text{sat}} - ' + BS + 'text{OBO}$"}]}')
draft = ResearchPipeline._parse_draft(draft_raw, require_field="summary")
check("解析成功", bool(draft))
if draft:
    check("summary 含 \\text 且无制表符",
          (BS + "text{eff}") in draft["summary"] and "\t" not in draft["summary"],
          repr(draft["summary"]))
    check("summary 含 \\times", (BS + "times 1024") in draft["summary"],
          repr(draft["summary"]))
    check("findings 正文含 \\text{sat}",
          (BS + "text{sat}") in draft["findings"][0]["content"],
          repr(draft["findings"][0]["content"]))

print("\n── case7 渲染出的 HTML 无控制字符残渣 ──")
# 下面用非 raw 字符串，让 Python 自己把 \text 变成 TAB+ext，
# 等价于 json.loads 之后的真实损伤现场，验证渲染前 esc 这道收口能救回来。
tmp = tempfile.mkdtemp(prefix="latex_fix_")
path = generate_research_report(
    topic="链路预算与功率回退",
    plan={"planner": "planner_agent", "topic": "链路预算",
          "angles": [{"question": "$P_{\text{eff}}$ 怎么算？", "expert": "hw"}]},
    literature="参考文献综述。",
    experts=[{"question": "$P_{\text{eff}}$ 怎么算？", "expert": "hw", "agent": "hw_agent",
              "answer": "$$P_{\text{eff}} = P_{\text{sat}} - \text{OBO}$$\n\n"
                        "峰均比高时需要回退。"}],
    verdict="【通过】公式与数值一致。",
    draft={"summary": "$R \times 1024 = 60$。", "background": "",
           "findings": [{"title": "功率", "expert": "hw",
                         "content": "$P_{\text{eff}}(\text{dBm})$ 见下式，"
                                    "其中回退量记为 $\text{PAPR_Margin}$。"}],
           "cross_analysis": "", "conclusion": "$\theta \to 0$ 时收敛。",
           "outlook": "", "keywords": ["NR"]},
    output_dir=tmp,
)
html = open(path, encoding="utf-8").read()
body_html = html[html.index('<div class="cover">'):]
bad = [c for c in ("\t", "\b", "\f", "\r") if c in body_html]
check("正文无制表符/退格/换页/回车残渣", not bad, str(bad))
check("正文里 \\text 完整", (BS + "text{eff}") in body_html)
check("正文里 \\times 完整", (BS + "times 1024") in body_html)
check("正文里 \\theta 与 \\to 完整",
      (BS + "theta") in body_html and (BS + "to 0") in body_html)
check("专家原文的真换行仍保留", "峰均比高时需要回退。" in body_html)
check("\\text 内下划线已转义", (BS + "text{PAPR" + BS + "_Margin}") in body_html)
check("KaTeX 分隔符配置未被误改", "$$', right: '$$" in body_html)
os.remove(path)
os.rmdir(tmp)

print("\n── case8 \\text{} 里的下划线转成 KaTeX 可接受写法 ──")
# 实测：\text{PAPR_Margin} 会让 KaTeX 报 ParseError，整条公式标红并露出源码
bad_math = "$P_" + BS + "text{OBO} - " + BS + "text{PAPR_Margin}$"
got = sanitize_math(bad_math)
check("\\text 内下划线被转义", (BS + "text{PAPR" + BS + "_Margin}") in got, repr(got))
check("\\text 外的真下标不受影响", "$P_" in got and (BS + "text{OBO}") in got, repr(got))
check("不含 \\text 时零改动", sanitize_math("$a_b + c^2$") == "$a_b + c^2$")
check("脱字符同样处理", (BS + "textasciicircum") in sanitize_math(BS + "text{a^b}"))
both = eaten(BS + "text{PAPR_Margin}")
got2 = sanitize_math(both)
check("被吃转义 + 非法下划线一次修好",
      (BS + "text{PAPR" + BS + "_Margin}") in got2 and "\t" not in got2, repr(got2))

print("\n" + "=" * 56)
print(f"总计: {PASSED[0]}/{PASSED[0] + PASSED[1]} 项通过")
sys.exit(0 if PASSED[1] == 0 else 1)
