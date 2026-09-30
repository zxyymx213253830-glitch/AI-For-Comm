# -*- coding: utf-8 -*-
"""
本地工具层离线验收测试 —— 不依赖 OpenTrek 平台，纯本地可跑

覆盖：
  1. 注册一致性：7 个工具全部自注册，Agent 权限白名单无悬空引用
  2. 符号数学（sympy_compute / sympy_check_equality）
  3. 通信算法库（comm_lib）：理论 BER、香农容量、蒙特卡洛对照教科书值
  4. 仿真执行（run_python）：真实执行 + 图表回收 + 错误容错
  5. 协议查询（protocol_lookup）：本地知识库命中
  6. 硬件仿真（run_verilog）：仿真器缺席优雅降级 / 装了则真编译
  7. 文献检索（search_papers）：降级与空结果路径（公网真检索需传 --net）
  8. 伪工具调用协议（tool_driver）：请求提取容错 + 定稿剥离标记

运行：
  .venv\\Scripts\\python.exe tests\\test_tools.py          # 全离线，不访问公网
  .venv\\Scripts\\python.exe tests\\test_tools.py --net    # 附带 arXiv 真检索用例
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools                                        # noqa: E402  触发 @tool 自注册
from tools import label as tools_label              # noqa: E402
from tools.registry import _REGISTRY, TOOL_PERMISSIONS, catalog_for   # noqa: E402
from core.tool_driver import extract_tool_calls, _strip_marks         # noqa: E402

EXPECTED_TOOLS = {
    "sympy_compute", "sympy_check_equality", "search_papers", "run_python",
    "comm_lib", "run_verilog", "protocol_lookup",
}

_TESTS = []          # [(section, name, func)]
_SECTION = ["注册层"]


def case(name):
    """登记一个用例；section() 用于切换分组标题。"""
    def deco(fn):
        _TESTS.append((_SECTION[0], name, fn))
        return fn
    return deco


def section(title):
    _SECTION[0] = title


def close(a, b, rel=1e-3):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


# ═══════════════════════════════════════════════════
#  1. 注册层
# ═══════════════════════════════════════════════════

@case("工具注册表完整（7 个工具全部自注册）")
def _t_registry():
    assert set(_REGISTRY) == EXPECTED_TOOLS, \
        f"缺 {EXPECTED_TOOLS - set(_REGISTRY)} / 多 {set(_REGISTRY) - EXPECTED_TOOLS}"


@case("Agent 权限白名单无悬空工具、无无人使用的工具")
def _t_perms():
    dangling = {a: [t for t in ts if t not in _REGISTRY]
                for a, ts in TOOL_PERMISSIONS.items()}
    dangling = {k: v for k, v in dangling.items() if v}
    assert not dangling, f"白名单引用了未注册工具: {dangling}"
    unclaimed = [t for t in _REGISTRY
                 if not any(t in v for v in TOOL_PERMISSIONS.values())]
    assert not unclaimed, f"工具无人可用（漏配权限）: {unclaimed}"


@case("工具中文短名齐全（前端展示不依赖英文原名）")
def _t_labels():
    from tools.registry import TOOL_LABELS
    missing = [t for t in _REGISTRY if t not in TOOL_LABELS or not TOOL_LABELS[t]]
    assert not missing, f"无中文名: {missing}"
    assert tools_label("comm_lib") == "通信算法库"
    assert tools_label("不存在的工具") == "不存在的工具", "未知工具应原样返回"


@case("工具说明书可注入提示词（含请求标记与工具名）")
def _t_catalog():
    cat = catalog_for("sim_agent")
    assert "〔工具请求〕" in cat and "run_python" in cat and "comm_lib" in cat
    assert catalog_for("lit_review_agent") == "", "文献 Agent 不应有工具说明书"


@case("未知工具 / 参数错误均返回中文提示且不抛异常")
def _t_unknown_tool():
    assert tools.execute("no_such_tool", {})["ok"] is False
    r = tools.execute("comm_lib", {"wrong_arg": 1})
    assert r["ok"] is False and "参数" in str(r["result"]), r


section("符号数学")


@case("高斯积分 ∫exp(-x²)dx = √π")
def _t_sympy_integral():
    r = tools.execute("sympy_compute", {"op": "definite_integrate",
                                        "expression": "exp(-x**2)",
                                        "var": "x", "extra": "-oo,oo"})
    assert r["ok"], r
    assert "pi" in r["result"]["结果"], r["result"]
    assert close(float(r["result"]["数值近似"]), math.sqrt(math.pi), 1e-6), r["result"]


@case("方程求解 x²-5x+6=0 → 2 和 3")
def _t_sympy_solve():
    r = tools.execute("sympy_compute", {"op": "solve",
                                        "expression": "x**2-5*x+6=0", "var": "x"})
    assert r["ok"], r
    assert {2, 3} <= set(eval(r["result"]["解"])), r["result"]


@case("恒等式复核：erfc(√(x/2))/2 ≡ Qfunc(√(x/2))")
def _t_sympy_equal():
    r = tools.execute("sympy_check_equality", {
        "left": "erfc(sqrt(x/2))/2", "right": "Qfunc(sqrt(x/2))"})
    assert r["ok"] and r["result"]["恒等"] is True, r["result"]


@case("能识破错误恒等式 √x ≢ x")
def _t_sympy_unequal():
    r = tools.execute("sympy_check_equality", {"left": "sqrt(x)", "right": "x"})
    assert r["ok"] and r["result"]["恒等"] is False, r["result"]


section("通信算法库")


@case("BPSK/AWGN 0dB 理论 BER ≈ 0.0787（= Q(√2)）")
def _t_comm_theo():
    r = tools.execute("comm_lib", {"action": "theo_ber", "scheme": "bpsk",
                                   "channel": "awgn", "ebn0_db": "0"})
    assert r["ok"], r
    assert close(r["result"]["理论误码率"][0], 0.07865, 5e-3), r["result"]


@case("BER 随 Eb/N0 单调下降（16QAM 0→10dB）且低信噪比不饱和在 0.5")
def _t_comm_monotone():
    r = tools.execute("comm_lib", {"action": "theo_ber", "scheme": "16qam",
                                   "channel": "awgn", "ebn0_db": "0,4,8,10"})
    assert r["ok"], r
    ber = r["result"]["理论误码率"]
    assert len(ber) == 4 and all(a > b for a, b in zip(ber, ber[1:])), ber
    assert ber[0] < 0.3, f"0dB 就到 {ber[0]}，低信噪比失真饱和"
    # 教科书近似校核：16QAM 0dB ≈ 0.14，8dB ≈ 9e-3
    assert close(ber[0], 0.14, 0.25), f"16QAM@0dB={ber[0]} 偏离教科书 0.14"
    assert close(ber[2], 9e-3, 0.35), f"16QAM@8dB={ber[2]} 偏离教科书 ~9e-3"


@case("16QAM 理论曲线与蒙特卡洛逐点吻合（自对自）")
def _t_comm_qam_selfcheck():
    r = tools.execute("comm_lib", {"action": "monte_carlo_ber", "scheme": "16qam",
                                   "channel": "awgn", "ebn0_db": "4,8",
                                   "nbits": 400000})
    assert r["ok"], r
    for row in r["result"]["结果"]:
        sim, theo = row["误码率"], row["理论值"]
        assert close(sim, theo, 0.15), f"{row['EbN0_dB']}dB: sim={sim} theo={theo}"


@case("香农容量 B=1MHz, SNR=10dB → 3.459 Mbps")
def _t_comm_shannon():
    r = tools.execute("comm_lib", {"action": "shannon",
                                   "bandwidth": 1e6, "snr_db": 10})
    assert r["ok"], r
    assert close(r["result"]["信道容量_bps"], 1e6 * math.log2(11), 1e-6), r["result"]


@case("蒙特卡洛 BPSK 6dB 与理论值吻合（偏差 <10%）")
def _t_comm_mc():
    r = tools.execute("comm_lib", {"action": "monte_carlo_ber", "scheme": "bpsk",
                                   "channel": "awgn", "ebn0_db": "6",
                                   "nbits": 400000})
    assert r["ok"], r
    row = r["result"]["结果"][0]
    sim, theo = row["误码率"], row["理论值"]
    assert close(theo, 2.4e-3, 0.05), f"6dB 理论值应≈ 2.4e-3，实际 {theo}"
    assert close(sim, theo, 0.10), f"sim={sim} theo={theo}"


@case("不支持的组合明确报错（rayleigh + 16qam 无精确式）")
def _t_comm_bad_combo():
    r = tools.execute("comm_lib", {"action": "theo_ber", "scheme": "16qam",
                                   "channel": "rayleigh", "ebn0_db": "10"})
    assert r["ok"] is False, f"应报错却返回: {r}"
    assert "rayleigh" in str(r["result"]), r


section("仿真执行")


@case("真实执行 Python 并回传标准输出")
def _t_run_python():
    r = tools.execute("run_python", {"code": "print('BER=', 0.5*0.02)", "timeout": 30})
    assert r["ok"] and "0.01" in r["result"]["标准输出"], r


@case("matplotlib 图表回收为 base64（不把图片喂回模型）")
def _t_run_python_fig():
    code = ("import matplotlib.pyplot as plt\n"
            "plt.plot([0,1],[0,1])\n"
            "plt.savefig('t.png')\n")
    r = tools.execute("run_python", {"code": code, "timeout": 90})
    assert r["ok"], r
    assert "生成图表" in r["result"], r["result"]
    assert "images" not in r["result"], "base64 图片不应回传给模型（token 爆炸）"


@case("代码语法错误 → 中文错误信息而非异常中断")
def _t_run_python_err():
    r = tools.execute("run_python", {"code": "def f(:\n  pass", "timeout": 30})
    assert r["ok"] is False and r["result"]["错误信息"], r


@case("模型误带 ```python 围栏仍能执行")
def _t_run_python_fence():
    r = tools.execute("run_python", {"code": "```python\nprint(1+1)\n```",
                                     "timeout": 30})
    assert r["ok"] and "2" in r["result"]["标准输出"], r


section("协议查询")


@case("命中本地知识库（香农信道容量）")
def _t_protocol():
    r = tools.execute("protocol_lookup", {"query": "香农 信道容量 公式", "top_k": 3})
    assert r["ok"], r
    assert r["result"]["来源"] == "本地知识库", r["result"]
    assert r["result"]["条目"] and r["result"]["条目"][0]["内容"], r["result"]


@case("top_k 越界自动夹到 1~5")
def _t_protocol_topk():
    r = tools.execute("protocol_lookup", {"query": " AWGN 信道模型", "top_k": 99})
    assert r["ok"] and len(r["result"].get("条目", [])) <= 5, r


section("硬件仿真")


@case("仿真器缺席时给出中文安装指引（不静默失败）")
def _t_verilog_graceful():
    from tools.hw_tools import _find_tool
    has_sim = bool(_find_tool("iverilog.exe") or _find_tool("iverilog"))
    r = tools.execute("run_verilog", {"verilog_code": "module m; endmodule",
                                      "testbench_code": ""})
    if not has_sim:
        assert r["ok"] is False and "未安装" in str(r["result"]), r
        print("        （本机未装 Icarus Verilog：已验证降级路径，装好后自动转真编译）")
        return
    assert r["ok"], r


_V_DESIGN = ("module cnt(input clk, input rst, output reg [2:0] q);\n"
             "  always @(posedge clk or posedge rst)\n"
             "    if (rst) q <= 3'b000;\n"
             "    else     q <= q + 1'b1;\n"
             "endmodule\n")
_V_TB_HEAD = ("`timescale 1ns/1ps\nmodule tb;\n  reg clk=0; \n"
              "  wire [2:0] q;\n"
              "  cnt u(.clk(clk), .rst(rst), .q(q));\n  always #5 clk = ~clk;\n")
_V_TB_TAIL = ('    repeat(8) begin @(posedge clk); #1 $display("Q=%0d", q); end\n'
              "    $finish;\n  end\nendmodule\n")
# 正确写法：复位在 initial 块内赋值，产 x→1 跳变，异步复位真的触发
_V_TB_OK = (_V_TB_HEAD + "  reg rst;\n  initial begin\n    rst = 1;\n    #3 rst = 0;\n"
            + _V_TB_TAIL)
# 错误写法：声明式初始化不产生跳变 → 寄存器一直 x（实测教训）
_V_TB_NOEDGE = (_V_TB_HEAD + "  reg rst = 1;\n  initial begin\n    #3 rst = 0;\n"
                + _V_TB_TAIL)


@case("真编译真仿真：带复位的 3 位计数器依序走 1…7 后模 8 回绕")
def _t_verilog_real():
    from tools.hw_tools import _find_tool
    if not (_find_tool("iverilog.exe") or _find_tool("iverilog")):
        print("        （本机未装 Icarus Verilog，跳过真实编译用例）")
        return
    r = tools.execute("run_verilog", {"verilog_code": _V_DESIGN,
                                      "testbench_code": _V_TB_OK, "timeout": 30})
    assert r["ok"], r
    seq = [int(v) for v in re.findall(r"Q=(\d)", r["result"]["仿真输出"])]
    assert seq == [1, 2, 3, 4, 5, 6, 7, 0], f"计数序列异常: {seq}"


@case("仿真输出含不定态 x 时，工具回报中文复位提示")
def _t_verilog_xdz_hint():
    from tools.hw_tools import _find_tool
    if not (_find_tool("iverilog.exe") or _find_tool("iverilog")):
        print("        （本机未装 Icarus Verilog，跳过不定态用例）")
        return
    r = tools.execute("run_verilog", {"verilog_code": _V_DESIGN,
                                      "testbench_code": _V_TB_NOEDGE, "timeout": 30})
    assert "Q=x" in r["result"]["仿真输出"], r["result"]
    assert "不定态" in r["result"].get("重要提示", ""), "未提示 x 态风险"


section("文献检索")


@case("检索层抛异常时降级为中文提示（不把异常抛给 Agent）")
def _t_lit_degrade():
    import io
    import contextlib
    import tools.lit_tools as lt
    orig = lt.search_literature
    lt.search_literature = lambda q, max_results=5: (_ for _ in ()).throw(
        OSError("模拟断网"))
    try:
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):     # 意外异常会在注册层打栈，测试里收起
            r = tools.execute("search_papers", {"query": "BPSK AWGN"})
        assert r["ok"] is False and "断网" in str(r["result"]), r
    finally:
        lt.search_literature = orig


@case("双源均无结果时返回空列表提示而非报错")
def _t_lit_empty():
    import tools.lit_tools as lt
    orig = lt.search_literature
    lt.search_literature = lambda q, max_results=5: []
    try:
        r = tools.execute("search_papers", {"query": "xxx"})
        assert r["ok"] and r["result"]["文献"] == [], r
        assert "换英文" in r["result"]["说明"], r
    finally:
        lt.search_literature = orig


@case("公网真检索（--net 才跑）：arXiv 命中且字段齐全")
def _t_lit_live():
    if "--net" not in sys.argv:
        print("        （未传 --net，跳过公网用例）")
        return
    r = tools.execute("search_papers", {"query": "LDPC channel coding 5G NR",
                                        "top_k": 2})
    assert r["ok"], r
    assert r["result"]["文献"], "公网未返回文献（可确认本机外网）"
    first = r["result"]["文献"][0]
    assert first["标题"] and first["链接"].startswith("http"), first


section("伪工具调用协议")


@case("解析标准标记的请求")
def _t_extract():
    text = ('答案如下。\n〔工具请求〕{"name": "comm_lib", '
            '"arguments": {"action": "shannon", "snr_db": 10}}〔/工具请求〕\n')
    calls = extract_tool_calls(text)
    assert len(calls) == 1 and calls[0]["name"] == "comm_lib", calls
    assert calls[0]["arguments"]["snr_db"] == 10, calls


@case("容忍缺失闭合标记 / 非法 JSON（至少抠出 name）")
def _t_extract_loose():
    calls = extract_tool_calls('我先算一下：〔工具请求〕{"name": "run_python", "arguments": {}}')
    assert len(calls) == 1 and calls[0]["name"] == "run_python", calls
    calls2 = extract_tool_calls('〔工具请求〕{name: "sympy_compute", arguments: {}}')
    assert calls2 and calls2[0]["name"] == "sympy_compute", calls2


@case("单轮上限 3 个请求；无标记返回空列表")
def _t_extract_limit():
    one = '〔工具请求〕{"name": "comm_lib", "arguments": {}}〔/工具请求〕\n'
    assert len(extract_tool_calls(one * 6)) == 3
    assert extract_tool_calls("纯文本回答，不需要工具。") == []


@case("arguments 非对象时降级为空参数（不崩溃）")
def _t_extract_badargs():
    calls = extract_tool_calls('〔工具请求〕{"name": "comm_lib", "arguments": "oops"}')
    assert calls == [{"name": "comm_lib", "arguments": {}}], calls


@case("定稿剥离全部工具标记与 JSON 残片")
def _t_strip():
    text = ('结论：C=B*log2(1+SNR)。\n'
            '〔工具请求〕{"name": "comm_lib", "arguments": {"action": "shannon"}}〔/工具请求〕\n'
            '以上。')
    out = _strip_marks(text)
    assert "工具请求" not in out and '"name"' not in out, out
    assert "C=B*log2(1+SNR)" in out and "以上" in out, out


@case("悬挂未闭合的 JSON 残行也被清除")
def _t_strip_hanging():
    text = '结论。\n〔工具请求〕{"name": "run_python",\n"arguments": {"code": "print(1)}'
    out = _strip_marks(text)
    assert '"name"' not in out and '"arguments"' not in out, out
    assert out.startswith("结论"), out


# ═══════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  本地工具层离线验收测试（无需 OpenTrek 平台）")
    print("=" * 60)
    passed, failed, cur = 0, [], None
    for sec, name, fn in _TESTS:
        if sec != cur:
            cur = sec
            print(f"\n▶ {sec}")
        try:
            fn()
            passed += 1
            print(f"  [PASS] {name}")
        except AssertionError as e:
            failed.append((name, str(e)))
            print(f"  [FAIL] {name} → {str(e)[:200]}")
        except Exception as e:
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  [ERROR] {name} → {type(e).__name__}: {e}")

    total = passed + len(failed)
    print(f"\n{'=' * 60}")
    print(f"  结果: {passed}/{total} 通过")
    for name, err in failed:
        print(f"    ✗ {name}: {err[:180]}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
