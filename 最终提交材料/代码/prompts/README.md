# prompts/ —— AI 提示词与约束文件

- `*_system.md` —— 各智能体的角色手册（系统提示词），与平台在线版本保持同步：
  - `math_system.md` —— 含"推导三步法"自查规范（2026-09-02 交付包并入）
  - `verify_system.md` —— 含"通用四项清单"（量纲/单调性/特殊值代入/文献对照）+ 三级评级
  - `report_system.md` —— 主用版：固定字段 JSON 统稿协议（流水线依赖，勿改结构）
  - `report_presentation_system.md` —— 备用版：七章节文本汇报稿规范（交付包并入，未上线）
  - `sim_system.md` / `comm_system.md` / `hw_system.md` / `lit_review_system.md` —— 其余角色手册
- `constraints_*.md` —— 调用时追加的硬约束（输出格式、禁止事项、知识库引用要求）

修改本目录后需通过配置接口同步到平台在线版本才会对智能体生效（有现成脚本配方）。
