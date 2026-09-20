"""worktree 清理的真实 Git 流程回归：默认删除已合并空间目录且不丢工作。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "scripts" / "worktree_flow.py"


class WorktreeRemoveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="worktree清理-")
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True, capture_output=True)
        (self.root / "README.md").write_text("# 基线\n", encoding="utf-8")
        self.commit(self.root, "基线")
        self.branch = "feature/demo/task1"

    def tearDown(self):
        self.temp.cleanup()

    def commit(self, cwd, message):
        subprocess.run(["git", "-C", str(cwd), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(cwd), "-c", "user.name=隔离测试",
             "-c", "user.email=test@example.invalid", "commit", "-qm", message],
            check=True, capture_output=True,
        )

    def call(self, *args):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(self.root), *args],
            text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30,
        )
        payload = {}
        stream = result.stdout.strip() or result.stderr.strip()
        if stream:
            payload = json.loads(stream)
        return result, payload

    def worktrees(self):
        _, payload = self.call("inspect")
        return payload["worktrees"]

    def create_branch(self):
        result, payload = self.call("create", "--base", "main", "--feature", "demo", "--task", "task1")
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(payload["path"])

    def test_merged_branch_worktree_is_removed_and_branch_kept(self):
        path = self.create_branch()
        (path / "feature.txt").write_text("并行成果\n", encoding="utf-8")
        self.commit(path, "并行实现")

        result, _ = self.call("merge", "--branch", self.branch, "--target", "main")
        self.assertEqual(result.returncode, 0, result.stderr)

        result, payload = self.call("remove", "--branch", self.branch, "--target", "main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["removed"])
        self.assertFalse(path.exists())
        self.assertEqual(len(self.worktrees()), 1)  # 只剩主工作区
        parent = self.root.parent / f"{self.root.name}.worktrees"
        self.assertFalse(parent.exists())  # 变空的父目录一并清理
        kept = subprocess.run(
            ["git", "-C", str(self.root), "show-ref", "--verify", "--quiet", f"refs/heads/{self.branch}"],
        )
        self.assertEqual(kept.returncode, 0)  # 分支引用保留，交给已有授权决定
        merged_text = (self.root / "feature.txt").read_text(encoding="utf-8")
        self.assertEqual(merged_text, "并行成果\n")  # 合并成果仍在主工作区

    def test_unmerged_branch_is_refused(self):
        path = self.create_branch()
        (path / "feature.txt").write_text("未合并成果\n", encoding="utf-8")
        self.commit(path, "未合并实现")

        result, payload = self.call("remove", "--branch", self.branch, "--target", "main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not merged into main", payload.get("error", ""))
        self.assertTrue(path.exists())
        self.assertTrue((path / "feature.txt").exists())

    def test_dirty_worktree_is_refused(self):
        path = self.create_branch()
        (path / "uncommitted.txt").write_text("未提交\n", encoding="utf-8")

        result, payload = self.call("remove", "--branch", self.branch, "--target", "main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("dirty", payload.get("error", ""))
        self.assertTrue((path / "uncommitted.txt").exists())

    def test_force_removes_clean_unmerged_worktree(self):
        path = self.create_branch()
        (path / "feature.txt").write_text("放弃的成果\n", encoding="utf-8")
        self.commit(path, "已提交但放弃")

        result, payload = self.call("remove", "--branch", self.branch, "--target", "main", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["removed"])
        self.assertFalse(path.exists())

    def test_remove_main_worktree_is_refused(self):
        result, payload = self.call("remove", "--branch", "main", "--target", "main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("main worktree", payload.get("error", ""))
        self.assertTrue(self.root.exists())

    def test_remove_unknown_branch_reports_error(self):
        result, payload = self.call("remove", "--branch", "feature/nope/x", "--target", "main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no worktree registered", payload.get("error", ""))


if __name__ == "__main__":
    unittest.main()
