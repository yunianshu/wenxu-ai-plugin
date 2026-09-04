# 插件中文说明：ai-project-steward

本仓库当前托管的插件。面向人工读者的中文速览；插件自带文件（各技能 SKILL、平台 plugin.json、插件 CHANGELOG）均以英文为原文，本页为其中文对照与摘要。

## 它是什么

`ai-project-steward` 是一个 AI 编程助手插件，帮项目在四件事上保持专业：**项目文档、架构图、并行交付、发布产物**。由 Wenxu 维护，当前托管版本 **v0.1.0**（其自身 CHANGELOG 尚未有已发布版本，变更处于 `Unreleased`）。

## 面向宿主与清单

| 宿主 | 清单文件 | 说明 |
| --- | --- | --- |
| Codex | `ai-project-steward/.codex-plugin/plugin.json` | 版本带 `codex` 变体后缀 |
| Zcode | `ai-project-steward/.zcode-plugin/plugin.json` | 原生 ZCode 清单 |

同源插件也会以 marketplace 形式分发到 Claude Code 环境；本仓库是它的可追踪副本。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `ai-project-steward/skills/` | 4 个技能（见下） |
| `ai-project-steward/scripts/` | 5 个 Python 脚本（见下） |
| `ai-project-steward/hooks/hooks.json` | Stop 钩子：每轮编码收尾前检查文档影响 |
| `ai-project-steward/assets/` | 素材（当前为空） |
| `ai-project-steward/CHANGELOG.md` | 插件英文变更日志 |

## 技能（skills）

| 技能 | 中文说明 | 典型触发场景 |
| --- | --- | --- |
| `project-doc-manager` | 初始化 / 同步 / 审计 AI 可读仓库文档（AGENTS.md、模块地图、业务规则、验证、图表索引等），并评估代码变更后的文档影响。 | 首次为仓库搭建 agent 上下文，或代码变化后让文档跟上。 |
| `project-diagrams` | 依据仓库证据生成或更新架构 / 流程 / 时序 / 数据流 / 生命周期图（[archify](https://github.com/tt-a1i/archify) 模型）。 | 需要反映模块关系、流程或架构的可视化图表。 |
| `project-packager` | 构建发布版本，产出带脚本契约的可部署 tar.gz 包。 | 实现要以可下载、可安装、可升级、可回滚的发布产物收尾。 |
| `parallel-feature-workflow` | 把功能拆成独立子任务，用隔离 worktree 并行实现，校验后按依赖顺序合并。 | 需要用多分支 / 多代理并发实现同一功能的不同部分。 |

各技能的权威说明见 `ai-project-steward/skills/*/SKILL.md`。

## 脚本（scripts）

| 脚本 | 中文说明 |
| --- | --- |
| project_docs.py | 初始化并校验 AI 可读仓库文档（模式：init / sync / impact / audit）。 |
| diagram_docs.py | 在项目内管理 Archify 图表工作区。 |
| doc_guard.py | 一次性 Stop 钩子，让收尾前把文档影响纳入考量。 |
| release_artifacts.py | 探测、收集并审计项目的发布产物；`scaffold` 可在仓库缺失打包文件时按检测到的技术栈生成部署脚本模板（含 Windows 一键启动/停止的 start.bat 与 stop.bat，不覆盖已有文件、不自行发明版本），`bundle` 遇缺失脚本会自动补建并在结果中标注。 |
| worktree_flow.py | 并行特性分支场景下的 Git worktree 安全辅助。 |

## 使用入门

在支持的环境加载插件后，按其技能名触发即可（如文档维护用 `project-doc-manager`、图表用 `project-diagrams`）。仓库级确定性校验可运行（示例，非自动流程）：

```bash
py ai-project-steward/scripts/project_docs.py audit --root .
```

## 变更摘要（插件 CHANGELOG：Unreleased）

- **新增**：`release_artifacts.py scaffold`——仓库缺失打包文件时按检测到的技术栈生成部署脚本模板（只补缺失文件、不覆盖已有脚本、不自行发明版本，可记录用户确认的初始版本），并同时生成 Windows 一键启动/停止的 start.bat 与 stop.bat（CRLF 行尾、PID 文件幂等、可选 `HEALTH_URL` 健康检查、docker 项目走 compose），`bundle` 遇缺失脚本会自动补建并在结果中标注。
- **新增**：带单一顶层目录、栈检测、校验和，以及 package / backup / restore / start / stop / upgrade 脚本契约的版本化 tar.gz 部署打包。
- **新增**：与 Archify 兼容的图表工作区（typed JSON 源、校验后的 HTML、receipts 证据）。
- **新增**：为被管项目创建并同步根 `CHANGELOG.md`；同步时补全缺失的基线文档。
- **变更**：发布包版本改为从项目权威版本文件 / 构建清单解析，版本冲突会阻断打包。
- **变更**：架构与流程图改用 [archify](https://github.com/tt-a1i/archify) 模型替代 Mermaid 作为主格式。
- **修复**：ZCode 钩子改用跨宿主兼容的 `CLAUDE_PLUGIN_ROOT` 路径变量，并附带原生 ZCode 清单。
- **修复**：Stop 钩子 doc_guard.py 在宿主下发字面 `null` 或非对象 payload 时不再崩溃退出（改为放行），并对钩子 JSON 输出做 ASCII 转义，避免非 ASCII 的阻断原因在 Windows 管道编码下乱码。

英文原文见 `ai-project-steward/CHANGELOG.md`。
