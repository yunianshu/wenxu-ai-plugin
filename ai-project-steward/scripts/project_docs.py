#!/usr/bin/env python3
"""Initialize and check AI-readable repository documentation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt", ".adoc"}
IGNORED_PARTS = {
    ".git", ".gradle", ".idea", ".dart_tool", ".next", ".venv", "venv",
    "build", "dist", "coverage", "node_modules", "target", "vendor",
}
CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".h", ".hpp", ".java",
    ".js", ".jsx", ".kt", ".kts", ".php", ".py", ".rb", ".rs", ".scala",
    ".sh", ".sql", ".swift", ".ts", ".tsx", ".vue", ".xml", ".yaml", ".yml",
}
HIGH_IMPACT_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "package.json", "pubspec.yaml", "pom.xml", "Cargo.toml", "go.mod",
    "requirements.txt", "pyproject.toml", "Dockerfile", "docker-compose.yml",
}


def run_git(root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def resolve_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    code, output = run_git(root, "rev-parse", "--show-toplevel")
    return Path(output).resolve() if code == 0 and output else root


def resolve_doc_root(root: Path, subdir: str | None) -> tuple[Path, str]:
    """Resolve the doc-set root: the repository root itself, or one plugin subdirectory inside it."""
    if not subdir:
        return root, "."
    doc_root = (root / subdir).resolve()
    if doc_root == root:
        raise ValueError("--subdir cannot be the repository root itself")
    if root not in doc_root.parents:
        raise ValueError(f"--subdir escapes the repository root: {subdir}")
    if not doc_root.is_dir():
        raise ValueError(f"--subdir does not exist or is not a directory: {subdir}")
    return doc_root, doc_root.relative_to(root).as_posix()


def discover_doc_scopes(root: Path) -> list[tuple[str, Path]]:
    """Subdirectories that carry their own managed doc set (marked by .project-docs.json)."""
    scopes = []
    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_dir() or item.name.startswith(".") or item.name in IGNORED_PARTS:
            continue
        if (item / ".project-docs.json").is_file():
            scopes.append((item.relative_to(root).as_posix(), item))
    return scopes


def write_missing(path: Path, content: str) -> bool:
    if path.exists() and path.stat().st_size > 0:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def discover_stack(root: Path) -> list[str]:
    markers = {
        "Android/Gradle": ["settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"],
        "Flutter/Dart": ["pubspec.yaml"],
        "Node.js": ["package.json"],
        "Java/Maven": ["pom.xml"],
        "Python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "Rust": ["Cargo.toml"],
        "Go": ["go.mod"],
        "Docker": ["Dockerfile", "docker-compose.yml", "compose.yml"],
    }
    return [name for name, files in markers.items() if any((root / file).exists() for file in files)]


def discover_modules(root: Path) -> list[str]:
    modules = []
    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_dir() or item.name.startswith(".") or item.name in IGNORED_PARTS:
            continue
        if item.name in {"docs", "scripts", "tools", "assets"}:
            continue
        modules.append(item.name)
    return modules[:30]


def init_docs(root: Path) -> dict:
    stack = discover_stack(root)
    modules = discover_modules(root)
    stack_text = ", ".join(stack) if stack else "待确认"
    project_name = root.name
    module_rows = "\n".join(
        f"| `{name}/` | 待确认 | `{name}/` | 待确认 | 待确认 |"
        for name in modules
    ) or "| 待确认 | 待确认 | 待确认 | 待确认 | 待确认 |"

    files = {
        root / "README.md": f"""# {project_name}

## Project overview

待确认。用一段简短文字说明项目解决的问题、主要用户和当前状态。

## Technology

{stack_text}

## Quick start

待确认。填写经过验证的安装、构建和启动命令。

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
""",
        root / "CHANGELOG.md": """# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Add current work under `Unreleased`; create a dated version section only when a release is confirmed.

## [Unreleased]

### Added

### Changed

### Fixed

### Removed
""",
        root / "AGENTS.md": f"""# Repository instructions

## Project context

- Overview: `docs/ai/project-overview.md`
- Module map: `docs/ai/module-map.md`
- Business rules: `docs/ai/business-rules.md`
- Development: `docs/ai/development-guide.md`
- Verification: `docs/ai/verification.md`
- Known issues: `docs/ai/known-issues.md`
- Changelog: `CHANGELOG.md`

Detected stack: {stack_text}

## Before changing code

Read this file and the documents relevant to the task. Confirm the root cause and affected callers before editing. Preserve existing architecture and avoid unrelated refactors.

