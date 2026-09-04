# Module map

| Module | Responsibility | Code location | Entry point | Dependencies |
| --- | --- | --- | --- | --- |
| project-doc-manager | init/sync/impact/audit 被管项目文档基线；支持 `--subdir` 管理插件集合仓库的子目录文档集 | `scripts/project_docs.py` | SKILL.md + CLI init / sync / impact / audit 子命令 | Python 3, git |
| project-diagrams | 管理与校验 Archify 图表工作区 | `scripts/diagram_docs.py` | SKILL.md + CLI | Python 3 |
| parallel-feature-workflow | git worktree 并行特性交付安全辅助 | `scripts/worktree_flow.py` | SKILL.md + agents/openai.yaml | git |
| project-packager | 探测/收集/审计发布产物；scaffold 部署脚本与 Windows 一键脚本；bundle 单顶层 tar.gz | `scripts/release_artifacts.py` | SKILL.md + CLI detect / version / scaffold / collect / bundle / audit 子命令 | Python 3, 目标项目工具链 |
| doc_guard（Stop 钩子） | 收尾前检查文档影响并阻断未同步的收尾 | `scripts/doc_guard.py` + `hooks/hooks.json` | 宿主 Stop 事件（CLAUDE_PLUGIN_ROOT） | Python 3 |
| 平台清单 | 向宿主声明插件名/版本/能力 | `.codex-plugin/plugin.json`、`.zcode-plugin/plugin.json` | 宿主插件加载器 | 无 |

Add detail documents under `docs/ai/modules/` only when a module has non-obvious boundaries, compatibility constraints, or verification requirements.
