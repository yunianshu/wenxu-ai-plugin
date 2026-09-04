---
name: project-diagrams
description: Generate, supplement, adjust, validate, or audit architecture, workflow, sequence, data-flow, and lifecycle diagrams from repository evidence using tt-a1i/archify typed JSON and self-contained HTML.
---

# Project Diagrams

Follow [tt-a1i/archify](https://github.com/tt-a1i/archify): typed JSON IR is authoritative and validated self-contained HTML is the generated deliverable. Do not use Mermaid as the primary output.

Run the helper when useful:

```text
python3 "$PLUGIN_ROOT/scripts/diagram_docs.py" <init|inventory|impact|audit> --root <repo>
python3 "$PLUGIN_ROOT/scripts/diagram_docs.py" validate --root <repo> --source <json> [--archify <archify-dir>]
python3 "$PLUGIN_ROOT/scripts/diagram_docs.py" deliver --root <repo> --source <json> [--archify <archify-dir>]
```

Read [diagram-guidance.md](references/diagram-guidance.md) before generating or substantially restructuring diagrams.

## Select the right diagram

- `architecture`: systems, boundaries, components, services, storage, and integrations.
- `workflow`: processes, decisions, approval gates, runbooks, and CI/CD.
- `sequence`: API calls, runtime ordering, asynchronous traces, and returns.
- `dataflow`: pipelines, ETL/ELT, lineage, governance, and consumers.
- `lifecycle`: states, retries, waiting, recovery, and terminal transitions.

Do not generate every type by default. Create the smallest set that materially improves understanding.

## Generate

1. Read `AGENTS.md`, project overview, module map, business rules, existing diagrams, and relevant code entry points.
2. Gather evidence for every node and edge. Distinguish code-confirmed behavior from user-confirmed business intent.
3. Run `diagram_docs.py init` to create the Archify workspace without overwriting existing content.
4. Read the matching Archify schema, `schemas/common.schema.json`, and one matching example. Write a fresh `docs/ai/diagrams/sources/<name>.<type>.json` with stable IDs and `meta.quality_profile: "showcase"`.
5. Validate after every source edit. A showcase pass requires all 9 artifact checks with zero composition errors and warnings.
6. Run `deliver` once for final acceptance into `docs/ai/diagrams/output/`. Never edit generated HTML.
7. Update `docs/ai/diagram-index.md` with type, purpose, evidence, JSON source, HTML output, and status; then run the workspace audit.
8. When possible run Archify `visual-check`; report deterministic delivery, browser evidence, and perceptual review separately.

## Supplement or adjust

Preserve useful existing structure and stable node IDs where practical. Update only the affected subgraph or flow, then check all incoming and outgoing relationships. Remove obsolete nodes and edges rather than leaving historical states in the current diagram.

When code and business documentation disagree, record the uncertainty in supporting documentation and ask for resolution. Never invent a service, event, transition, or dependency.

After code changes, run `diagram_docs.py impact`. Review diagrams when module boundaries, APIs, storage, external integrations, business steps, decisions, events, or lifecycle states changed. Presentation-only code changes normally do not require diagram edits.

## Diagram quality

- Keep one diagram focused on one question.
- Prefer top-down layout when the graph would place more than five nodes horizontally.
- Use short labels and explain details below the diagram.
- Avoid decorative nodes, duplicated flows, and low-information two-node diagrams.
- Show direction and ownership explicitly.
- For important decisions, label branches with the condition or outcome.
- Treat diagrams as current-state documentation; Git provides history.
- Use workflow schema v2 for new diagrams; preserve v1 only for existing fixed-geometry sources.
- Start with automatic routes and labels. Apply only a diagnosed supported geometry fix, one control per repair.
- Static output is the default. Enable trace motion or a visual preset only when requested.

## Completion

Report which diagrams were created or adjusted, the evidence inspected, any unresolved assumptions, and whether the audit passed. If no diagram update is needed, state the concrete reason.
