"""Run the coordinator against real temporary workspaces and bare remotes."""
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import daily_close
except ModuleNotFoundError:
    daily_close = None
import study_book


class DailyCloseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fast-close-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "workspace"
        self.root.mkdir()
        self.remote = base / "remote.git"
        subprocess.run(["git", "init", "--bare", str(self.remote)], capture_output=True, check=True)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Close Test")
        self.git("config", "user.email", "close@example.invalid")
        self.git("config", "core.autocrlf", "true")
        self.git("remote", "add", "origin", str(self.remote))
        self.write("baseline.txt", b"baseline\n")
        self.git("add", "baseline.txt")
        self.git("commit", "-m", "Baseline")
        self.git("push", "origin", "main")
        self.payload = b"print('hello')\r\n"
        self.write("03-code_codex/practice.py", self.payload)
        self.write("04-notes/lesson.md", "# 完整讲义\n".encode())
        self.write("02-logs/day.md", "# 原课堂流水\n".encode())
        self.write("next.md", b"300-minute next lesson\n")
        self.write("intro.md", "# 今日学习册\n".encode())
        self.write("03-code_codex/go.bat", b"@echo off\r\n")
        self.plan = {
            "date": "2026-11-07", "book": "02-logs/day.md", "intro": "intro.md",
            "visibility": "private", "required_paths": ["next.md"],
            "manifest": [
                {"path": "03-code_codex/practice.py", "cleanup": True},
                {"path": "04-notes/lesson.md", "cleanup": True},
                {"path": "02-logs/day.md", "cleanup": False},
            ],
            "stage_paths": ["03-code_codex/practice.py", "04-notes/lesson.md",
                            "02-logs/day.md", "next.md"],
            "checks": [],
            "restore_checks": [{"name": "restored-python",
                                "commands": [[sys.executable, "{restored}/03-code_codex/practice.py"]],
                                "expected_stdout": "hello\n"}],
        }

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout.strip()

    def runner(self):
        self.assertIsNotNone(daily_close, "The deadline-bounded daily close coordinator is missing")
        return daily_close

    def test_complete_close_preserves_bytes_and_cleans_only_after_remote_final(self):
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "complete", result)
        self.assertFalse((self.root / "03-code_codex/practice.py").exists())
        self.assertFalse((self.root / "04-notes/lesson.md").exists())
        self.assertTrue((self.root / "03-code_codex/go.bat").exists())
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], result["final_commit"])
        data = study_book.verify(self.root, self.plan["book"])
        source = next(s for s in data["sources"] if s["path"] == "03-code_codex/practice.py")
        self.assertEqual(base64.b64decode(source["bytes_b64"]), self.payload)
        self.assertEqual(result["restored_sources"], 3)

    def test_failed_final_push_keeps_disk_originals_and_resume_reuses_final_commit(self):
        module = self.runner()
        original_push = module.NetworkSession.push_verified
        calls = []

        def fail_second(session, sha):
            calls.append(sha)
            if len(calls) == 2:
                raise module.NetworkError("Simulated final upload outage")
            return original_push(session, sha)

        with patch.object(module.NetworkSession, "push_verified", new=fail_second):
            result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_sync", result)
        self.assertEqual((self.root / "03-code_codex/practice.py").read_bytes(), self.payload)
        final = result["final_commit"]
        self.assertNotEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], final)
        resumed = module.run_close(self.root, self.plan, budget_seconds=30, resume=True)
        self.assertEqual(resumed["status"], "complete", resumed)
        self.assertEqual(resumed["final_commit"], final)
        self.assertNotIn("error", resumed)
        self.assertFalse((self.root / "03-code_codex/practice.py").exists())

    def test_accidental_second_start_preserves_the_completed_receipt(self):
        module = self.runner()
        result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "complete", result)
        receipt = self.root / ".git/study-close/2026-11-07.json"
        previous = receipt.read_bytes()
        again = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(again["status"], "pending_validation")
        self.assertEqual(receipt.read_bytes(), previous)

    def test_existing_writer_lock_preserves_its_in_progress_receipt(self):
        module = self.runner()
        receipt = self.root / ".git/study-close/2026-11-07.json"
        receipt.parent.mkdir()
        receipt.write_bytes(b'{"phase":"another-active-writer"}')
        (self.root / ".git/study-close.lock").write_text("12345")
        result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_validation")
        self.assertEqual(receipt.read_bytes(), b'{"phase":"another-active-writer"}')

    def test_explicit_attributes_path_can_be_updated_without_false_source_edit(self):
        self.write(".gitattributes", b"*.bin -text\n")
        self.plan["stage_paths"].append(".gitattributes")
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "complete", result)

    def test_source_changed_by_validation_preserves_all_sources(self):
        module = self.runner()
        command = "from pathlib import Path; Path('03-code_codex/practice.py').write_text('new work')"
        self.plan["checks"] = [{"name": "concurrent-edit", "commands": [[sys.executable, "-c", command]]}]
        result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_validation", result)
        self.assertEqual((self.root / "03-code_codex/practice.py").read_text(), "new work")
        self.assertTrue((self.root / "04-notes/lesson.md").exists())

    def test_restoration_checks_use_restored_working_directory(self):
        self.write("original-only.txt", b"must not leak into recovery checks")
        self.plan["restore_checks"] = [{"name": "isolated-recovery",
            "commands": [[sys.executable, "-c", "from pathlib import Path; assert not Path('original-only.txt').exists()"]]}]
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "complete", result)

    def test_program_sources_require_a_recovery_execution_check(self):
        self.plan["restore_checks"] = []
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_validation")
        self.assertTrue((self.root / "03-code_codex/practice.py").exists())

    def test_index_byte_validation_failure_prevents_the_first_upload(self):
        module = self.runner()
        initial_remote = self.git("ls-remote", "origin", "refs/heads/main").split()[0]
        with patch.object(module.study_book, "snapshot_sources", side_effect=ValueError("Index bytes diverged")):
            result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_validation", result)
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], initial_remote)
        self.assertTrue((self.root / "03-code_codex/practice.py").exists())

    def test_intro_changed_before_resume_blocks_archive(self):
        module = self.runner()
        with patch.object(module.NetworkSession, "push_verified", side_effect=module.NetworkError("offline")):
            result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_sync", result)
        self.write("intro.md", b"changed after frozen close inputs")
        result = module.run_close(self.root, self.plan, budget_seconds=30, resume=True)
        self.assertEqual(result["status"], "pending_validation", result)
        self.assertTrue((self.root / "03-code_codex/practice.py").exists())

    def test_independent_validators_really_overlap(self):
        for own, other in [("first.ready", "second.ready"), ("second.ready", "first.ready")]:
            script = ("from pathlib import Path; import time; "
                      f"Path('{own}').touch(); end=time.monotonic()+2\n"
                      f"while not Path('{other}').exists() and time.monotonic()<end: time.sleep(.01)\n"
                      f"assert Path('{other}').exists(), 'validators ran serially'\nprint('ok')")
            self.plan["checks"].append({"name": own, "commands": [[sys.executable, "-c", script]],
                                        "expected_stdout": "ok\n"})
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "complete", result)

    def test_deadline_stops_slow_validation_and_keeps_originals(self):
        self.plan["checks"] = [{"name": "slow", "commands": [[sys.executable, "-c", "import time; time.sleep(3)"]]}]
        start = time.monotonic()
        result = self.runner().run_close(self.root, self.plan, budget_seconds=0.8)
        self.assertNotEqual(result["status"], "complete")
        self.assertLess(time.monotonic() - start, 2)
        self.assertEqual((self.root / "03-code_codex/practice.py").read_bytes(), self.payload)

    def test_classroom_stop_time_consumes_the_same_total_budget(self):
        self.plan["classroom_ended_at"] = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        result = self.runner().run_close(self.root, self.plan, budget_seconds=1)
        self.assertNotEqual(result["status"], "complete")
        self.assertGreaterEqual(result["elapsed_seconds"], 10)
        self.assertFalse(result["within_budget"])
        self.assertTrue((self.root / "03-code_codex/practice.py").exists())

    def test_edit_during_final_remote_check_blocks_all_cleanup(self):
        module = self.runner()
        original_head = module.NetworkSession.remote_head

        def edit_while_reading(session):
            sha = original_head(session)
            (self.root / "03-code_codex/practice.py").write_bytes(b"newer student source")
            return sha

        with patch.object(module.NetworkSession, "remote_head", new=edit_while_reading):
            result = module.run_close(self.root, self.plan, budget_seconds=30)
        self.assertNotEqual(result["status"], "complete")
        self.assertEqual((self.root / "03-code_codex/practice.py").read_bytes(), b"newer student source")
        self.assertTrue((self.root / "04-notes/lesson.md").exists())

    def test_unrelated_staged_work_is_not_committed(self):
        self.write("unrelated.txt", b"keep separate")
        self.git("add", "unrelated.txt")
        result = self.runner().run_close(self.root, self.plan, budget_seconds=30)
        self.assertEqual(result["status"], "pending_validation", result)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "unrelated.txt")


if __name__ == "__main__":
    unittest.main()
