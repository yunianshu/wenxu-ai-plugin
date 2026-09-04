# 模块/插件地图

仓库顶层并非业务代码模块，而是「已托管插件 + 工具元数据」。下表列出当前托管对象。

| 托管对象 | 职责 | 位置 | 入口 | 依赖 |
| --- | --- | --- | --- | --- |
| `ai-project-steward`（v0.1.0，Wenxu） | 项目文档维护、Archify 图表、并行分支交付、发布产物 | `ai-project-steward/` | `ai-project-steward/.codex-plugin/plugin.json` 与 `ai-project-steward/.zcode-plugin/plugin.json`（平台清单）；`ai-project-steward/skills/*/SKILL.md`（能力） | 无外部运行时依赖；内部含 Python 3 脚本 |

## 其他顶层目录

- `.spec-workflow/` — spec-workflow 的规格/决策/审批存放区，非托管插件。
- `docs/ai/` — 本仓库的 AI 可读文档。

当前托管插件的中文速览：[`docs/ai/modules/ai-project-steward.md`](modules/ai-project-steward.md)。

新增托管插件时在此表增加一行，说明其职责、入口与依赖。仅当某插件存在难以从代码推断的边界、兼容约束或验证要求时，才在 `docs/ai/modules/` 下补充详情。
