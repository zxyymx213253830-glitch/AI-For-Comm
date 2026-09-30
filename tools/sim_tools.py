# -*- coding: utf-8 -*-
"""
仿真执行工具 —— 真实运行 Python 仿真代码并回收结果与图表

核心执行函数 execute_python_code 从 core/pipeline.py 的 _execute_sim_code
抽出，工具层与流水线共用同一套安全执行逻辑：
- 独立临时目录运行，注入中文字体与 Agg 后端设置（防窗口阻塞，已知教训）
- 超时强杀（默认 90 秒，上限 180 秒）
- savefig 自动重定向到临时目录，PNG 以 base64 回收
"""
import base64
import glob
import os
import re
import subprocess
import sys
import tempfile
import textwrap

from tools.registry import tool


def execute_python_code(code: str, timeout: int = 90):
    """在临时目录执行 Python 代码。

    Returns:
        {"ok": bool, "stdout": str, "stderr": str, "images": [base64...]}
    """
    timeout = max(10, min(int(timeout or 90), 180))
    with tempfile.TemporaryDirectory(prefix="tool_sim_") as tmpdir:
        script_path = os.path.join(tmpdir, "script.py")

        preamble = (
            "import matplotlib\n"
            "matplotlib.use('Agg')\n"
            "import matplotlib.pyplot as plt\n"
            "plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']\n"
            "plt.rcParams['axes.unicode_minus'] = False\n"
            f"_output_dir = r'{tmpdir}'\n"
            "import os\n"
        )
        # savefig 相对路径重定向到临时目录
        code_fixed = re.sub(
            r"savefig\(['\"]([^'\"]+)['\"]",
            r"savefig(os.path.join(_output_dir, r'\1')",
            code)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(preamble + code_fixed)

        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, timeout=timeout,
                env=env, cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "images": [],
                    "stderr": f"执行超时（{timeout}秒），请减小仿真规模（如减少比特数或信噪点）"}
        except Exception as e:
            return {"ok": False, "stdout": "", "images": [], "stderr": str(e)}

        images = []
        for png in sorted(glob.glob(os.path.join(tmpdir, "*.png"))):
            with open(png, "rb") as f:
                images.append(base64.b64encode(f.read()).decode("ascii"))

        stdout = (proc.stdout or "").strip()
        return {
            "ok": proc.returncode == 0,
            "stdout": stdout[-3000:],           # 截断防爆 token
            "stderr": (proc.stderr or "").strip()[-1500:],
            "images": images,
            "图表数": len(images),
        }


@tool(
    "run_python",
    "真实执行一段 Python 仿真/数值计算代码，返回标准输出与生成的图表数量（代码必须自行 print 关键数值结果）",
    {"code": "完整可运行的 Python 代码，多行用 \\n 分隔；出图请 plt.savefig('xxx.png')，不要 plt.show()",
     "timeout": "超时秒数，30~180，默认 90"},
)
def run_python(code: str, timeout: int = 90):
    code = str(code or "").strip()
    if not code:
        return {"ok": False, "result": "代码为空"}
    # 容错：模型偶尔无视禁围栏规则带 ```python 标记，剥掉
    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", code, flags=re.M)
    out = execute_python_code(code, timeout=timeout)
    # 图表 base64 体积大，不回传给模型，只报数量与文件名（报告嵌入走流水线原有通道）
    result = {
        "执行成功": out["ok"],
        "标准输出": out["stdout"],
    }
    if out["images"]:
        result["生成图表"] = f"{out['图表数']} 张 PNG（已回收进报告，无需在回答中重复）"
    if not out["ok"]:
        result["错误信息"] = out["stderr"]
    return {"ok": out["ok"], "result": result}


def extract_python_code(answer: str) -> list:
    """从 Agent 回答中提取 Python 代码块（供流水线复用）。

    支持四种形态：```python 围栏、无语言围栏、【代码】章节 4 空格缩进纯文本
    （平台禁围栏后 sim_agent 的常见输出形态）、import 行起手的裸代码回退
    （2026-09-02 交付包实测教训：平台输出 4 空格缩进裸代码无围栏无章节标记）。
    """
    blocks = re.findall(r"```python\s*\n(.*?)```", answer, re.S)
    if not blocks:
        blocks = re.findall(r"```\s*\n(.*?)```", answer, re.S)
    if not blocks:
        m_section = re.search(
            r"【代码】\s*\n((?:[ \t]*\n|    .+\n?)+)", answer, re.M)
        if m_section:
            dedented = []
            for ln in m_section.group(1).splitlines():
                if ln.startswith("    "):
                    dedented.append(ln[4:])
                elif ln.strip() == "":
                    dedented.append("")
            if dedented:
                blocks = ["\n".join(dedented)]
    if not blocks:
        # 裸代码回退：从第一行 import/from 起，截到下一个【章节】标记前；
        # 用 textwrap.dedent 统一缩进（首行与其余行缩进不一致时直接 strip 会 IndentationError）
        lines = answer.splitlines()
        start = next((i for i, ln in enumerate(lines)
                      if re.match(r"^\s*(import|from)\s+\w+", ln)), None)
        if start is not None:
            code_lines = []
            for ln in lines[start:]:
                if re.match(r"^【", ln.strip()):
                    break
                code_lines.append(ln)
            code = textwrap.dedent("\n".join(code_lines)).strip()
            if code:
                blocks = [code]
    return blocks
