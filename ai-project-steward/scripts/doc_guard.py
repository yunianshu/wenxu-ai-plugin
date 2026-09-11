#!/usr/bin/env python3
"""非阻断的文档影响提醒：只读检查仓库，不替代理决定任务范围。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

TIMEOUT_SECONDS = 5


def output(value: dict) -> int:
    # ASCII JSON 不依赖 Windows 控制台或管道的默认编码。
    print(json.dumps(value, ensure_ascii=True))
    return 0


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=TIMEOUT_SECONDS, check=False,
    )


def already_notified(payload: dict, paths: list[str]) -> bool:
    """仅在宿主专用数据目录去重；不在业务仓库创建完成标记。"""
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    session = payload.get("session_id") or payload.get("thread_id")
    if not data_root or not isinstance(session, str) or not session:
        return False
    fingerprint = hashlib.sha256(
        json.dumps([session, payload.get("cwd"), sorted(paths)], ensure_ascii=True).encode()
    ).hexdigest()
    marker = Path(data_root) / "doc-guard" / (fingerprint + ".seen")
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        with marker.open("x", encoding="utf-8") as handle:
            handle.write("advisory\n")
    except FileExistsError:
        return True
    except OSError:
        # 状态目录不可写不影响用户任务。
        pass
    return False


def inspect(payload: object) -> dict:
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        return {"continue": True}
    if payload.get("hook_event_name", "Stop") != "Stop":
        return {"continue": True}
    cwd_value = payload.get("cwd")
    if cwd_value is not None and not isinstance(cwd_value, str):
        return {"continue": True}
    cwd = Path(cwd_value or os.getcwd()).resolve()
    if not cwd.is_dir():
        return {"continue": True}
    root_result = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"])
    if root_result.returncode or not root_result.stdout.strip():
        return {"continue": True}
    root = Path(root_result.stdout.strip()).resolve()
    if not (root / "AGENTS.md").is_file() or not (root / "docs/ai").is_dir():
        return {"continue": True}

    # impact 不补建文档、不运行 sync/init/audit 修复，始终从当前脚本定位同版本依赖。
    helper = Path(__file__).resolve().with_name("project_docs.py")
    result = run([sys.executable, "-X", "utf8", str(helper), "impact", "--root", str(cwd)])
    if result.returncode:
        return {"continue": True}
    report = json.loads(result.stdout)
    if not isinstance(report, dict):
        return {"continue": True}
    paths = report.get("code_or_config")
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        return {"continue": True}
    if not paths or report.get("docs_changed") or already_notified(payload, paths):
        return {"continue": True}
    return {
        "continue": True,
        "systemMessage": (
            "文档影响提示：当前工作区包含代码或配置变化。仅在本任务改变长期行为、接口或命令时"
            "同步相关文档；这些变化可能属于既有工作，本提示不证明文档缺失，不阻止完成，"
            "无需固定回复词或补建整套文档。"
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        return output(inspect(payload))
    except (ValueError, TypeError, OSError, subprocess.SubprocessError):
        # 非强制文档提醒不能因格式、路径、Git、编码或超时错误打断任务。
        return output({"continue": True})


if __name__ == "__main__":
    sys.exit(main())
