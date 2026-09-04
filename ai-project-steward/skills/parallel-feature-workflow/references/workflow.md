# Worktree branch workflow

## Planning table

Prepare one row per subtask:

| Order | Branch | Responsibility | Allowed paths | Depends on | Verification | Documentation |
| --- | --- | --- | --- | --- | --- | --- |

Good partitions have explicit boundaries, independent acceptance checks, and little file overlap. Common useful partitions include backend API, client UI after contract stabilization, migration, focused test coverage, or separate modules. Avoid splitting tightly coupled edits across workers.

## Integration gates

A branch is merge-ready only when:

- its worktree is clean and work is committed;
- its scoped verification passes;
- public interfaces and data migrations have been reviewed;
- documentation impact is recorded;
- dependencies are already integrated or explicitly included;
- no unresolved Git operation exists.

After each merge, run tests covering both the merged branch and previously integrated behavior. After the final merge, run repository-level checks and `project_docs.py audit` when project documentation exists.

## Conflict policy

Conflicts indicate the original independence assumption was incomplete. Stop automation, inspect both intended behaviors, resolve at the target branch, rerun affected tests, and record any changed module boundary or business rule. Do not use blanket `ours` or `theirs` resolution.

