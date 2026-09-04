# Diagram guidance

## Evidence order

Use the strongest available evidence:

1. Executable code, schemas, routes, manifests, and configuration.
2. Tests demonstrating actual behavior.
3. Current project documentation and accepted architecture decisions.
4. User-confirmed intent.

Do not treat directory names alone as proof of runtime relationships.

## Default files

| File | Content |
| --- | --- |
| `docs/ai/diagram-index.md` | Diagram purpose, scope, evidence, owner, authoritative location |
| `docs/ai/diagrams/archify.json` | Engine, locale, quality profile, and directories |
| `docs/ai/diagrams/sources/*.json` | Authoritative Archify typed JSON IR |
| `docs/ai/diagrams/output/*.html` | Validated self-contained HTML deliverables |
| `docs/ai/diagrams/receipts/` | Optional validation, delivery, and visual-check receipts |

Split a file when it becomes difficult to review or when different teams own independent domains. Keep the index authoritative.

## Archify type choices

| Question | Archify type |
| --- | --- |
| What depends on what? | `architecture` |
| What process or decision runs next? | `workflow` |
| In what runtime order? | `sequence` |
| How does data move and transform? | `dataflow` |
| How does an entity change state? | `lifecycle` |

Architecture diagrams should show boundaries and directions, not every class. Business flows should include meaningful failure, cancellation, timeout, retry, or rejection paths only when they are real behavior.

## Supporting note

For each indexed diagram, record:

- what question it answers;
- evidence paths or documents;
- important exclusions;
- unresolved assumptions, if any.
