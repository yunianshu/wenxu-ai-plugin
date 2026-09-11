# 仓库规则（AGENTS.md）

## 项目语境

本仓库用于托管 AI 编程助手插件（skills / scripts / hooks + 平台清单）。当前托管一个插件：`ai-project-steward/`。

相关文档：

- 项目概述：`docs/ai/project-overview.md`
- 模块/插件地图：`docs/ai/module-map.md`
- 业务规则：`docs/ai/business-rules.md`
- 开发指南：`docs/ai/development-guide.md`
- 验证：`docs/ai/verification.md`
- 已知问题：`docs/ai/known-issues.md`
- 变更日志：`CHANGELOG.md`

技术栈：仓库本身无应用代码与构建链；`ai-project-steward/` 内为 Python 3 脚本与 Markdown skills。

## 改动前必读

阅读本文件与任务相关文档，先确认根因与受影响范围再修改。保持既有目录语义，不做无关重构。

## 约束

- `ai-project-steward/` 是**已托管的第三方插件内容**：本仓库文档只描述它，除非任务针对该插件本身，否则不要改动其内部，也不要把它当作自有业务模块重构。
- `.spec-workflow/` 是 spec-workflow 元数据工作区，勿随意改动。
- 不编造业务规则。依据本次用户要求与仓库证据修正陈旧事实；只有尚不能判定且影响结果的业务取舍才询问，并继续独立工作。
- 不改变插件公共清单（`ai-project-steward/.codex-plugin/`、`ai-project-steward/.zcode-plugin/` 等）而不评估影响。
- 保留任务范围外的用户改动。

## 完成标准（Definition of done）

- 先运行最小相关验证；未运行的部分要明确报告。
- 代码改动后评估文档影响。
- 行为、接口、数据结构、命令、模块边界或持久约束变化时，就地更新相关权威文档；否则简述无影响的原因，不要求固定措辞。普通修复不自动初始化完整文档、图表或发布脚本。
- 已明确要求优化/修复时，必要多文件修改、隔离测试和本地插件更新直接执行，不再审批同一计划；未经授权不提交/推送，不修改宿主钩子信任记录。
