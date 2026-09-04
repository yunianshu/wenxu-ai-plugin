#!/usr/bin/env python3
"""Safe Git worktree helper for parallel feature branches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


def git(cwd: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc


def repo_root(cwd: str) -> Path:
    start = Path(cwd).expanduser().resolve()
    proc = git(start, "rev-parse", "--show-toplevel", check=True)
    return Path(proc.stdout.strip()).resolve()


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    if not value:
        raise ValueError("feature and task names must contain letters or digits")
    return value[:48]


def branch_exists(root: Path, branch: str) -> bool:
    return git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0


def operation_in_progress(root: Path) -> list[str]:
    git_dir = Path(git(root, "rev-parse", "--git-dir", check=True).stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    markers = {
        "merge": "MERGE_HEAD",
        "rebase": "rebase-merge",
        "rebase-apply": "rebase-apply",
        "cherry-pick": "CHERRY_PICK_HEAD",
        "revert": "REVERT_HEAD",
    }
    return [name for name, marker in markers.items() if (git_dir / marker).exists()]


def current_branch(root: Path) -> str:
    return git(root, "branch", "--show-current", check=True).stdout.strip()


def dirty(root: Path) -> list[str]:
    return [line for line in git(root, "status", "--porcelain", check=True).stdout.splitlines() if line]


def default_worktree(root: Path, branch: str) -> Path:
    safe = branch.replace("/", "-")
    return root.parent / f"{root.name}.worktrees" / safe


def parse_worktrees(root: Path) -> list[dict[str, str]]:
    proc = git(root, "worktree", "list", "--porcelain", check=True)
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in proc.stdout.splitlines() + [""]:
        if not line:
            if current:
                if "branch" in current:
                    current["branch"] = current["branch"].removeprefix("refs/heads/")
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return records


def inspect(root: Path) -> dict:
    return {
        "root": str(root),
        "current_branch": current_branch(root),
        "dirty": dirty(root),
        "operations": operation_in_progress(root),
        "worktrees": parse_worktrees(root),
    }


def create(root: Path, base: str, feature: str, task: str, path: str | None) -> dict:
    if operation_in_progress(root):
        raise RuntimeError("repository has an unfinished Git operation")
    base_check = git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    if base_check.returncode != 0:
        raise RuntimeError(f"base revision does not exist: {base}")
    branch = f"feature/{slug(feature)}/{slug(task)}"
    if branch_exists(root, branch):
        raise RuntimeError(f"branch already exists: {branch}")
    destination = Path(path).expanduser().resolve() if path else default_worktree(root, branch)
    if destination.exists():
        raise RuntimeError(f"worktree destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    proc = git(root, "worktree", "add", "-b", branch, str(destination), base)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return {"branch": branch, "path": str(destination), "base": base}


def branch_worktree(root: Path, branch: str) -> Path | None:
    for record in parse_worktrees(root):
        if record.get("branch") == branch:
            return Path(record["worktree"])
    return None


def preflight(root: Path, branch: str, target: str) -> dict:
    problems: list[str] = []
    if not branch_exists(root, branch):
        problems.append(f"missing branch: {branch}")
    if current_branch(root) != target:
        problems.append(f"current branch must be {target}")
    if dirty(root):
        problems.append("target worktree is dirty")
    if operation_in_progress(root):
        problems.append("target repository has an unfinished Git operation")
    worktree = branch_worktree(root, branch)
    branch_dirty = dirty(worktree) if worktree and worktree.exists() else []
    if branch_dirty:
        problems.append("source branch worktree is dirty")
    ahead = None
    if branch_exists(root, branch) and git(root, "rev-parse", "--verify", f"{target}^{{commit}}").returncode == 0:
        proc = git(root, "rev-list", "--count", f"{target}..{branch}", check=True)
        ahead = int(proc.stdout.strip())
        if ahead == 0:
            problems.append("source branch has no commits ahead of target")
    return {
        "branch": branch,
        "target": target,
        "source_worktree": str(worktree) if worktree else None,
        "commits_ahead": ahead,
        "ready": not problems,
        "problems": problems,
    }


def merge(root: Path, branch: str, target: str) -> dict:
    result = preflight(root, branch, target)
    if not result["ready"]:
        raise RuntimeError("; ".join(result["problems"]))
    proc = git(root, "merge", "--no-ff", "--no-edit", branch)
    if proc.returncode != 0:
        raise RuntimeError(
            "merge stopped; inspect conflicts and either resolve them deliberately or run git merge --abort. "
            + (proc.stderr.strip() or proc.stdout.strip())
        )
    return {
        "branch": branch,
        "target": target,
        "merged": True,
        "head": git(root, "rev-parse", "HEAD", check=True).stdout.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect")
    create_parser = sub.add_parser("create")
    create_parser.add_argument("--base", required=True)
    create_parser.add_argument("--feature", required=True)
    create_parser.add_argument("--task", required=True)
    create_parser.add_argument("--path")
    sub.add_parser("status")
    for name in ("preflight-merge", "merge"):
        item = sub.add_parser(name)
        item.add_argument("--branch", required=True)
        item.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        root = repo_root(args.root)
        if args.command in {"inspect", "status"}:
            result = inspect(root)
        elif args.command == "create":
            result = create(root, args.base, args.feature, args.task, args.path)
        elif args.command == "preflight-merge":
            result = preflight(root, args.branch, args.target)
        else:
            result = merge(root, args.branch, args.target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

