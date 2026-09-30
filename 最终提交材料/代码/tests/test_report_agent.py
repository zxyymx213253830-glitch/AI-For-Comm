# -*- coding: utf-8 -*-
"""report_agent 统稿链路测试：JSON 容错解析 + 高审美模板渲染（含降级与内容量恢复）

不依赖平台网络：直接测 ResearchPipeline._parse_draft 与 core.report 渲染。
运行：python tests/test_report_agent.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pipeline import ResearchPipeline
from core.report import generate_research_report

# ── 测试材料（模拟一次 BPSK 课题的流水线产物）──

PLAN = {
    "topic": "BPSK 在 AWGN 信道下的误码率理论推导与仿真验证",
    "planner": "comm_agent",
    "angles": [
        {"question": "BPSK 在 AWGN 信道下的理论误码率公式是什么？", "expert": "math"},
        {"question": "如何用蒙特卡洛仿真验证 BPSK 误码率？", "expert": "sim"},
    ],
}

LITERATURE = (
    "## 文献综述\n"
    "BPSK 误码率经典结论见 Proakis《数字通信》(2001)：P_b = Q(sqrt(2*Eb/N0))。"
    "3GPP TS 36.212 中链路预算亦采用该式。"
)

EXPERTS = [
    {
        "question": "BPSK 在 AWGN 信道下的理论误码率公式是什么？",
        "extra": [], "expert": "math", "agent": "math_agent",
        "answer": "## 推导\n由匹配滤波器输出信噪比得 $P_b = Q\\left(\\sqrt{2E_b/N_0}\\right)$，"
                  "其中 $Q(x)=\\frac{1}{\\sqrt{2\\pi}}\\int_x^\\infty e^{-t^2/2}dt$。",
        "tools_used": [],
    },
    {
        "question": "如何用蒙特卡洛仿真验证 BPSK 误码率？",
        "extra": [], "expert": "sim", "agent": "sim_agent",
        "answer": "## 仿真方案\n固定随机种子，逐点统计误码数，低误码率点保证 ≥100 个错误。",
        "tools_used": ["运行 Python 仿真"],
        "images": [],
    },
]

VERDICT = "【通过】\n核对了理论公式与仿真方案，二者一致，无原理性错误。"

DRAFT = {
    "summary": "本报告研究 BPSK 在 AWGN 信道下的误码率，理论推导与蒙特卡洛仿真互相印证，校验结论为通过。",
    "background": "BPSK 误码率是链路预算的基础（Proakis 2001）。",
    "findings": [
        {"title": "理论误码率公式", "expert": "math",
         "content": ("匹配滤波后抽样统计量服从高斯分布，两信号点间距 d=2√Eb，"
                     "错判概率为尾积分，整理得 $P_b = Q(\\sqrt{2E_b/N_0})$；"
                     "与信噪比换算 $SNR = E_b/N_0 \\times R_b/B$ 联用，"
                     + "推导各步保留量纲核对与特殊值代入检验。" * 32)},
        {"title": "蒙特卡洛验证", "expert": "sim",
         "content": "固定随机种子逐点统计，与理论曲线一致。" * 32},
    ],
    "cross_analysis": "理论推导与仿真结果互相印证。",
    "conclusion": "【通过】核心结论正确。",
    "outlook": "建议扩展至 QPSK 与衰落信道。",
    "keywords": ["BPSK", "AWGN", "误码率", "蒙特卡洛"],
}

PNG_1PX = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
           "AAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")

STEPS = [
    {"step": "plan", "from": "comm_agent", "to": "orchestrator",
     "type": "angle@math", "chars": 32},
    {"step": "experts", "from": "math_agent", "to": "orchestrator",
     "type": "answer", "chars": 1955},
    {"step": "compile", "from": "report_agent", "to": "orchestrator",
     "type": "digest@math", "chars": 820},
]


def test_parse_draft_ok():
    """裸 JSON / 围栏包裹 / 前后杂文 / 单引号 均应解析成功"""
    import json
    raw_ok = json.dumps(DRAFT, ensure_ascii=False)
    assert ResearchPipeline._parse_draft(raw_ok)["summary"] == DRAFT["summary"]
    assert ResearchPipeline._parse_draft("```json\n" + raw_ok + "\n```")
    assert ResearchPipeline._parse_draft("以下是统稿结果：\n" + raw_ok)
    assert ResearchPipeline._parse_draft("") is None
    assert ResearchPipeline._parse_draft("完全不是 JSON 的文字") is None
    # summary 缺失视为无效
    assert ResearchPipeline._parse_draft('{"background": "x"}') is None
    print("  [PASS] JSON 容错解析")


def test_render_with_draft():
    """有统稿：四大统稿章节齐全，且核心发现为长正文 + 原文可展开 + 图表入正文"""
    import re
    experts = [dict(e) for e in EXPERTS]
    experts[1]["images"] = [PNG_1PX]
    out = tempfile.mkdtemp()
    path = generate_research_report(
        topic=PLAN["topic"], plan=PLAN, literature=LITERATURE,
        experts=experts, verdict=VERDICT, total_time="88",
        output_dir=out, draft=DRAFT, steps=STEPS)
    html = open(path, encoding="utf-8").read()
    for marker in ["执行摘要", "报告统稿", "交叉分析", "综合结论与展望",
                   "附录", "靛蓝", "v-pass", "BPSK", "展开本专家原文全貌",
                   "协作过程留痕", "angle@math", "digest@math"]:
        assert marker in html, f"模板缺少：{marker}"

    # 正文体量：核心发现章节不得再被压到百字量级（2026-09-02 内容量恢复）
    seg = html.split("<h2>核心发现</h2>")[1].split("</section>")[0]
    body = re.sub(r"<[^>]+>", "", seg)
    assert len(body) >= 1200, f"核心发现正文字数偏少：{len(body)}"

    # 仿真图表必须出现在核心发现里（而不是只在折叠附录）
    assert "data:image/png;base64," in seg, "仿真图表未随分节统稿入正文"
    # 专家原文全貌就在对应小节内，且未被截断
    assert EXPERTS[0]["answer"][:12] in html
    print(f"  [PASS] 统稿版渲染（核心发现正文 {len(body)} 字）→ {path}")
    return path


def test_render_fallback():
    """无统稿（降级）：报告仍生成，专家原文直接进核心发现"""
    out = tempfile.mkdtemp()
    path = generate_research_report(
        topic=PLAN["topic"], plan=PLAN, literature=LITERATURE,
        experts=EXPERTS, verdict=VERDICT, total_time="88",
        output_dir=out, draft=None)
    html = open(path, encoding="utf-8").read()
    assert "协作链路" in html and "BPSK" in html
    assert "执行摘要" not in html  # 降级时不出现统稿章节
    assert "未统稿，正文为专家原文" in html
    print(f"  [PASS] 降级版渲染 → {path}")


if __name__ == "__main__":
    print("report_agent 统稿链路测试")
    test_parse_draft_ok()
    test_render_with_draft()
    test_render_fallback()
    print("全部通过")