## Constraints

- Do not invent business rules or silently resolve conflicts between code and documentation.
- Do not change public interfaces, persistence schemas, protocols, signing, or production configuration without identifying the impact.
- Preserve user changes outside the task scope.

## Definition of done

- Run the smallest relevant verification first; report anything not run.
- Assess documentation impact after code changes.
- Update the authoritative document when behavior, interfaces, structures, commands, boundaries, or durable constraints change.
- Otherwise report `无需更新文档` and the concrete reason.
""",
        root / "docs/ai/project-overview.md": """# Project overview

## Purpose

待确认。

## Users and roles

待确认。

## Core flows

待确认。

## In scope

待确认。

## Out of scope

待确认。

## External dependencies

待确认。
""",
        root / "docs/ai/module-map.md": f"""# Module map

| Module | Responsibility | Code location | Entry point | Dependencies |
| --- | --- | --- | --- | --- |
{module_rows}

Add detail documents under `docs/ai/modules/` only when a module has non-obvious boundaries, compatibility constraints, or verification requirements.
""",
        root / "docs/ai/business-rules.md": """# Business rules

Record only current rules that cannot be reliably inferred from code. Each rule should identify its scope and affected module.

## Confirmed rules

待确认。
""",
        root / "docs/ai/development-guide.md": f"""# Development guide

## Detected technology

{stack_text}

## Prerequisites

待确认。

## Build and run

待确认。 Replace this text with commands verified in this repository.

## Environment and configuration

待确认。
""",
        root / "docs/ai/verification.md": """# Verification

## Fast checks

待确认。 Add the smallest commands for affected modules.

## Full checks

待确认。 Add release or whole-repository checks.

## Manual or real-environment checks

List behavior that cannot be proven by local automated tests.
""",
        root / "docs/ai/known-issues.md": """# Known issues

Record active limitations and durable workarounds. Remove entries when they are no longer true; use Git for history.

No confirmed entries yet.
""",
        root / "docs/ai/diagram-index.md": """# Diagram index

Archify JSON files are authoritative. HTML files are validated, generated deliverables.

| Diagram | Type | Question answered | Evidence | JSON source | HTML output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 待分析 | 待分析 | 待分析 | 待分析 | 待分析 | 待分析 | pending |
""",
        root / "docs/ai/diagrams/README.md": """# Archify diagram workspace

