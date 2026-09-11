"""文档提醒的真实输入、只读边界与跨宿主命令回归。"""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("doc_guard", PLUGIN / "scripts/doc_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DocGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="文档钩子 空格-")
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        (self.root / "AGENTS.md").write_text("# 测试约定\n", encoding="utf-8")
        (self.root / "docs/ai").mkdir(parents=True)
        (self.root / "docs/ai/business-rules.md").write_text("# 已有规则\n", encoding="utf-8")
        (self.root / "example.py").write_text("print('测试')\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=隔离测试",
             "-c", "user.email=test@example.invalid", "commit", "-qm", "基线"],
            check=True, capture_output=True,
        )
        self.env = os.environ.copy()
        self.env.pop("PLUGIN_DATA", None)
        self.env.pop("CLAUDE_PLUGIN_DATA", None)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, payload, command=None, env=None):
        result = subprocess.run(
            command or [sys.executable, "-X", "utf8", str(PLUGIN / "scripts/doc_guard.py")],
            input=json.dumps(payload), text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=15, cwd=self.root, env=env or self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertTrue(parsed.get("continue"))
        self.assertNotEqual(parsed.get("decision"), "block")
        return parsed

    def test_payload_shapes_do_not_crash(self):
        for payload in [None, [], "text", 1, {"cwd": 1}, {"cwd": []}]:
            with self.subTest(payload=payload):
                self.call(payload)

    def test_non_string_last_message_does_not_crash(self):
        self.call({"cwd": str(self.root), "last_assistant_message": [{"text": "完成"}]})

    def test_clean_repository_has_no_warning(self):
        self.assertNotIn("systemMessage", self.call({"cwd": str(self.root)}))

    def test_dirty_repository_is_advisory_and_read_only(self):
        (self.root / "example.py").write_text("print('变化')\n", encoding="utf-8")
        before = {str(p.relative_to(self.root)): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        result = self.call({"cwd": str(self.root)})
        after = {str(p.relative_to(self.root)): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertIn("systemMessage", result)
        self.assertEqual(before, after)
        self.assertFalse((self.root / "CHANGELOG.md").exists())

    def test_documentation_change_does_not_require_magic_words(self):
        (self.root / "example.py").write_text("print('变化')\n", encoding="utf-8")
        (self.root / "docs/ai/business-rules.md").write_text("# 当前规则\n", encoding="utf-8")
        self.assertNotIn("systemMessage", self.call({"cwd": str(self.root), "last_assistant_message": "完成"}))

    def test_non_repo_and_missing_path_pass(self):
        self.call({"cwd": str(self.root / "missing")})
        with tempfile.TemporaryDirectory() as outside:
            self.call({"cwd": outside})

    def test_active_stop_and_other_event_pass(self):
        self.call({"cwd": str(self.root), "stop_hook_active": True})
        self.call({"cwd": str(self.root), "hook_event_name": "SessionStart"})

    def test_subdirectory_and_unicode_paths(self):
        child = self.root / "中文 子目录"
        child.mkdir()
        self.call({"cwd": str(child)})

    def test_missing_git_and_timeout_are_nonblocking(self):
        for error in [FileNotFoundError("git"), subprocess.TimeoutExpired("git", 5)]:
            with self.subTest(error=type(error).__name__):
                with patch.object(guard, "run", side_effect=error), \
                     patch("sys.stdin", io.StringIO(json.dumps({"cwd": str(self.root)}))), \
                     patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    self.assertEqual(guard.main(), 0)
                    self.assertTrue(json.loads(stdout.getvalue())["continue"])

    def test_invalid_json_passes(self):
        with patch("sys.stdin", io.StringIO("{broken")), \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(guard.main(), 0)
            self.assertTrue(json.loads(stdout.getvalue())["continue"])

    def test_reminder_deduplicates_in_host_data_not_repository(self):
        (self.root / "example.py").write_text("print('变化')\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as data:
            env = dict(self.env, PLUGIN_DATA=data)
            payload = {"cwd": str(self.root), "session_id": "隔离会话"}
            self.assertIn("systemMessage", self.call(payload, env=env))
            self.assertNotIn("systemMessage", self.call(payload, env=env))

    @unittest.skipUnless(os.name == "nt", "仅 Windows shell")
    def test_manifest_command_in_powershell_and_cmd(self):
        hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))
        command = hooks["hooks"]["Stop"][0]["hooks"][0]["commandWindows"]
        for variable in ["PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"]:
            env = dict(self.env)
            env.pop("PLUGIN_ROOT", None)
            env.pop("CLAUDE_PLUGIN_ROOT", None)
            env[variable] = str(PLUGIN)
            for shell in ["powershell", "pwsh"]:
                if shutil.which(shell):
                    self.call(None, [shell, "-NoProfile", "-Command", command], env)
            # cmd /c 接收原始命令行；列表参数会被 Python 以反斜杠转义成错误的第二层引号。
            self.call(None, "cmd /d /c " + command, env)


if __name__ == "__main__":
    unittest.main()
