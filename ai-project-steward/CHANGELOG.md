# Changelog

All notable changes to AI Project Steward are documented here.

## [Unreleased]

### Added

- Subdirectory doc sets for plugin-collection repositories: `project_docs.py --subdir <plugin>` initializes, syncs, and audits a doc set inside a plugin subdirectory; without `--subdir`, `sync` and `audit` also discover and cover every subdirectory doc set marked by `.project-docs.json`, and `impact` filters changed paths to the selected subdirectory.
- Windows one-click `start.bat`/`stop.bat` in `scaffold` output: CRLF line endings, PID-file idempotency, `run.log` output capture, optional `HEALTH_URL` readiness probing, error `pause` for double-click visibility, and `docker compose up/down` for Docker projects.
- `release_artifacts.py scaffold`: generates stack-aware deployment script templates (package/backup/restore/start/stop/upgrade) for exactly the missing files when a repository has no packaging files, records a user-confirmed initial version into `VERSION`, and reports remaining `TODO(project)` markers. `bundle` now scaffolds missing scripts automatically and flags them in its result.
- Versioned tar.gz deployment packaging with a single top-level directory, stack detection, checksums, and package/backup/restore/start/stop/upgrade script contracts.
- Archify-compatible diagram workspaces with typed JSON sources, validated HTML outputs, and receipts.
- Root `CHANGELOG.md` creation and synchronization for managed projects.
- Synchronization that supplements missing baseline documentation.

### Changed

- 面向自主模型收窄技能触发、审批与完成条件：文档维护不自动扩展图表/打包，原生产物与服务部署包分开，常规合并冲突按授权自行分析处理。
- Stop 钩子改为只读、非阻断的文档影响提示，不再调用 sync 自动补文件，不以固定措辞作为完成口令；宿主数据目录可用于提示去重。

- Release package versions are now resolved from the project's authoritative version file or build manifest; conflicting versions block packaging.
- Architecture and flow diagrams now use the `tt-a1i/archify` model instead of Mermaid as the primary format.

### Fixed

- Windows 钩子在 Python 内解析插件环境变量，兼容 PowerShell 与 cmd；异常 cwd、非字符串消息、Git 缺失与超时不再导致未捕获异常。新增隔离回归测试。

- ZCode hook startup now uses the cross-compatible `CLAUDE_PLUGIN_ROOT` path variable instead of Codex-only `PLUGIN_ROOT`, with a native ZCode plugin manifest included.
- The `doc_guard.py` Stop hook no longer crashes with exit code 1 when a host feeds it a literal `null` or non-object hook payload; it now passes through with `continue`. Hook JSON output is ASCII-escaped so non-ASCII block reasons survive Windows pipe encoding.
