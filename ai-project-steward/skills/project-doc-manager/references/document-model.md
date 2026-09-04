# Documentation model

Use this default layout, adapting it to the repository rather than creating empty documents without purpose:

```text
README.md
CHANGELOG.md
AGENTS.md
docs/ai/
├── project-overview.md
├── module-map.md
├── business-rules.md
├── development-guide.md
├── verification.md
├── known-issues.md
├── diagram-index.md
├── diagrams/
│   ├── README.md
│   ├── archify.json
│   ├── sources/
│   ├── output/
│   └── receipts/
└── modules/
```

## Ownership

| Information | Authoritative location |
| --- | --- |
| Human-facing purpose, quick start, navigation | `README.md` |
| Notable unreleased and released changes | `CHANGELOG.md` |
| Agent workflow, constraints, done criteria | `AGENTS.md` |
| Product purpose, scope, roles, major flow | `project-overview.md` |
| Feature-to-code navigation | `module-map.md` |
| Business decisions not reliably inferable from code | `business-rules.md` |
| Setup, build, run, environment | `development-guide.md` |
| Minimal and full verification commands | `verification.md` |
| Active limitations and durable workarounds | `known-issues.md` |
| Diagram purpose, evidence, and ownership | `diagram-index.md` |
| Architecture and flow source of truth | `diagrams/sources/*.<type>.json` |
| Validated interactive diagram deliverables | `diagrams/output/*.html` |
| Module boundaries and compatibility details | `modules/<module>.md` |

## Writing rules

- Describe the current valid state; use Git for history.
- Keep the root README concise and link to detailed documents instead of copying them.
- Keep each fact in one authoritative place and link to it elsewhere.
- Prefer exact paths, commands, entry points, and constraints over general prose.
- Record design reasons only when removing them would invite a recurring mistake.
- Do not duplicate source code or document implementation details that are obvious from nearby code.
- Mark unverified business information as `待确认` and resolve it with the user.
