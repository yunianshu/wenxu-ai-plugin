"""scaffold 生成 Windows 本地一键调试 dev.bat 的契约回归。"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_artifacts", PLUGIN / "scripts/release_artifacts.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

ALL_WINDOWS_SCRIPTS = ("dev.bat", "start.bat", "stop.bat")


class DevBatContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="packager devbat ")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def scaffold_node(self):
        (self.root / "package.json").write_text(
            json.dumps({"name": "demo", "version": "0.3.0", "scripts": {"start": "node server.js"}}),
            encoding="utf-8")
        return release.scaffold(self.root, None)

    def assert_crlf(self, path: Path):
        data = path.read_bytes()
        self.assertTrue(data.count(b"\n") > 0)
        self.assertEqual(data.count(b"\r\n"), data.count(b"\n"), f"{path.name} must use CRLF line endings")

    def test_scaffold_creates_dev_bat_for_every_profile(self):
        stacks = {
            "node": ["package.json"],
            "jvm": ["pom.xml"],
            "binary": ["go.mod"],
            "docker": ["docker-compose.yml"],
            "generic": [],
        }
        markers = {
            "node": {"profile_file": json.dumps({"name": "demo", "version": "0.3.0"}), "needs_version": False},
            "jvm": {"profile_file": "<project><version>0.2.0</version></project>", "needs_version": False},
            "binary": {"profile_file": "module demo\n", "needs_version": True},
            "docker": {"profile_file": "services: {}\n", "needs_version": True},
            "generic": {"profile_file": "", "needs_version": True},
        }
        for stack, files in stacks.items():
            with self.subTest(stack=stack):
                temp = tempfile.TemporaryDirectory(prefix=f"packager devbat {stack} ")
                root = Path(temp.name)
                try:
                    for name in files:
                        (root / name).write_text(markers[stack]["profile_file"], encoding="utf-8")
                    result = release.scaffold(root, "0.1.0" if markers[stack]["needs_version"] else None)
                    self.assertIn("dev.bat", result["created"], "scaffold must create dev.bat")
                    self.assertIn(result["profile"], ("node", "jvm", "binary", "docker", "generic"))
                    dev = root / "dev.bat"
                    self.assertTrue(dev.is_file())
                    self.assert_crlf(dev)
                    text = dev.read_text(encoding="utf-8")
                    self.assertIn("TODO(project)", text, "dev.bat must keep the review marker")
                    self.assertIn("pause", text, "double-click window must stay visible after exit")
                finally:
                    temp.cleanup()

    def test_dev_bat_commands_are_stack_aware(self):
        node = release.render_script("dev.bat", "node")
        self.assertIn("call npm run start", node)
        self.assertIn("TODO(project)", node)
        jvm = release.render_script("dev.bat", "jvm")
        self.assertIn("java -jar app.jar", jvm)
        binary = release.render_script("dev.bat", "binary")
        self.assertIn("app.exe", binary)
        generic = release.render_script("dev.bat", "generic")
        self.assertIn("TODO(project)", generic)

    def test_dev_bat_runs_foreground_without_pid_lifecycle(self):
        for profile in ("node", "jvm", "binary", "generic"):
            with self.subTest(profile=profile):
                text = release.render_script("dev.bat", profile)
                self.assertNotIn("-WindowStyle Hidden", text, "dev.bat must run in the foreground window")
                self.assertNotIn(">app.pid", text, "dev.bat must not record a service PID")

    def test_docker_dev_bat_uses_foreground_compose(self):
        text = release.render_script("dev.bat", "docker")
        self.assertIn('docker compose -f "%COMPOSE_FILE%" up', text)
        self.assertNotIn("up -d", text, "docker dev.bat must stay in the foreground")
        self.assertNotIn(">app.pid", text)

    def test_existing_dev_bat_is_never_overwritten(self):
        result = self.scaffold_node()
        self.assertIn("dev.bat", result["created"])
        custom = self.root / "dev.bat"
        custom.write_bytes(b"@echo off\r\nrem my custom dev launcher\r\n")
        second = release.scaffold(self.root, None)
        self.assertNotIn("dev.bat", second["created"])
        self.assertIn("dev.bat", second["existing"])
        self.assertEqual(custom.read_bytes(), b"@echo off\r\nrem my custom dev launcher\r\n")

    def test_todo_marker_count_covers_dev_bat(self):
        self.scaffold_node()
        counted = sum((self.root / name).read_text(encoding="utf-8").count("TODO(project)")
                      for name in release.REQUIRED_SCRIPTS + release.WINDOWS_SCRIPTS
                      if (self.root / name).exists())
        result = release.scaffold(self.root, None)
        self.assertEqual(result["todo_markers"], counted)
        self.assertGreater((self.root / "dev.bat").read_text(encoding="utf-8").count("TODO(project)"), 0)

    def test_bundle_carries_dev_bat_when_matched(self):
        self.scaffold_node()
        result = release.bundle(self.root, "demo", None, ["*.sh", "*.bat", "package.json"], "release")
        staging = Path(result["package_directory"])
        for name in ALL_WINDOWS_SCRIPTS:
            self.assertTrue((staging / name).is_file(), f"bundle must carry {name} when *.bat is included")
        self.assertTrue(Path(result["archive"]).is_file())


@unittest.skipUnless(os.name == "nt", "Windows shell execution only")
class DevBatExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="packager devbat run ")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_dev_bat_is_runnable_and_propagates_exit_code(self):
        release.scaffold(self.root, "0.1.0")
        result = subprocess.run(
            ["cmd", "/c", str(self.root / "dev.bat")],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        self.assertNotEqual(result.returncode, 0, "missing app.exe must fail the debug launcher")
        self.assertIn("[dev] starting in local debug mode", result.stdout)
        self.assertIn("[dev] exited with code", result.stdout)
        self.assertFalse((self.root / "app.pid").exists(), "dev.bat must not write app.pid")

    def test_docker_dev_bat_fails_fast_without_compose_file(self):
        (self.root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        release.scaffold(self.root, "0.1.0")
        (self.root / "docker-compose.yml").unlink()
        result = subprocess.run(
            ["cmd", "/c", str(self.root / "dev.bat")],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("[dev] ERROR: compose file not found", result.stdout)


if __name__ == "__main__":
    unittest.main()
