# Module map

| Module | Responsibility | Code location | Entry point | Dependencies |
| --- | --- | --- | --- | --- |
| project-doc-manager | init/sync/impact/audit 被管项目文档基线；支持 `--subdir` 管理插件集合仓库的子目录文档集 | `scripts/project_docs.py` | SKILL.md + CLI init / sync / impact / audit 子命令 | Python 3, git |
| project-diagrams | 管理与校验 Archify 图表工作区 | `scripts/diagram_docs.py` | SKILL.md + CLI | Python 3 |
| parallel-feature-workflow | git worktree 并行特性交付安全辅助 | `scripts/worktree_flow.py` | SKILL.md + agents/openai.yaml | git |
| project-packager | 探测/收集/审计发布产物；scaffold 部署脚本与 Windows 一键脚本（dev.bat 本地前台调试、start/stop.bat 服务生命周期）；bundle 单顶层 tar.gz | `scripts/release_artifacts.py` | SKILL.md + CLI detect / version / scaffold / collect / bundle / audit 子命令 | Python 3, 目标项目工具链 |
| doc_guard（Stop 钩子） | 只读文档影响提示；异常放行、不阻断、不自动建文档 | `scripts/doc_guard.py` + `hooks/hooks.json` | 宿主 Stop 事件（PLUGIN_ROOT 或 CLAUDE_PLUGIN_ROOT） | Python 3, git |
| 钩子回归 | 隔离验证输入、只读边界、去重及 Windows shell 启动 | `tests/test_doc_guard.py` | unittest discover | Python 3, git；Windows shell 用例仅在 Windows 执行 |
| 平台清单 | 向宿主声明插件名/版本/能力 | `.codex-plugin/plugin.json`、`.zcode-plugin/plugin.json` | 宿主插件加载器 | 无 |

Add detail documents under `docs/ai/modules/` only when a module has non-obvious boundaries, compatibility constraints, or verification requirements.
