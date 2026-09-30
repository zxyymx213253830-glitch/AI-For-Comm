# tools/ —— 本地工具集（智能体的"手和脚"）

平台侧智能体无执行环境，真实计算全部由本目录落地，经 `core/tool_driver.py` 回环调用：

- `math_tools.py` —— SymPy 符号计算（推导验证、等式复核）
- `comm_tools.py` —— 通信算法库（调制、信噪比换算、理论误码率/容量公式）
- `sim_tools.py` —— Python 代码沙箱执行（临时目录隔离、无窗口绘图、图片回收）+ 代码提取（含裸代码回退）
- `hw_tools.py` —— Verilog 编译与仿真（本地 Verilator）
- `lit_tools.py` —— 文献检索（arXiv / Semantic Scholar 公网通道）
- `protocol_tools.py` —— 本地资料检索（knowledge/ 与 prompts/ 目录毫秒级离线查询）
- `registry.py` —— 工具注册表与中文标签（前端徽标、提示词目录均由它生成）
