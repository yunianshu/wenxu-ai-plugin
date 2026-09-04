# Project overview

## Purpose

为 AI 编程助手宿主提供统一的项目治理能力：让被管项目拥有 AI 可读的文档基线并保持同步、以 Archify 模型产出经校验的架构/流程图、在隔离 worktree 中并行交付特性、并以带脚本契约的版本化包收尾发布。

## Users and roles

- 被管项目的开发者与其中的 AI 编程助手（技能的主要消费者）。
- 插件维护者（上层插件集合仓库的作者，负责版本与分发）。

## Core flows

1. project-doc-manager 在被管项目 init/sync 文档基线，Stop 钩子 doc_guard.py 在收尾前检查文档影响。
2. project-diagrams 管理 Archify 图表工作区（typed JSON 源 → 校验后的 HTML + receipts）。
3. parallel-feature-workflow 用 git worktree 隔离并行特性。
4. project-packager 探测/收集/审计发布产物；缺失打包文件时按技术栈 scaffold（含 Windows 一键 start.bat/stop.bat），bundle 产出单一顶层目录的 tar.gz。

## In scope

技能、脚本、钩子、平台清单（.codex-plugin/.zcode-plugin）以及随插件分发的自描述文档。

## Out of scope

上层集合仓库的运维（多宿主分发工具、根文档）——那些属于集合仓库自身的文档集，不在本目录内。

## External dependencies

无第三方运行时依赖；宿主环境需提供 Python 3 与 git。project-packager 的 scaffold 生成的脚本依赖 bash / Windows cmd 与目标项目自身的工具链。
