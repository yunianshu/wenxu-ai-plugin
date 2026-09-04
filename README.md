# wenxu-ai-plugin

AI 编程助手插件管理项目：集中托管、组织面向 AI 编程助手的插件（skills / scripts / hooks 及平台清单）。

## 项目概述

本项目用于管理 AI 编程助手插件。**当前托管 1 个插件：**

- [`ai-project-steward/`](ai-project-steward/) — 插件 `ai-project-steward`（作者 Wenxu，版本 0.1.0）。提供项目文档维护、Archify 图表、并行分支交付、发布产物等能力，面向 Codex 与 Zcode 等宿主环境（含 `.codex-plugin/`、`.zcode-plugin/` 平台清单）。

仓库还包含 `.spec-workflow/`（spec-workflow 工作流的规格/决策/审批存放区）。

> 状态：仓库处于早期阶段 —— 尚无业务代码与构建链；已建立初始提交并托管于 GitHub（<https://github.com/yunianshu/wenxu-ai-plugin>）。插件托管之外的用途与演进方向待确认。

## 目录结构

- `ai-project-steward/` — 已托管的插件内容（第三方插件，默认不应改动其内部）
- `.spec-workflow/` — spec-workflow 元数据工作区
- `docs/ai/` — AI 可读项目文档（入口见[模块/插件地图](docs/ai/module-map.md)）
- `AGENTS.md` — 给改动仓库内容的 agent / 贡献者的规则

## 快速开始

当前没有可构建或可运行的应用，因此没有经过验证的安装 / 构建 / 启动命令。如需改动仓库内容，先阅读 [`AGENTS.md`](AGENTS.md) 与[项目概述](docs/ai/project-overview.md)。

## 项目文档

- [插件 ai-project-steward 中文说明](docs/ai/modules/ai-project-steward.md)
- [项目概述](docs/ai/project-overview.md)
- [模块/插件地图](docs/ai/module-map.md)
- [业务规则](docs/ai/business-rules.md)
- [开发指南](docs/ai/development-guide.md)
- [验证](docs/ai/verification.md)
- [已知问题](docs/ai/known-issues.md)
- [图表索引](docs/ai/diagram-index.md)
- [变更日志](CHANGELOG.md)

## 开发约定

改动代码的 agent 与贡献者请先阅读 [`AGENTS.md`](AGENTS.md)。
