# 项目概述

## 目的

托管并管理面向 AI 编程助手的插件（skills / scripts / hooks 及平台清单），作为插件内容与元数据的集中工作区。当前托管 1 个插件：`ai-project-steward`（v0.1.0，作者 Wenxu）。

## 用户与角色

待确认。推测包括：插件维护者（人工）与消费插件能力的 AI 助手宿主环境（如 Codex、Zcode）。

## 核心流程

待确认。当前无插件管理相关的自动化流程（新增/淘汰、校验、分发均未定义）。

## 范围内

- 托管与组织插件目录内容。
- 维护插件的平台清单元数据（`ai-project-steward/.codex-plugin/`、`ai-project-steward/.zcode-plugin/`）。
- 维护本仓库的 AI 可读文档（`docs/ai/`、`AGENTS.md`）。

## 范围外

待确认。推测包括：插件的业务逻辑与自身上下游发布流程（这些能力由 `ai-project-steward/` 内部的 skills / scripts 提供，本仓库暂未封装独立的分发层）。

## 外部依赖

待确认。当前插件均为本地文件，无网络或第三方服务依赖；以 git 做版本管理，仓库已有远程 `origin`（<https://github.com/yunianshu/wenxu-ai-plugin>）。
