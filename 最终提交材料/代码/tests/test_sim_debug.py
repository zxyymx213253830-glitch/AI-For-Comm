# -*- coding: utf-8 -*-
"""
sim_agent 单节点验收测试 —— 阶段四验证脚本

验证目标（用户既定标准）：
  1. 非空回复：调用 sim_agent 得到完整四章节回复
     （【仿真方案】→【代码】→【理论对照】→【运行说明】）
  2. 代码可跑：从回复中抽出 Python 仿真源码，本地真实执行，
     并将仿真误码率与本地独立计算的理论 BER 对照。

运行方式：
  d:\\ai创新大赛\\.venv\\Scripts\\python.exe tests/test_sim_debug.py
"""
import os
import re
import math
import time
import subprocess
import sys
import textwrap
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_node import AgentNode
from core.config import AGENTS

# ── 日志 ──────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(OUT_DIR, f"test_sim_{TS}.log")
GEN_CODE = os.path.join(OUT_DIR, f"sim_gen_{TS}.py")


def slog(msg):
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass


# ── 1. 配置检查 ───────────────────────────────────
cfg = AGENTS.get("sim_agent", {})
if not cfg.get("agentCode") or not cfg.get("agentVersion"):
    slog("[ERROR] sim_agent 未配置，请先在 core/config.py 填写 agentCode/agentVersion")
    sys.exit(1)

slog("=" * 60)
slog(f"  sim_agent 验收测试  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
slog(f"  agentCode={cfg['agentCode']}")
slog(f"  agentVersion={cfg['agentVersion']}")
slog("=" * 60)

agent = AgentNode("sim_agent", cfg["agentCode"], cfg["agentVersion"])

# ── 2. 发起测试问题 ───────────────────────────────
QUESTION = ("仿真 BPSK 在 AWGN 下 Eb/N0=6dB 的误码率"
            + cfg.get("requireFullAnswer", ""))   # 要求终答一次写全四章节
slog(f"\n[1/4] 调用 sim_agent.think()\n      问题: {QUESTION}")

_start = time.time()
reply = agent.think(QUESTION)          # 内置空回复重试
_elapsed = int(time.time() - _start)

slog(f"      回复长度: {len(reply)} 字符，耗时 {_elapsed}s")

# ── 3. 回复质量校验 ───────────────────────────────
HEADINGS = ["【仿真方案】", "【代码】", "【理论对照】", "【运行说明】"]
idx_list = [reply.find(h) for h in HEADINGS]
ordered = all(i >= 0 for i in idx_list) and all(
    idx_list[i] < idx_list[i + 1] for i in range(len(idx_list) - 1)
)
has_numpy_code = bool(re.search(r"\bimport\s+numpy|import\s+math", reply))
fence_free = reply.count("```") == 0

checks = {
    "非空且足够长(>=400字符)": len(reply.strip()) >= 400,
    "四章节齐全且有序": ordered,
    "包含可执行代码要素(import)": has_numpy_code,
    "无Markdown围栏(平台管道规避)": fence_free,
}

slog("\n[2/4] 回复质量校验:")
all_pass = True
for name, ok in checks.items():
    slog(f"      [{'PASS' if ok else 'FAIL'}] {name}")
    all_pass = all_pass and ok

slog("\n" + "=" * 28 + " Reply Head " + "=" * 28)
slog(reply[:800])
slog("...(中略)...")
slog(reply[-400:])

if not all_pass:
    slog("\n[RESULT] FAIL —— 见上方校验明细")
    sys.exit(2)

# ── 4. 抽取代码并本地执行 ──────────────────────────
slog("\n[3/4] 抽取【代码】章节源码并本地执行:")
m = re.search(r"【代码】(.*?)【理论对照】", reply, re.S)
code_block = m.group(1) if m else ""

lines = []
for ln in code_block.splitlines():
    if ln.startswith("    "):
        lines.append(ln[4:])
    elif ln.strip() == "":
        lines.append("")
    elif not lines:          # 开头尚未进入代码区（如引导语），跳过
        continue
code_text = textwrap.dedent("\n".join(lines)).strip()

if "import" not in code_text:
    slog("      [WARN] 缩进抽取失败，尝试整段直接使用（去除明显中文叙述行）")
    code_text = "\n".join(
        ln for ln in map(str.strip, code_block.splitlines())
        if ln and not re.search(r"[\u4e00-\u9fff]", ln.split("#")[0])
    )

with open(GEN_CODE, "w", encoding="utf-8") as f:
    f.write(code_text + "\n")
slog(f"      已写入: {GEN_CODE}  ({len(code_text)} 字符)")

# 无头执行：Agg 后端使 plt.show() 不阻塞等待窗口关闭，图像仅落盘不弹窗
_env = dict(os.environ, MPLBACKEND="Agg")
try:
    run = subprocess.run(
        [sys.executable, GEN_CODE],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300, env=_env,
    )
except subprocess.TimeoutExpired:
    slog("      [FAIL] 生成代码执行超时(300s)，请检查是否含死循环/交互阻塞")
    sys.exit(3)
slog("      --- 执行 stdout ---")
for line in (run.stdout or "").strip().splitlines():
    slog("      " + line)
if run.returncode != 0:
    slog("      --- 执行 stderr(前600字) ---")
    slog("      " + (run.stderr or "")[:600])

# ── 5. 数值对照（与本地独立理论值比较）─────────────
EBN0_DB = 6.0
theory_ber = 0.5 * math.erfc(math.sqrt(10 ** (EBN0_DB / 10)))   # ≈2.39e-3
m_ber = re.search(r"仿真误码率[^0-9]*([0-9]+\.?[0-9eE+\-]*)", run.stdout or "")
sim_ber = float(m_ber.group(1)) if m_ber else None

slog(f"\n[4/4] 数值对照:")
slog(f"      本地独立理论 BER(Q函数) = {theory_ber:.4e}")
ratio_ok = False
if sim_ber is not None:
    ratio = sim_ber / theory_ber
    ratio_ok = 0.5 <= ratio <= 2.0     # 容许统计涨落一半以内到两倍以内
    slog(f"      仿真输出 BER           = {sim_ber:.4e}")
    slog(f"      仿真/理论比值           = {ratio:.3f}")
else:
    slog("      [FAIL] 未能从执行输出解析仿真误码率")

exec_ok = run.returncode == 0
final = exec_ok and ratio_ok
slog(f"      [{'PASS' if exec_ok else 'FAIL'}] 代码可无错运行")
slog(f"      [{'PASS' if ratio_ok else 'FAIL'}] 仿真结果符合理论区间[0.5x, 2x]")
slog(f"\n[RESULT] {'PASS —— 非空回复且仿真代码可跑、数值正确' if final else 'FAIL'}")
slog(f"[FILES]\n  日志: {os.path.abspath(LOG_FILE)}\n  生成代码: {GEN_CODE}")
sys.exit(0 if final else 3)
