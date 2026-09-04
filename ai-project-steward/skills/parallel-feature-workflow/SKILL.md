---
name: parallel-feature-workflow
description: 将功能拆分为相互独立的子任务，创建隔离的 Git worktree 分支，协调并行实现，逐个校验分支，并按依赖顺序把完成的工作合并到目标分支。当希望用多个分支或代理并发实现某个功能的不同部分时使用。Split a feature into independent subtasks, create isolated Git worktree branches, coordinate parallel implementation, verify each branch, and merge completed work into the target branch in dependency order. Use when the user wants multiple branches or agents to implement parts of a feature concurrently.
---

# Parallel Feature Workflow

Use one Git worktree per subtask so parallel workers have isolated files and indexes. Prefer different modules or low-overlap boundaries; do not create parallel branches merely to increase activity.

Read [workflow.md](references/workflow.md) before creating branches or merging.

The deterministic helper is:

```text
python3 "$PLUGIN_ROOT/scripts/worktree_flow.py" <command>
```

Supported commands are `inspect`, `create`, `status`, `preflight-merge`, and `merge`.

## Plan before mutation

1. Identify the target branch and verify the repository has no unresolved merge, rebase, or cherry-pick.
2. Decompose the feature into independently testable subtasks with explicit ownership, allowed paths, dependencies, acceptance checks, and documentation impact.
3. Keep shared contracts in an earlier foundation task. Downstream branches should start only after that contract is stable, or explicitly depend on its branch.
4. Present the branch plan before creating worktrees when decomposition or merge order requires non-trivial judgment.

Use branch names like `feature/<feature-slug>/<task-slug>`. Sanitize names with the helper rather than interpolating untrusted text into shell commands.

## Create and implement

For each approved subtask, run:

```text
worktree_flow.py create --base <base> --feature <feature> --task <task>
```

The helper creates a sibling worktree directory by default. Give each worker only its task, worktree path, allowed files, dependency assumptions, tests, and completion contract. If agent delegation is available and the user requested parallel execution, assign one worker per independent worktree.

Each branch must:

- read the repository's `AGENTS.md` and relevant project documents;
- avoid unrelated refactors and files owned by another branch;
- run the smallest relevant tests;
- assess and synchronize documentation using `$project-doc-manager`;
- update affected architecture or flow diagrams using `$project-diagrams`;
- after integration, invoke `$project-packager` when the task requires a distributable artifact;
- finish with a focused commit and a summary of changed files, tests, and remaining risks.

## Integrate

1. Run `status` and confirm every required branch has committed work and a clean worktree.
2. Merge foundation and dependency branches first. Rebase or update dependent work only when the user or repository policy allows it.
3. Run `preflight-merge` for the next branch. Stop on dirty target state, missing branch, unresolved operation, or failed branch verification.
4. Run `merge` only from a clean target worktree whose current branch equals `--target`. The helper uses a non-fast-forward merge and never pushes.
5. On conflict, stop. Report conflicting files and choose a resolution based on intended behavior; never accept one side wholesale without inspection.
6. After every merge, run integration checks. Run the full agreed verification and documentation audit after the final merge.
7. Do not delete branches or worktrees automatically. Offer cleanup only after successful integration and user confirmation.

## Safety boundaries

- Never push, force-push, delete branches, remove worktrees, or rewrite published history without explicit authorization.
- Never merge into a dirty target branch.
- Do not claim branches are independent when they modify the same contract or central file.
- If a branch's tests fail, do not merge it merely because other branches passed.
