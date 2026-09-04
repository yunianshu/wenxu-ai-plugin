# Repository instructions

## Project context

本目录是 ai-project-steward 插件本体，由上层插件集合仓库托管并分发到多个宿主。

- Overview: `docs/ai/project-overview.md`
- Module map: `docs/ai/module-map.md`
- Business rules: `docs/ai/business-rules.md`
- Development: `docs/ai/development-guide.md`
- Verification: `docs/ai/verification.md`
- Known issues: `docs/ai/known-issues.md`
- Changelog: `CHANGELOG.md`

Detected stack: Python 3 (standard library), Markdown skills

## Before changing code

Read this file and the documents relevant to the task. Confirm the root cause and affected callers before editing. Preserve existing architecture and avoid unrelated refactors.

## Constraints

- `.codex-plugin/` 与 `.zcode-plugin/` 是插件公共清单：改动前必须评估对各宿主加载的影响，并同步上层仓库的统一分发工具。
- 本目录会被整体复制分发到各宿主安装缓存：新增文件会随分发落地，勿放置密钥、缓存或本机私有内容。
- 不要编造业务规则，也不要静默裁决代码与文档之间的冲突；冲突时向用户提出。

## Definition of done

- Run the smallest relevant verification first; report anything not run.
- Assess documentation impact after code changes.
- Update the authoritative document when behavior, interfaces, structures, commands, boundaries, or durable constraints change.
- Otherwise report `无需更新文档` and the concrete reason.
