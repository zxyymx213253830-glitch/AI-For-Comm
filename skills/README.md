# skills/ —— 平台技能（Skills Hub）源文件

每个子目录是一个技能包（内含标准格式 SKILL.md），已上传至 OpenTrek 平台 Skills Hub：

- `sim-five-step-method/` —— 仿真五步法：方案→代码→真执行→理论对比→出图 强制闭环，
  搭载于仿真 Agent 的工作流（方法论注入其提示词与本地执行回灌管线）
- `research-report-compile/` —— 科研汇报统稿：收集→组织→成文→复核，七章节固定结构，
  搭载于报告 Agent 的文本汇报场景
- `research-report-aesthetic/` —— 科研报告高审美排版规范（靛蓝瓷主题），
  搭载于报告渲染引擎（本地 HTML 排版即按此规范实现）

上传平台的注意事项：文件上传入口实际要求 .zip 包（包根目录放 SKILL.md），直传 .md 会安全扫描失败。