This workspace follows [Archify](https://github.com/tt-a1i/archify). The sources directory contains authoritative typed JSON IR; output contains self-contained HTML produced by Archify deliver; receipts may contain validation, delivery, and visual-check evidence. Never edit generated HTML by hand.
""",
        root / "docs/ai/diagrams/archify.json": """{
  "schema_version": 1,
  "engine": "tt-a1i/archify",
  "quality_profile": "showcase",
  "locale": "zh-CN",
  "source_dir": "sources",
  "output_dir": "output",
  "receipt_dir": "receipts"
}
""",
        root / "docs/ai/diagrams/sources/.gitkeep": "",
        root / "docs/ai/diagrams/output/.gitkeep": "",
        root / "docs/ai/diagrams/receipts/.gitkeep": "",
        root / ".project-docs.json": """{
  "docs": ["AGENTS.md", "docs/ai/**"],
  "ignore": ["build/**", "dist/**", "coverage/**", "node_modules/**", "target/**"],
  "mappings": []
}
""",
    }
    created = [str(path.relative_to(root)) for path, content in files.items() if write_missing(path, content)]
    return {"root": str(root), "created": created, "preserved": len(files) - len(created), "stack": stack, "modules": modules}


def changed_files(root: Path, base: str | None) -> list[str]:
    args = ["diff", "--name-only", "--diff-filter=ACMRD"]
    if base:
        args.append(base)
    code, tracked = run_git(root, *args)
    if code != 0:
        tracked = ""
    _, staged = run_git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD")
    _, untracked = run_git(root, "ls-files", "--others", "--exclude-standard")
    return sorted({p for block in (tracked, staged, untracked) for p in block.splitlines() if p})


def is_ignored(path: str) -> bool:
    return any(part in IGNORED_PARTS for part in Path(path).parts)


def classify(path: str) -> str:
    p = Path(path)
    low = path.lower()
    if p.name in HIGH_IMPACT_NAMES or low.startswith((".github/", ".gitlab/", "docker/", "deploy/", "infra/")):
        return "build/deployment"
    if any(token in low for token in ("migration", "schema", "database", "entity", "model")):
        return "data/interface"
    if any(token in low for token in ("api", "controller", "route", "protocol", "dto")):
        return "public interface"
    if p.suffix.lower() in CODE_EXTENSIONS:
        return "implementation"
    return "other"


def impact(root: Path, base: str | None, doc_root: Path | None = None) -> dict:
    scope_root = doc_root or root
    prefix = ""
    if scope_root != root:
        prefix = scope_root.relative_to(root).as_posix() + "/"
    files = [p for p in changed_files(root, base) if not is_ignored(p)]
    if prefix:
        files = [p[len(prefix):] for p in files if p.startswith(prefix)]
    docs = [p for p in files if Path(p).suffix.lower() in DOC_EXTENSIONS or p == "AGENTS.md" or p.startswith("docs/")]
    code = [p for p in files if p not in docs and (Path(p).suffix.lower() in CODE_EXTENSIONS or Path(p).name in HIGH_IMPACT_NAMES)]
    areas: dict[str, list[str]] = {}
    for path in code:
        areas.setdefault(classify(path), []).append(path)
    needs_review = bool(code)
    return {
        "root": str(root),
        "scope": prefix.rstrip("/") or ".",
        "changed": files,
        "code_or_config": code,
        "documentation": docs,
        "areas": areas,
        "needs_semantic_review": needs_review,
        "docs_changed": bool(docs),
    }


PATH_PATTERN = re.compile(r"`([^`\n]+(?:/[^`\n]*)?)`")


def iter_markdown(root: Path) -> Iterable[Path]:
    candidates = [root / "AGENTS.md", root / "docs/ai"]
    for candidate in candidates:
        if candidate.is_file():
            yield candidate
        elif candidate.is_dir():
            yield from sorted(candidate.rglob("*.md"))


def plausible_repo_path(value: str) -> bool:
    if value.startswith(("http://", "https://", "$", "~", "/")):
        return False
    if " " in value or value.startswith(("待确认", "docs/ai/**")) or value.rstrip("/") == "docs/ai/modules":
        return False
    return "/" in value or Path(value).suffix != ""


def audit_scope(doc_root: Path, scope: str) -> dict:
    issues = []
    documents = [str(p.relative_to(doc_root)) for p in iter_markdown(doc_root)]
    required = [doc_root / "README.md", doc_root / "CHANGELOG.md", doc_root / "AGENTS.md", doc_root / "docs/ai/project-overview.md", doc_root / "docs/ai/module-map.md", doc_root / "docs/ai/verification.md"]
    for path in required:
        if not path.exists():
            issues.append({"type": "missing-document", "scope": scope, "source": str(path.relative_to(doc_root)), "value": ""})
    readme = doc_root / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8", errors="replace")
        if "docs/ai/" not in readme_text:
            issues.append({"type": "missing-project-doc-link", "scope": scope, "source": "README.md", "value": "docs/ai/"})
        if "AGENTS.md" not in readme_text:
            issues.append({"type": "missing-agent-instructions-link", "scope": scope, "source": "README.md", "value": "AGENTS.md"})
        if "CHANGELOG.md" not in readme_text:
            issues.append({"type": "missing-changelog-link", "scope": scope, "source": "README.md", "value": "CHANGELOG.md"})
    for doc in iter_markdown(doc_root):
        text = doc.read_text(encoding="utf-8", errors="replace")
        for value in PATH_PATTERN.findall(text):
            clean = value.strip().rstrip(".,:;")
            if not plausible_repo_path(clean) or "*" in clean or clean.startswith("docs/ai/modules/<"):
                continue
            target = doc_root / clean
            if not target.exists():
                issues.append({"type": "missing-path", "scope": scope, "source": str(doc.relative_to(doc_root)), "value": clean})
    return {"scope": scope, "root": str(doc_root), "documents": documents, "issues": issues}


def combine_scopes(root: Path, scopes: list[dict]) -> dict:
    issues = [issue for result in scopes for issue in result["issues"]]
    documents = []
    for result in scopes:
        prefix = "" if result["scope"] == "." else result["scope"] + "/"
        documents += [prefix + doc for doc in result["documents"]]
    return {"root": str(root), "scopes": [result["scope"] for result in scopes], "documents": documents, "issues": issues}


def audit(root: Path, subdir: str | None = None) -> dict:
    doc_root, scope = resolve_doc_root(root, subdir)
    if subdir:
        return audit_scope(doc_root, scope)
    return combine_scopes(root, [audit_scope(root, ".")] + [audit_scope(path, name) for name, path in discover_doc_scopes(root)])


def sync_docs(root: Path, base: str | None, subdir: str | None = None) -> dict:
    doc_root, scope = resolve_doc_root(root, subdir)
    if subdir:
        baseline = init_docs(doc_root)
        change_impact = impact(root, base, doc_root)
        consistency = audit(root, subdir)
        return {
            "root": str(root),
            "scope": scope,
            "created_missing": baseline["created"],
            "preserved": baseline["preserved"],
            "impact": change_impact,
            "audit": consistency,
            "needs_semantic_review": bool(
                baseline["created"]
                or change_impact["needs_semantic_review"]
                or consistency["issues"]
            ),
        }
    baseline = init_docs(root)
    created = list(baseline["created"])
    for name, path in discover_doc_scopes(root):
        sub_baseline = init_docs(path)
        created += [f"{name}/{c}" for c in sub_baseline["created"]]
    change_impact = impact(root, base)
    consistency = combine_scopes(root, [audit_scope(root, ".")] + [audit_scope(path, name) for name, path in discover_doc_scopes(root)])
    return {
        "root": str(root),
        "scope": ".",
        "created_missing": created,
        "preserved": baseline["preserved"],
        "impact": change_impact,
        "audit": consistency,
        "needs_semantic_review": bool(
            created
            or change_impact["needs_semantic_review"]
            or consistency["issues"]
        ),
    }


def scope_line(result: dict) -> list[str]:
    scope = result.get("scope")
    return [f"Scope: {scope}"] if scope and scope != "." else []


def as_markdown(mode: str, result: dict) -> str:
    if mode == "init":
        lines = ["# Project documentation initialized", *scope_line(result), "", f"Created: {len(result['created'])}", f"Preserved: {result['preserved']}"]
        lines += ["", "## Created files", ""] + ([f"- `{p}`" for p in result["created"]] or ["- None"])
        return "\n".join(lines)
    if mode == "impact":
        lines = ["# Documentation impact", *scope_line(result), "", f"Semantic review required: {'yes' if result['needs_semantic_review'] else 'no'}", f"Documentation changed: {'yes' if result['docs_changed'] else 'no'}"]
        for area, paths in result["areas"].items():
            lines += ["", f"## {area}", ""] + [f"- `{p}`" for p in paths]
        if not result["areas"]:
            lines += ["", "No relevant code or configuration changes detected."]
        return "\n".join(lines)
    if mode == "sync":
        lines = [
            "# Project documentation synchronized",
            *scope_line(result),
            "",
            f"Created missing files: {len(result['created_missing'])}",
            f"Semantic review required: {'yes' if result['needs_semantic_review'] else 'no'}",
            f"Audit issues: {len(result['audit']['issues'])}",
        ]
        lines += ["", "## Created missing files", ""] + (
            [f"- `{path}`" for path in result["created_missing"]] or ["- None"]
        )
        lines += ["", "## Changed code or configuration", ""] + (
            [f"- `{path}`" for path in result["impact"]["code_or_config"]] or ["- None"]
        )
        lines += ["", "## Audit findings", ""] + (
            [f"- {item['type']} [{item.get('scope', '.')}]: `{item['source']}` -> `{item['value']}`" for item in result["audit"]["issues"]]
            or ["- No deterministic issues found."]
        )
        return "\n".join(lines)
    lines = ["# Documentation audit", *scope_line(result), "", f"Issues: {len(result['issues'])}"]
    if result.get("scopes"):
        lines += ["", f"Scopes audited: {', '.join(result['scopes'])}"]
    lines += ["", "## Findings", ""] + ([f"- {i['type']} [{i.get('scope', '.')}]: `{i['source']}` -> `{i['value']}`" for i in result["issues"]] or ["- No deterministic issues found."])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("init", "sync", "impact", "audit"))
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--subdir", help="Manage the doc set of this plugin subdirectory instead of the repository root; without it, sync/audit also cover discovered subdirectory doc sets")
    parser.add_argument("--base", help="Optional Git revision/range for impact mode")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    root = resolve_root(args.root)
    try:
        if args.mode == "init":
            doc_root, scope = resolve_doc_root(root, args.subdir)
            result = init_docs(doc_root)
            result["scope"] = scope
        elif args.mode == "sync":
            result = sync_docs(root, args.base, args.subdir)
        elif args.mode == "impact":
            doc_root, _ = resolve_doc_root(root, args.subdir)
            result = impact(root, args.base, doc_root if args.subdir else None)
        else:
            result = audit(root, args.subdir)
    except ValueError as exc:
        print(json.dumps({"root": str(root), "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else as_markdown(args.mode, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
