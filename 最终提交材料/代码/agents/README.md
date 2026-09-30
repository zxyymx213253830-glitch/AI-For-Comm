# agents/ —— 智能体角色层（各 Agent 的本地子类）

每个文件对应平台上的一个智能体，在 `core/agent_node.py` 通用节点基础上叠加各自的领域行为：

- `math_agent.py` —— 数学推导（信息论公式、信道容量计算）
- `comm_agent.py` —— 3GPP 协议分析与信令流程
- `hw_agent.py` —— FPGA / Verilog 模块生成与时序分析
- `sim_agent.py` —— 通信仿真（含"代码真执行回灌"闭环 think_verified）
- `verify_agent.py` —— 结果校验（三级评级：通过 / 有条件通过 / 不通过）
- `lit_review_agent.py` —— 文献调研（公网 + 平台知识库双源检索）
- `report_agent.py` —— 报告统稿（固定字段 JSON 协议）

新建智能体时继承 AgentNode 并在此注册；`__init__.py` 统一导出。
