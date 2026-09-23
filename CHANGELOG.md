# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Add current work under `Unreleased`; create a dated version section only when a release is confirmed.

## [Unreleased]

### Fixed

- `parallel-feature-workflow` 集成完成后分支 worktree 目录残留：`worktree_flow.py` 新增 `remove` 子命令（拒绝未合并/脏工作区，`--force` 仅限放弃干净工作区，变空 `.worktrees` 父目录一并清理，`--delete-branch` 连分支引用一起删除），技能约定改为完成后先询问用户、确认后才清理目录与分支，新增真实 Git 流程回归测试。

### Changed

- Codex 分发改为同步 CLI 确认的本地插件源并执行官方 plugin add，验证安装版本与完整缓存，修复只复制 Skills 导致钩子仍旧的问题。
- 同步目录不再先递归删除目标，保留额外文件并报告差异。优化项目规则及技能的自主性、澄清、授权与完成边界。

### Added

- `project-packager` 脚手架新增 Windows 本地一键调试脚本 `dev.bat`：前台启动、实时日志流到双击窗口、Ctrl+C/关窗即停，按技术栈生成命令（Node `call npm run start`、JVM `java -jar app.jar`、二进制、Docker 前台 `docker compose up`），不写 `app.pid`、不干扰 `start.bat`/`stop.bat` 的服务生命周期，沿用只补缺失与 `TODO(project)` 契约；另修复 `bundle`/`collect` 直接库调用时未规范项目根导致 Windows 短路径下 `relative_to` 崩溃。
- `tools/sync-plugin.py`：一条命令把 `ai-project-steward/` 最新内容统一同步到本机各宿主（ZCode 插件市场+缓存+注册表、Claude Code 市场+缓存+注册表并自动维护 `.claude-plugin` 清单、Codex/Kimi CLI/共享 `.agents/skills` 技能目录分发），`--check` 只读校验、`--only` 指定宿主，内容变化时自动升构建戳/版本号，并输出逐宿主 PASS/FAIL。
- 初始化 AI 可读项目文档：根 `README.md`、`CHANGELOG.md`、`AGENTS.md` 与 `docs/ai/` 文档集（项目概述、插件地图、业务规则、开发指南、验证、已知问题、图表索引）。
- 初始化 Archify 图表工作区（`docs/ai/diagrams/`）。
