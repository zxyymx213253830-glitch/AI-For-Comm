# -*- coding: utf-8 -*-
"""交付包整合自检（离线，不调平台）：语法编译 + 模块导入 + 裸代码回退提取单测"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

files = [
    ROOT / "agents" / "sim_agent.py",
    ROOT / "agents" / "report_agent.py",
    ROOT / "agents" / "math_agent.py",
    ROOT / "agents" / "comm_agent.py",
    ROOT / "agents" / "hw_agent.py",
    ROOT / "agents" / "verify_agent.py",
    ROOT / "tests" / "run_eval.py",
    ROOT / "tests" / "merge_eval_results.py",
    ROOT / "tests" / "make_score_sheet.py",
    ROOT / "tools" / "sim_tools.py",
]
for f in files:
    py_compile.compile(str(f), doraise=True)
print("[1] 语法编译通过:", len(files), "个文件")

import agents.sim_agent, agents.report_agent, agents.math_agent
import agents.comm_agent, agents.hw_agent, agents.verify_agent
print("[2] 六个 Agent 子类导入通过")
assert agents.sim_agent.SIM_PYTHON == sys.executable, "SIM_PYTHON 应跟随本机解释器"
print("[2.1] SIM_PYTHON =", agents.sim_agent.SIM_PYTHON)

from tools.sim_tools import extract_python_code

# 形态1：围栏代码（原有能力不回归）
t1 = extract_python_code("说明\n```python\nimport numpy as np\nprint(1)\n```\n")
assert t1 and "import numpy" in t1[0], "围栏提取失败"

# 形态2：队友实测形态——4空格缩进裸代码、无围栏、无【代码】标记，后面跟【运行结果】章节
t2_raw = (
    "好的，仿真代码如下：\n"
    "    import numpy as np\n"
    "    import matplotlib.pyplot as plt\n"
    "    def ber(x):\n"
    "        return x * 2\n"
    "    print(ber(3))\n"
    "【运行结果】\n"
    "退出码 0\n"
)
t2 = extract_python_code(t2_raw)
assert t2 and t2[0].startswith("import numpy"), "裸代码回退提取失败"
assert "def ber" in t2[0] and "【运行结果】" not in t2[0], "截断边界错误"
compile(t2[0], "<t2>", "exec")  # 缩进统一后可编译

# 形态3：首行无缩进、后续 4 空格缩进（dedent 场景）
t3 = extract_python_code(
    "    import numpy as np\n    a = np.array([1, 2])\n【结论】\n略\n")
assert t3 and t3[0].startswith("import numpy"), "dedent 场景失败"
compile(t3[0], "<t3>", "exec")

# 形态4：无代码时不误提取
assert extract_python_code("这里没有任何代码") == [], "误提取"
print("[3] extract_python_code 四形态单测通过")

# 评测题库完整性
import json
data = json.loads((ROOT / "evals" / "tasks.json").read_text(encoding="utf-8"))
n_tasks, n_collab = len(data.get("tasks", [])), len(data.get("collab", []))
assert n_tasks + n_collab >= 30, "题数异常"
print(f"[4] evals/tasks.json 加载通过：{n_tasks} 题 + {n_collab} 协作 = {n_tasks + n_collab} 题")
print("ALL-SELFTEST-PASS")
