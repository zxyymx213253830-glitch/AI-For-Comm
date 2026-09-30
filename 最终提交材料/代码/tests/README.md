# tests/ —— 测试与工具脚本

- `run_eval.py` / `merge_eval_results.py` / `make_score_sheet.py` —— 评测执行器、结果合并、评分表生成（配合 evals/ 题库）
- `test_pipeline.py` / `test_simple.py` / `test_tools.py` / `test_report_agent.py` —— 流水线与工具层测试
- `test_sim_templates.py` / `test_sim_debug.py` / `test_sim_templates.py` —— 仿真模板验证
- `test_delivery_merge.py` —— 交付包整合离线自检（语法编译 + 导入 + 代码提取四形态单测 + 题库完整性）
- `test_hw_debug.py`、`probe_agents.py` 等 —— 专项调试脚本
- `run_test.bat` —— 一键双智能体协作测试（在资源管理器双击运行）
- `*_output*.txt`、`hw_debug_output*.txt` —— 历次调试输出留档
