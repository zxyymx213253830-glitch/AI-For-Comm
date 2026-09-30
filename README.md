# AI for Comm —— 通信领域多智能体科研协作系统

> AI 创新大赛参赛项目 · 本地编排 + 平台智能体混合架构
> 覆盖通信工程 / 数学理论（信息论）/ 硬件实践（FPGA）三个学科域

用户提出一个通信领域问题，系统内 7 个专业 Agent 像真实工程师团队一样分工协作、交叉验证，最终输出经过校验的结构化研究报告。

---

## 一、它能做什么

| 学科域 | 负责 Agent | 典型问题 |
|---|---|---|
| 通信工程 | `comm_agent` | "GTPv2 中 Create Session Request 有哪些必选 IE？" |
| 数学理论 | `math_agent` | "AWGN 信道 B=20MHz、SNR=30dB，求信道容量" |
| 硬件实践 | `hw_agent` | "写一个 8B/10B 编码器的 Verilog 模块并说明时序约束" |
| 仿真验证 | `sim_agent` | 生成蒙特卡洛仿真代码并与理论值对照（BER / 容量 / 星座图） |
| 文献调研 | `lit_review_agent` | arXiv / SemanticScholar + 平台知识库双源检索综述 |
| 结果校验 | `verify_agent` | 检查推导正确性并给出反馈 |
| 报告统稿 | `report_agent` | 把多智能体产出统稿成结构化报告（JSON → 高审美 HTML） |

七个 Agent 不是各自回答，而是走一条**六步科研流水线**：任务拆解 → 领域求解 → 交叉校验 → 仿真验证 → 文献佐证 → 统稿渲染，任何一步不通过都会回到上一轮重做。

## 二、架构：节点化 + 本地编排

每个 Agent 是一个独立节点，节点内部四件套：

```
┌────────────────────────────────┐
│           Agent 节点            │
│  执行手册 System Prompt         │  角色定义 · 领域知识 · 行为约束
│  工具集 Skills                  │  平台 API · 计算器 · RAG 检索
│  记忆存储 Memory                │  对话线程 · 历史消息 · 中间结果
│  消息接口 Message I/O           │  收件箱 · 发件 · 全部写日志
└────────────────────────────────┘
```

本地 `core/orchestrator.py` 负责编排调度、消息总线与日志，平台侧负责大模型推理与知识库检索——两边通过 `core/tool_driver.py` 的工具回环衔接。

## 三、快速开始

```bash
pip install -r requirements.txt

# 方式一：Web 界面（推荐，6 个中文页面：对话 / 流水线 / 报告库 / 监控 / 设置）
python web/app.py        # → http://localhost:7860

# 方式二：命令行直接跑一次双智能体协作研究
python main.py

# 方式三：容器
docker compose up
```

**首次运行前**需要填写 `config.json`（也可用 Web 设置页可视化编辑）：

```json
{
  "platform": {
    "baseUrl": "http://<platform-host>/sfm-agent-studio/sfm-api-gateway/gateway/agent/api",
    "appKey": "YOUR_APP_KEY"
  }
}
```

> 本仓库为公开存档版，`config.json` 与 `core/config_manager.py` 中的平台地址与 appKey 已替换为占位符，请填入你自己的平台地址与密钥。

可选工具脚本：

```bash
python build_kb_json.py   # 把 knowledge/ 打包成平台知识库导入 JSON
```

## 四、目录地图

| 目录 | 用途 |
|---|---|
| `core/` | 核心架构：智能体节点、六步流水线、协作编排、消息总线、工具回环、报告渲染、配置管理 |
| `agents/` | 7 个智能体的本地子类 |
| `tools/` | 本地工具集：SymPy 计算、通信算法库、代码沙箱、Verilog 仿真、文献检索、本地资料检索 |
| `prompts/` | 各智能体角色手册与硬约束（与平台在线提示词同源） |
| `web/` | Flask 服务：对话、科研流水线、报告库、监控、设置 |
| `knowledge/` | 本地知识库源文档：信息论 9 专题 + 仿真模板 6 类 + 权威文献 |
| `skills/` | 平台技能包源文件（仿真五步法 / 科研汇报统稿 / 高审美排版规范） |
| `evals/` | 38 题能力评测集与评测结果 |
| `tests/` | 各级测试脚本与一键测试批处理 |
| `outputs/` | 运行产物：`research_*.html` 研究报告、仿真图表、历史存档 |
| `docs/` | 方案书、实践手册、架构图、结课汇报书、排查记录、设计稿与 Logo |
| `最终提交材料/` | 参赛提交版：代码 + 项目文档 + 演示成果（含提交材料清单） |
| `中间材料/ 中间材料2/` | 建设期中间产物，仅作溯源 |
| `archive/` | 归档区：队友交付包原件、早期旧版程序 |

详细的逐目录说明见 [`目录结构说明.md`](目录结构说明.md)。

## 五、产物一览

- 项目方案书：[`docs/AI_for_Comm_项目方案书.pdf`](docs/AI_for_Comm_项目方案书.pdf)
- 实践手册：[`docs/AI_for_Comm_实践手册.pdf`](docs/AI_for_Comm_实践手册.pdf)
- 结课汇报：[`docs/项目结课汇报书.md`](docs/项目结课汇报书.md) / [`项目结课汇报.html`](项目结课汇报.html)
- 架构图：[`architecture.svg`](architecture.svg)

## 六、技术栈

Python 3 · Flask · SymPy · NumPy / Matplotlib · SSE 流式通信 · Docker · 平台侧 OpenTrek 智能体 + 知识库

---

**注**：本仓库只含项目资料与代码，不含 `.venv/` 虚拟环境与开发工具配置；原始调试脚本与临时截图未纳入。
