# AI for Comm 评测集 v1.1

> 系统化评测 7 个 Agent 的领域能力与多 Agent 协作链路，为验收/答辩提供数据支撑。
> 创建：2026-08-30 · B 角色（李程宇） · 需求来源：周行远（架构师） · v1.1 新增 sim/report

---

## 一、目录结构

```
evals/
  tasks.json       题库（机读，评测脚本唯一数据源）
  results/         评测结果输出（HTML + CSV，按时间戳命名）
  README.md        本文档
tests/
  run_eval.py      评测执行器
```

## 二、快速开始

```bash
# 跑全部（约 30 题，依赖校园网连 OpenTrek，预计 15~40 分钟）
python tests/run_eval.py

# 只跑某个 Agent
python tests/run_eval.py --agent math_agent

# 只跑协作闭环（4 条链路）
python tests/run_eval.py --mode collab

# 调试：只跑 3 题
python tests/run_eval.py --limit 3

# 跳过某条会卡死的链路（如 hw→verify）
python tests/run_eval.py --mode collab --exclude collab-03
```

> ⚠️ 注意：运行 python 请用 venv 解释器
> `C:\Users\Lenovo\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
> （numpy/matplotlib/gradio/structlog 已装齐）。

结果输出到 `evals/results/eval_时间戳.html`（可浏览器打开）和 `.csv`。

## 三、题目概览

### 单题直答（32 道）

| ID | Agent | 难度 | 考点 | 判定 |
|---|---|---|---|---|
| math-01 | math | S | AWGN 香农容量（B=20MHz, SNR=30dB） | 待人工 |
| math-02 | math | S | BSC 容量（p=0.1） | 待人工 |
| math-03 | math | M | 容量倍数对比（10dB vs 0dB） | 待人工 |
| math-04 | math | M | 无限带宽容量极限 | 待人工 |
| math-05 | math | M | 16-QAM 每符号容量上界 | 待人工 |
| math-06 | math | H | 香农极限超越方程 | 待人工 |
| comm-01 | comm | S | GTPv2 Create Session 必选 IE（TS 29.274） | 待人工 |
| comm-02 | comm | S | 5G NR SIB1 内容（TS 38.331） | 待人工 |
| comm-03 | comm | M | LTE RRC 连接建立流程（TS 36.331） | 待人工 |
| comm-04 | comm | M | NGAP UE 上下文建立（TS 38.413） | 待人工 |
| comm-05 | comm | M | Xn 切换 vs N2 切换 | 待人工 |
| comm-06 | comm | H | GTPv2-C vs GTPv1-U 分离设计 | 待人工 |
| hw-01 | hw | S | 同步 FIFO（深 16 宽 8） | 待人工 |
| hw-02 | hw | S | 4 位计数器 + 异步复位 | 待人工 |
| hw-03 | hw | M | FIFO 空满判断与 N+1 指针 | 待人工 |
| hw-04 | hw | M | 亚稳态避免三方法 | 待人工 |
| hw-05 | hw | M | 三段式状态机（1011 检测） | 待人工 |
| hw-06 | hw | H | 异步 FIFO 格雷码同步 | 待人工 |
| lit-01 | lit | S | LDPC 在 5G NR 的应用 | 待人工 |
| lit-02 | lit | M | Polar 码在 eMBB 的应用 | 待人工 |
| lit-03 | lit | M | URLLC 关键技术 | 待人工 |
| lit-04 | lit | M | 大规模 MIMO 信道估计 | 待人工 |
| lit-05 | lit | H | 语义通信研究进展 | 待人工 |
| verify-01 | verify | S | 校验正确推导 → 应【通过】 | **自动** |
| verify-02 | verify | S | 校验公式系数错误 → 应【不通过】 | **自动** |
| verify-03 | verify | M | 校验 dB 未换算 → 应【不通过】 | **自动** |
| verify-04 | verify | M | 校验双 always 多驱动 → 应【不通过】 | **自动** |
| verify-05 | verify | H | 综合交叉校验 → 应【通过】 | **自动** |
| sim-01 | sim | S | AWGN BPSK BER 蒙特卡洛仿真（五步法真执行） | 待人工 |
| sim-02 | sim | M | BPSK vs QPSK BER 对比仿真 | 待人工 |
| report-01 | report | S | 单源产出 → 固定结构科研汇报 | 待人工 |
| report-02 | report | M | 双源聚合汇报（math + sim） | 待人工 |

### 协作闭环（4 道）

| ID | 链路 | 考点 |
|---|---|---|
| collab-01 | math → verify | 推导正确 → 判通过（仅格式建议不判不通过） |
| collab-02 | comm → verify | 协议答案 + 枚举细节不误判 |
| collab-03 | hw → verify | 完整代码 + 事实错误检测 |
| collab-04 | lit_review → verify | 双源引用 + 引用完整性校验 |

## 四、评分口径

| 模式 | 判定方式 |
|---|---|
| direct（单题直答） | **待人工评分**——脚本记录输出+耗时，HTML 报告里人工看答案打分（对照 tasks.json 的 answer_points） |
| judge（verify 判定） | **自动**——比对 verify 输出中的【通过】/【不通过】与题目预期 |
| collab（协作闭环） | **自动**——取 dual_verify 的 passed |

人工评分建议维度（对应 tasks.json 的 criteria）：
- `correctness` 核心答案正确性（0-3：错/部分对/对/对且完整）
- `citation` 是否引用来源（规范编号/章节/知识库文档）
- `structure` 是否按约定结构输出（推导步骤/完整代码/综述章节）
- `time` 耗时是否在阈值内（默认 300s）

## 五、如何扩展（给曹阳/周行远）

1. **加题**：编辑 `evals/tasks.json`，复制一行模板改内容：
   ```json
   {"id": "math-07", "agent": "math_agent", "level": "M",
    "question": "题目...", "answer_points": ["参考答案要点..."],
    "criteria": ["correctness", "citation", "structure", "time"], "timeout": 300}
   ```
2. **judge 题**（verify 用）：`"mode": "judge"`，并在 answer_points 里写清 `应判【通过】/【不通过】`（脚本靠它定预期）。
3. **协作题**：加到 `collab` 数组：`{"id": "collab-05", "solver": "hw_agent", "question": "...", "expect": "..."}`。
4. id 保持唯一、建议带 Agent 前缀（math-xx / comm-xx / hw-xx / lit-xx / verify-xx / collab-xx）。

## 六、注意事项

- 评测依赖**校园网连 OpenTrek**（<platform-host>）；网络断会整批失败。
- lit_review 题目会触发公网检索（arXiv+S2），S2 无 Key 限流时单题可能多等 ~30s。
- judge 题 verify 用的是新版判定规则（只有事实错误判不通过），verify-01/05 就是为此设计的回归题。
- 全量跑一次较久（30+ 题 × 平台调用），答辩前建议先 `--agent` 分科跑并人工核对 direct 答案。
