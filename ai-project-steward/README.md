# ai-project-steward

## Project overview

ai-project-steward 是一个跨 AI 编程助手宿主（ZCode、Claude Code、Codex、Kimi CLI）分发的插件：统辖项目知识文档、Archify 架构/流程图、并行分支交付与经校验的发布产物。当前状态：0.1.0，已在上述四类宿主安装并验证。

## Technology

Python 3（标准库脚本）+ Markdown skills。无构建链。

## Quick start

插件由宿主环境加载后按技能名触发（如文档维护用 project-doc-manager、图表用 project-diagrams、发布用 project-packager）。仓库级确定性校验：

```bash
py ai-project-steward/scripts/project_docs.py audit --root .
```

## Project structure

See [`docs/ai/module-map.md`](docs/ai/module-map.md) for module responsibilities, entry points, and dependencies.

## Project documentation

- [Changelog](CHANGELOG.md)
- [Project overview](docs/ai/project-overview.md)
- [Business rules](docs/ai/business-rules.md)
- [Development guide](docs/ai/development-guide.md)
- [Verification](docs/ai/verification.md)
- [Known issues](docs/ai/known-issues.md)
- [Diagram index](docs/ai/diagram-index.md)

## Development conventions

Coding agents and contributors should read [`AGENTS.md`](AGENTS.md) before changing code.
