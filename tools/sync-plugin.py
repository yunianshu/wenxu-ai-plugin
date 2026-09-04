#!/usr/bin/env python3
"""Sync the ai-project-steward plugin to every local AI CLI host and verify the result.

Hosts:
  zcode   full plugin: marketplace copy + versioned cache + installed_plugins.json
  claude  full plugin: marketplace copy (+ .claude-plugin manifest) + versioned cache + registry
  codex   the four skills copied into ~/.codex/skills/<name>
  kimi    the four skills copied into ~/.kimi/skills/<name>
  agents  the four skills copied into ~/.agents/skills/<name> (shared skill dir read by ZCode and friends)

Usage:
  python3 tools/sync-plugin.py            # sync changed content to all hosts, then verify
  python3 tools/sync-plugin.py --check    # verify only, no writes
  python3 tools/sync-plugin.py --only claude,codex
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "ai-project-steward"
SKILLS = sorted(p.name for p in PLUGIN.glob("skills/*") if p.is_dir())
IGNORED = {".git", "__pycache__", ".DS_Store"}
HOME = Path.home()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_state(root: Path) -> dict[str, str]:
    state = {}
    if not root.exists():
        return state
    for path in sorted(root.rglob("*")):
        if path.is_dir() or IGNORED & set(path.parts):
            continue
        state[path.relative_to(root).as_posix()] = sha256(path)
    return state


def diff_tree(expected: dict[str, str], actual_root: Path) -> list[str]:
    actual = tree_state(actual_root)
    problems = [f"missing {p}" for p in expected if p not in actual]
    problems += [f"stale {p}" for p, h in expected.items() if p in actual and actual[p] != h]
    problems += [f"extra {p}" for p in actual if p not in expected]
    return problems


def sync_tree(source: Path, target: Path):
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*IGNORED))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def backup(root: Path, host: str, files: list[Path]):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = root / f"backup-sync-{host}-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.exists():
            shutil.copy2(f, dest / f.name)
    return dest


def plugin_state(adapted: dict[str, str] | None = None) -> dict[str, str]:
    state = tree_state(PLUGIN)
    if adapted:
        state.update(adapted)
    return state


def smoke_checks(root: Path) -> list[str]:
    problems = []
    for py in sorted(root.rglob("scripts/*.py")):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as exc:
            problems.append(f"syntax {py.name}: {exc}")
    for skill_md in sorted(root.glob("skills/*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        if not (text.lstrip().startswith("---") and "name:" in text[:200] and "description:" in text[:400]):
            problems.append(f"frontmatter {skill_md.parent.name}")
    return problems


class Zcode:
    id = "zcode"
    root = HOME / ".zcode/cli/plugins"

    def __init__(self):
        self.marketplace = self.root / "marketplaces/local-project-docs/ai-project-steward"
        self.marketplace_json = self.root / "marketplaces/local-project-docs/marketplace.json"
        self.cache_base = self.root / "cache/local-project-docs/ai-project-steward"
        self.registry = self.root / "installed_plugins.json"
        self.version = read_json(PLUGIN / ".codex-plugin/plugin.json")["version"]

    def needs_update(self) -> bool:
        return bool(diff_tree(tree_state(PLUGIN), self.marketplace))

    def bump_version(self) -> str:
        manifest = PLUGIN / ".codex-plugin/plugin.json"
        data = read_json(manifest)
        data["version"] = "0.1.0+codex." + datetime.now().strftime("%Y%m%d%H%M%S")
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.version = data["version"]
        print(f"  repo .codex-plugin stamp bumped -> {self.version} (commit this change)")
        return self.version

    def sync(self):
        if self.needs_update():
            self.bump_version()
        backup(self.root, self.id, [self.registry, self.marketplace_json])
        sync_tree(PLUGIN, self.marketplace)
        cache_dir = self.cache_base / self.version
        sync_tree(PLUGIN, cache_dir)
        reg = read_json(self.registry)
        entry = next(e for e in reg["plugins"] if e["id"] == "ai-project-steward@local-project-docs")
        entry["version"] = self.version
        entry["installPath"] = str(cache_dir)
        entry["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        write_json(self.registry, reg)
        mj = read_json(self.marketplace_json)
        mj["plugins"][0]["version"] = self.version
        write_json(self.marketplace_json, mj)

    def verify(self) -> list[str]:
        expected = tree_state(PLUGIN)
        problems = diff_tree(expected, self.marketplace) + diff_tree(expected, self.cache_base / self.version)
        try:
            entry = next(e for e in read_json(self.registry)["plugins"] if e["id"] == "ai-project-steward@local-project-docs")
            if entry["version"] != self.version:
                problems.append(f"registry version {entry['version']} != {self.version}")
            elif not Path(entry["installPath"]).is_dir():
                problems.append("registry installPath missing")
        except StopIteration:
            problems.append("registry entry missing")
        problems += smoke_checks(self.cache_base / self.version)
        return problems


class Claude:
    id = "claude"
    root = HOME / ".claude/plugins"
    plugin_id = "ai-project-steward@ai-project-steward"

    def __init__(self):
        self.marketplace = self.root / "marketplaces/ai-project-steward/plugins/ai-project-steward"
        self.cache_base = self.root / "cache/ai-project-steward/ai-project-steward"
        self.registry = self.root / "installed_plugins.json"
        self.version = self._installed_version()

    def _installed_version(self) -> str:
        try:
            entry = next(e for e in read_json(self.registry)["plugins"][self.plugin_id] if e["scope"] == "user")
            return entry["version"]
        except (KeyError, StopIteration):
            return "0.2.0"

    def _adapted(self) -> tuple[str, str, str]:
        body = {
            "name": "ai-project-steward",
            "version": self.version,
            "description": read_json(PLUGIN / ".zcode-plugin/plugin.json")["description"],
            "author": {"name": "Wenxu"},
            "keywords": ["documentation", "diagrams", "worktree", "parallel-features", "release-packaging"],
        }
        relpath = ".claude-plugin/plugin.json"
        text = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
        return relpath, text, hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _write_adapted(self, target: Path):
        relpath, text, _ = self._adapted()
        path = target / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def needs_update(self) -> bool:
        relpath, _, digest = self._adapted()
        return bool(diff_tree(plugin_state({relpath: digest}), self.marketplace))

    def bump_version(self) -> str:
        major, minor, patch = (int(x) for x in self.version.split("."))
        self.version = f"{major}.{minor}.{patch + 1}"
        print(f"  claude version bumped -> {self.version}")
        return self.version

    def sync(self):
        if self.needs_update():
            self.bump_version()
        backup(self.root, self.id, [self.registry])
        sync_tree(PLUGIN, self.marketplace)
        self._write_adapted(self.marketplace)
        cache_dir = self.cache_base / self.version
        sync_tree(PLUGIN, cache_dir)
        self._write_adapted(cache_dir)
        reg = read_json(self.registry)
        entries = reg["plugins"][self.plugin_id]
        entry = next(e for e in entries if e["scope"] == "user")
        entry["version"] = self.version
        entry["installPath"] = str(cache_dir)
        entry["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        write_json(self.registry, reg)

    def verify(self) -> list[str]:
        relpath, _, digest = self._adapted()
        expected = plugin_state({relpath: digest})
        problems = diff_tree(expected, self.marketplace) + diff_tree(expected, self.cache_base / self.version)
        try:
            entry = next(e for e in read_json(self.registry)["plugins"][self.plugin_id] if e["scope"] == "user")
            if entry["version"] != self.version:
                problems.append(f"registry version {entry['version']} != {self.version}")
            elif not Path(entry["installPath"]).is_dir():
                problems.append("registry installPath missing")
        except (KeyError, StopIteration):
            problems.append("registry entry missing")
        problems += smoke_checks(self.cache_base / self.version)
        return problems


class SkillHost:
    def __init__(self, id: str, root: Path):
        self.id, self.root = id, root

    def sync(self):
        self.root.mkdir(parents=True, exist_ok=True)
        for name in SKILLS:
            sync_tree(PLUGIN / "skills" / name, self.root / name)

    def verify(self) -> list[str]:
        problems = []
        for name in SKILLS:
            problems += [f"{name}: {p}" for p in diff_tree(tree_state(PLUGIN / "skills" / name), self.root / name)]
        return problems


HOSTS = [
    Zcode(),
    Claude(),
    SkillHost("codex", HOME / ".codex/skills"),
    SkillHost("kimi", HOME / ".kimi/skills"),
    SkillHost("agents", HOME / ".agents/skills"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify only, no writes")
    ap.add_argument("--only", help="comma-separated host filter")
    args = ap.parse_args()
    selected = [h for h in HOSTS if not args.only or h.id in args.only.split(",")]
    failures = 0
    for host in selected:
        mode = "CHECK" if args.check else "SYNC"
        print(f"[{mode}] {host.id}")
        if args.check:
            problems = host.verify()
        else:
            try:
                host.sync()
                problems = host.verify()
            except Exception as exc:  # noqa: BLE001 - report any host failure and continue
                problems = [f"sync error: {exc}"]
        if problems:
            failures += 1
            print(f"  FAIL {host.id}")
            for p in problems[:20]:
                print(f"    - {p}")
            if len(problems) > 20:
                print(f"    ... and {len(problems) - 20} more")
        else:
            print(f"  PASS {host.id}")
    print("RESULT:", "PASS" if failures == 0 else f"FAIL ({failures} host(s))")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
