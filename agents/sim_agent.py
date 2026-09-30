# -*- coding: utf-8 -*-
"""
仿真 Agent —— 通信数值仿真（蒙特卡洛 BER / 容量曲线）

继承 core.agent_node.AgentNode，封装 sim_agent 的 OpenTrek 凭证。

⚠️ 需要先在 OpenTrek 控制台创建 sim_agent：
  1. 控制台 → 新建 Agent
  2. 名称：sim_agent
  3. System Prompt：prompts/sim_system.md 全文
  4. 发布后拿到 agentCode + agentVersion
  5. 填入 core/config.py 的 AGENTS['sim_agent']

核心能力：仿真五步法闭环 —— 平台出代码 → 本地 venv 真实执行（numpy/matplotlib）
→ 执行结果回灌平台 → 理论曲线对比出结论。禁止只交"没跑过的代码"。
"""
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from core.agent_node import AgentNode
from core.config import AGENTS
from core.logger import log

# 本地执行器：跟随当前解释器（由 venv 启动即 venv），不再硬编码队友机器路径
SIM_PYTHON = sys.executable
SIM_OUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "sim"


class SimAgent(AgentNode):
    """仿真 Agent —— 通信数值仿真"""

    DOMAIN = "通信数值仿真"

    def __init__(self, bus=None):
        cfg = AGENTS.get("sim_agent", {})
        if not cfg.get("agentCode") or not cfg.get("agentVersion"):
            raise ValueError(
                "sim_agent 未配置 agentCode/agentVersion。\n"
                "请先在 OpenTrek 控制台创建 sim_agent"
                "（System Prompt 用 prompts/sim_system.md），\n"
                "然后将 agentCode + agentVersion 填入 core/config.py 的 AGENTS['sim_agent']。"
            )
        super().__init__(
            name="sim_agent",
            agent_code=cfg["agentCode"],
            agent_version=cfg["agentVersion"],
            kb_ids=cfg.get("kbIds", []),
            bus=bus,
        )

    # ── 领域便捷方法 ─────────────────────────────────

    def simulate_ber(self, modulation: str = "BPSK",
                     ebno_min_db: float = 0.0, ebno_max_db: float = 10.0,
                     num_symbols: int = 100_000) -> str:
        """标准题目：AWGN 信道 BER 蒙特卡洛仿真"""
        task = (
            f"仿真题目：AWGN 信道 {modulation} 误码率曲线\n"
            f"参数：Eb/N0 从 {ebno_min_db} dB 到 {ebno_max_db} dB，步进 1 dB，"
            f"蒙特卡洛符号数 {num_symbols}，随机种子 42\n"
            f"要求：按仿真五步法输出可运行的 Python 代码（numpy 实现），"
            f"仿真曲线与理论公式同图对比（semilogy），输出 PNG 与关键点对照表。"
        )
        return self.think(task)

    def simulate_capacity(self, snr_db_range: tuple = (0, 30)) -> str:
        """标准题目：AWGN 信道容量随 SNR 变化曲线仿真"""
        task = (
            f"仿真题目：AWGN 信道容量 C = B·log₂(1+S/N) 随 SNR 变化曲线\n"
            f"参数：SNR 从 {snr_db_range[0]} dB 到 {snr_db_range[1]} dB，带宽 B = 1 MHz\n"
            f"要求：按仿真五步法输出可运行的 Python 代码（numpy 实现），"
            f"数值结果与香农公式直接计算对比，输出 PNG 曲线。"
        )
        return self.think(task)

    # ── 五步法闭环：think → 本地真执行 → 回灌对比 ────

    def think_verified(self, task: str, timeout: int = 180) -> dict:
        """完整闭环：平台出代码 → 本地真执行 → 结果回灌 → 理论对比出图

        Returns:
            dict: {final_text, code, exec, pngs, note}
        """
        # 第一步：平台 Agent 按五步法产出（含可运行代码）
        raw = self.think(task)

        code = self._extract_python(raw)
        if not code:
            return {
                "final_text": raw,
                "code": None,
                "exec": None,
                "pngs": [],
                "note": "未提取到 ```python 代码块，无法真执行",
            }

        # 第二~三步：本地真实执行
        exec_result = self.execute_code(code, timeout=timeout)

        # 第四~五步：回灌真实结果，让 Agent 完成理论对比与结论
        feedback_task = (
            f"{task}\n\n---\n你的仿真代码已在本地真实执行，结果如下：\n"
            f"[stdout]\n{exec_result['stdout'][-3000:]}\n"
            f"[stderr]\n{exec_result['stderr'][-1000:]}\n"
            f"退出码：{exec_result['returncode']}\n"
            f"输出图片：{exec_result['pngs']}\n\n"
            f"请按五步法输出最终版：【运行结果】关键点对照表、"
            f"【对比结论】偏差分析、【图】PNG 路径。"
            f"若执行失败，请修正代码后重新给出可运行版本。"
        )
        final = self.think(feedback_task)
        return {
            "final_text": final,
            "code": code,
            "exec": exec_result,
            "pngs": exec_result["pngs"],
            "note": "",
        }

    # ── 本地执行器 ──────────────────────────────────

    @staticmethod
    def _extract_python(text: str):
        """提取可执行 Python 代码：
        1) 优先匹配 ```python ... ``` 围栏代码块
        2) 回退：从 import/from 行起，截到下一个【章节】标记前（平台常输出 4 空格缩进的裸代码）
        """
        m = re.search(r"```python\s*\n(.*?)```", text, re.S)
        if m:
            return m.group(1).strip()
        # 裸代码回退：找第一行 import/from 语句
        lines = text.splitlines()
        start = None
        for i, ln in enumerate(lines):
            if re.match(r"^\s*(import|from)\s+\w+", ln):
                start = i
                break
        if start is None:
            return None
        code_lines = []
        for ln in lines[start:]:
            if re.match(r"^【", ln.strip()):  # 章节标记结束
                break
            code_lines.append(ln)
        # 先统一去公共缩进（首行/其余行缩进不一致时直接 strip 会 IndentationError）
        code = textwrap.dedent("\n".join(code_lines)).strip()
        return code or None

    def execute_code(self, code: str, timeout: int = 180) -> dict:
        """在 venv（numpy/matplotlib）中真实执行仿真代码"""
        SIM_OUT_DIR.mkdir(parents=True, exist_ok=True)
        script_path = SIM_OUT_DIR / "sim_run.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            env = os.environ.copy()
            env["MPLBACKEND"] = "Agg"  # 防 matplotlib 窗口阻塞（已知教训）
            proc = subprocess.run(
                [SIM_PYTHON, str(script_path)],
                cwd=str(SIM_OUT_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
            )
            result = {
                "returncode": proc.returncode,
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
            }
        except subprocess.TimeoutExpired:
            result = {
                "returncode": -1,
                "stdout": "",
                "stderr": f"执行超时（>{timeout}s）",
            }
        except Exception as e:  # noqa: BLE001
            result = {"returncode": -1, "stdout": "", "stderr": str(e)}

        pngs = [p.name for p in SIM_OUT_DIR.glob("*.png")]
        result["pngs"] = pngs
        result["script"] = str(script_path)
        log.info("sim.execute", returncode=result["returncode"],
                 pngs=pngs, script=str(script_path))
        return result
