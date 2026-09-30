# -*- coding: utf-8 -*-
"""
硬件仿真工具 —— 真实编译并运行 Verilog 代码（Icarus Verilog / Verilator）

补上 hw_agent 缺失的 RTL 验证闭环：Agent 生成 Verilog 后不再"纸上谈兵"，
而是本地真编译真仿真，拿回真实仿真输出。

仿真器探测顺序：iverilog+vvp（轻量，Windows 友好）→ verilator。
未安装时返回中文安装指引，绝不静默失败。
"""
import glob
import os
import re
import shutil
import subprocess
import tempfile

from tools.registry import tool

# 常见安装位置兜底（winget/msys2 装完可能不在当前会话 PATH 里）
_EXTRA_DIRS = [
    os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages"),
    r"C:\msys64\usr\bin", r"C:\msys64\mingw64\bin",
    r"C:\iverilog\bin", r"C:\Program Files\Icarus Verilog\bin",
]


def _find_tool(exe: str):
    p = shutil.which(exe)
    if p:
        return p
    for d in _EXTRA_DIRS:
        if not os.path.isdir(d):
            continue
        hits = glob.glob(os.path.join(d, "**", exe), recursive=True)
        if hits:
            return hits[0]
    return None


@tool(
    "run_verilog",
    "真实编译并仿真 Verilog 代码（Icarus Verilog），返回仿真器实际输出。用于验证模块功能、测试激励结果",
    {"verilog_code": "设计代码（纯 Verilog 文本，多行用 \\n 分隔，不要包含测试激励）",
     "testbench_code": "测试激励代码（含 initial 块和 $display/$finish，可选但强烈建议）",
     "timeout": "仿真超时秒数，10~120，默认 60"},
)
def run_verilog(verilog_code: str, testbench_code: str = "", timeout: int = 60):
    iverilog = _find_tool("iverilog.exe") or _find_tool("iverilog")
    vvp = _find_tool("vvp.exe") or _find_tool("vvp")
    if not iverilog or not vvp:
        return {"ok": False, "result": {
            "错误": "本机未安装 Icarus Verilog 仿真器",
            "安装方法": "管理员 PowerShell 执行: winget install Icarus_Verilog 或从 icarus.com 下载 Windows 版",
        }}

    timeout = max(10, min(int(timeout or 60), 120))
    design = str(verilog_code or "").strip()
    tb = str(testbench_code or "").strip()
    if not design:
        return {"ok": False, "result": "设计代码为空"}

    with tempfile.TemporaryDirectory(prefix="hw_sim_") as tmpdir:
        files = [os.path.join(tmpdir, "design.v")]
        with open(files[0], "w", encoding="utf-8") as f:
            f.write(design)
        if tb:
            tb_path = os.path.join(tmpdir, "tb.v")
            with open(tb_path, "w", encoding="utf-8") as f:
                f.write(tb)
            files.append(tb_path)

        exe_path = os.path.join(tmpdir, "sim.vvp")
        # 编译
        cp = subprocess.run([iverilog, "-g2012", "-o", exe_path] + files,
                            capture_output=True, text=True, timeout=60)
        if cp.returncode != 0:
            return {"ok": False, "result": {
                "编译通过": False,
                "编译错误": (cp.stderr or cp.stdout).strip()[:2000],
                "说明": "Verilog 编译失败，请修正语法后重新申请",
            }}
        # 仿真
        try:
            sp = subprocess.run([vvp, exe_path], capture_output=True,
                                text=True, timeout=timeout, cwd=tmpdir)
        except subprocess.TimeoutExpired:
            return {"ok": False, "result": {
                "编译通过": True,
                "仿真输出": "",
                "错误": f"仿真运行超时（{timeout}s），检查 testbench 是否缺少 $finish/结束条件",
            }}
        return {"ok": sp.returncode == 0, "result": _with_xdz_hint({
            "编译通过": True,
            "仿真输出": (sp.stdout or "").strip()[-3000:],
            "警告或错误": (sp.stderr or "").strip()[:1000],
            "激励文件": "有 testbench" if tb else "无 testbench（仅编译+默认运行）",
        })}


# 不定态特征：$display 打出的 x/z（如 "Q=x"、"data=xxxx"、"bin=01xz"）
_XDZ_RE = re.compile(r"[=:(,\s][xXzZ]{1,8}\b")


def _with_xdz_hint(result: dict) -> dict:
    """仿真输出含不定态时附中文定位提示。

    实测教训：testbench 里写 `reg rst = 1;` 这类声明式初始化不产生 x→1 跳变，
    异步复位 always 块永不触发，寄存器一直保持 x；必须写成 initial 块内赋值。
    """
    out = result.get("仿真输出", "")
    if out and _XDZ_RE.search(out):
        result["重要提示"] = (
            "仿真结果出现不定态 x/z，通常是寄存器没有真正复位。"
            "请检查 testbench：① 复位信号要在 initial 块内赋值（rst = 1; #3 rst = 0;），"
            "不要写 `reg rst = 1;`——声明式初始化不产生 x→1 跳变，异步复位不会触发；"
            "② 或给设计模块加同步复位/寄存器初始化。"
        )
    return result
