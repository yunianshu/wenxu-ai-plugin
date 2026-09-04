---
name: project-doc-manager
description: 初始化、更新或审计 AI 可读的仓库文档（含 AGENTS.md、模块地图、业务规则、验证指引、图表索引，以及代码变更后的文档影响评估）。用于为编码代理搭建项目上下文，或让项目文档与代码保持同步。Initialize, update, or audit AI-readable repository documentation, including AGENTS.md, module maps, business rules, verification guidance, diagram indexes, and documentation impact after code changes. Use when setting up project context for coding agents or keeping project documentation synchronized with code.
---

# Project Doc Manager

Keep repository documentation concise, current, and useful to coding agents. Treat Git as change history; project documents describe the current valid state.

## Choose the mode

- **Initialize**: create the documentation skeleton, then replace inferred placeholders with facts supported by repository evidence.
- **Synchronize**: first supplement missing baseline documents, then inspect code changes and update existing authoritative content when needed.
- **Audit**: compare existing documentation with code, commands, paths, interfaces, and module relationships. Report discrepancies before broad rewrites.

Use `python3 "$PLUGIN_ROOT/scripts/project_docs.py" <mode>` when `PLUGIN_ROOT` is available. Otherwise locate this skill's plugin root and run the same script. Supported modes are `init`, `sync`, `impact`, and `audit`.

## Initialize

1. Inspect the repository root, existing instructions, manifests, build files, README files, and top-level modules.
2. Run `project_docs.py init --root <repo>` to create only missing files, including root `README.md`, `CHANGELOG.md`, and the Archify workspace. Never overwrite a non-empty existing file without reviewing it.
3. Make `README.md` the concise human-facing landing page: purpose, verified quick start, project structure, documentation links, and contributor entry. If an existing README lacks links to `docs/ai/` or `AGENTS.md`, add only the missing navigation without replacing useful content.
4. Replace generated prompts with verified facts. Mark genuinely unknown business facts as `待确认`; do not invent them.
5. Keep `AGENTS.md` short: repository rules, commands, constraints, definition of done, and links to detailed documents.
6. Add module rows only for meaningful modules. Record responsibilities, code locations, entry points, dependencies, and authoritative module documents.
7. Invoke `$project-diagrams` to initialize and generate only the architecture or flow diagrams that materially improve project understanding.

Read [document-model.md](references/document-model.md) when initializing or reorganizing documentation.

## Synchronize after code changes

1. Run `project_docs.py sync --root <repo> --format markdown`. Synchronization always checks and creates missing baseline files before analyzing the diff.
2. Populate newly created README, `CHANGELOG.md`, `AGENTS.md`, and `docs/ai/` files with repository-supported facts. Do not leave generated `待确认` prompts when the answer is available from code or existing documentation; do not invent historical releases.
3. Resolve audit findings. For an existing README, supplement missing navigation or current information without replacing useful content.
4. Inspect the actual diff for each reported area. A changed path is a prompt for semantic review, not proof that documentation must change.
5. Update documentation when the change affects business rules, public interfaces, data structures, module boundaries, build/run/test commands, compatibility constraints, or durable operational knowledge.
6. Usually skip semantic edits for formatting, behavior-preserving refactors, local defensive checks, generated files, and minor presentation-only changes. This exception does not permit leaving required baseline documents missing.
7. Modify the single authoritative document in place. Remove obsolete statements and avoid duplicating the same rule elsewhere.
8. In the completion report state either:
   - which documents were updated and why; or
   - `无需更新文档` with the concrete reason.

When the task asks for a distributable, release, installation package, APK, AAB, JAR, executable, image, or source archive, invoke `$project-packager` after synchronization and verification.

When module boundaries, dependencies, actors, state transitions, or business steps change, also invoke `$project-diagrams` to assess architecture and flow diagram impact.

Never change documentation merely to silence the guard. If code and documented business intent conflict, surface the conflict instead of silently declaring either side authoritative.

## Audit

1. Run `project_docs.py audit --root <repo> --format markdown` for deterministic checks, including root README and changelog presence and navigation to `docs/ai/`, `CHANGELOG.md`, and `AGENTS.md`.
2. Inspect semantic consistency that scripts cannot prove: business rules, module boundaries, interface behavior, and verification claims.
3. Present the discrepancy list before making broad or ambiguous corrections. Safe factual corrections explicitly requested by the user may be applied directly.
4. Re-run the audit after edits.

## Completion standard

Report code changes, validation performed, documentation synchronized, and any remaining manual or real-environment verification. Do not claim real-device or production validation unless it actually ran.
