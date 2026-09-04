#!/usr/bin/env python3
"""One-shot Stop hook that asks Codex to account for documentation impact."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ACKNOWLEDGEMENTS = (
    "无需更新文档",
    "文档同步",
    "documentation updated",
    "no documentation update",
    "docs updated",
)


def output(value: dict) -> int:
    print(json.dumps(value, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return output({"continue": True})

    if payload.get("stop_hook_active"):
        return output({"continue": True})

    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    if not (cwd / ".git").exists():
        proc = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            return output({"continue": True})
        cwd = Path(proc.stdout.strip())

    if not (cwd / "AGENTS.md").exists() or not (cwd / "docs/ai").exists():
        return output({"continue": True})

    message = (payload.get("last_assistant_message") or "").lower()
    if any(token.lower() in message for token in ACKNOWLEDGEMENTS):
        return output({"continue": True})

    plugin_root = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
    command = [sys.executable, str(plugin_root / "scripts/project_docs.py"), "sync", "--root", str(cwd)]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        return output({"continue": True})
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return output({"continue": True})

    if not result.get("needs_semantic_review"):
        return output({"continue": True})

    created = result.get("created_missing") or []
    created_note = f" Missing baseline files were created: {', '.join(created)}." if created else ""
    reason = (
        "Before finishing, complete the project documentation synchronization." + created_note + " Inspect the current Git diff; "
        "update the authoritative docs if behavior, interfaces, data structures, module boundaries, commands, "
        "or durable constraints changed. Resolve audit findings and populate any newly created baseline documents with verified facts. "
        "Otherwise include ‘无需更新文档’ and the concrete reason in the final report."
    )
    return output({"decision": "block", "reason": reason})


if __name__ == "__main__":
    sys.exit(main())
