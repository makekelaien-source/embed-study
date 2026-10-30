"""Exercise real archive/restore behavior; all repositories live in temporary folders."""
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import study_book


class StudyBookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="study-book-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.root = base / "workspace"
        self.root.mkdir()
        self.remote = base / "remote.git"
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Archive Test")
        self.git("config", "user.email", "archive@example.invalid")
        self.git("config", "core.autocrlf", "false")
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(self.remote))
        self.payload = b'print("hello")\r\r\n# ``` nested fence\r\n'
        self.write("03-code_codex/practice.py", self.payload)
        self.write("04-notes/lesson.md", "# 讲义\n[代码](../03-code_codex/practice.py)\n".encode())
        self.write("03-code_codex/go.bat", b"@echo off\r\n")
        self.write("02-logs/2026-10-28.md", "# 原课堂记录\n原始证据\n".encode())
        self.git("add", ".")
        self.git("commit", "-m", "Keep raw source snapshot")
        self.snapshot = self.git("rev-parse", "HEAD").strip()
        self.git("push", "origin", "main")
        self.entries = [
            {"path": "03-code_codex/practice.py", "group": "Python", "role": "学生", "cleanup": True},
            {"path": "04-notes/lesson.md", "group": "Python", "role": "讲义", "cleanup": True},
            {"path": "03-code_codex/go.bat", "group": "公共工具", "role": "教师", "cleanup": False},
            {"path": "02-logs/2026-10-28.md", "group": "课堂原记录", "role": "证据", "cleanup": False},
        ]
        self.book = "02-logs/2026-10-28.md"

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True).stdout

    def build(self):
        study_book.build(self.root, self.book, "2026-10-28", self.snapshot, self.entries, "# 今日重点\n")

    def test_book_is_readable_and_restores_exact_bytes_with_nested_fences(self):
        self.build()
        data = study_book.verify(self.root, self.book)
        self.assertEqual(len(data["sources"]), 4)
        text = (self.root / self.book).read_text(encoding="utf-8")
        self.assertIn("原始证据", text)
        self.assertIn('print("hello")', text)
        self.assertIn("](#src-", text)
        study_book.restore(self.root, self.book, "03-code_codex/practice.py", "03-code_codex/restored.py")
        self.assertEqual((self.root / "03-code_codex/restored.py").read_bytes(), self.payload)
        with self.assertRaises(FileExistsError):
            study_book.restore(self.root, self.book, "03-code_codex/practice.py", "03-code_codex/restored.py")

    def test_cleanup_removes_only_listed_sources_after_real_remote_snapshot(self):
        self.build()
        removed = study_book.clean(self.root, self.book)
        self.assertEqual(set(removed), {"03-code_codex/practice.py", "04-notes/lesson.md"})
        self.assertTrue((self.root / "03-code_codex/go.bat").exists())
        self.assertTrue((self.root / self.book).exists())
        study_book.restore(self.root, self.book, "03-code_codex/practice.py")
        self.assertEqual((self.root / "03-code_codex/practice.py").read_bytes(), self.payload)

    def test_concurrent_source_edit_blocks_all_cleanup(self):
        self.build()
        self.write("03-code_codex/practice.py", b"# newer student work\n")
        with self.assertRaises(ValueError):
            study_book.clean(self.root, self.book)
        self.assertTrue((self.root / "04-notes/lesson.md").exists())

    def test_unpushed_snapshot_blocks_cleanup(self):
        self.build()
        self.write("shared.txt", b"new commit\n")
        self.git("add", "shared.txt")
        self.git("commit", "-m", "Unpushed work")
        with self.assertRaises(ValueError):
            study_book.clean(self.root, self.book)
        self.assertTrue((self.root / "03-code_codex/practice.py").exists())

    def test_readable_code_tampering_is_detected(self):
        self.build()
        path = self.root / self.book
        path.write_text(path.read_text(encoding="utf-8").replace('print("hello")', 'print("changed")'), encoding="utf-8")
        with self.assertRaises(ValueError):
            study_book.verify(self.root, self.book)

    def test_protected_and_outside_paths_are_rejected(self):
        with self.assertRaises(ValueError):
            study_book.build(self.root, self.book, "2026-10-28", self.snapshot,
                             [{"path": "../outside.py", "cleanup": True}], "intro")
        bad = [dict(entry) for entry in self.entries]
        bad[-1]["cleanup"] = True
        with self.assertRaises(ValueError):
            study_book.build(self.root, self.book, "2026-10-28", self.snapshot, bad, "intro")
        self.build()
        with self.assertRaises(ValueError):
            study_book.restore(self.root, self.book, "03-code_codex/practice.py", "../outside.py")

    def github_snapshot(self, metadata, visibility=None):
        """Only the external GitHub network responses are substituted."""
        responses = [self.snapshot.encode(), b"https://github.com/example/study.git",
                     (self.snapshot + " refs/heads/main").encode()]
        response = subprocess.CompletedProcess([], 0, json.dumps(metadata), "")
        with patch.object(study_book, "git", side_effect=responses), \
                patch.object(study_book.subprocess, "run", return_value=response):
            if visibility is None:
                return study_book.private_remote_snapshot(self.root, self.snapshot)
            return study_book.private_remote_snapshot(self.root, self.snapshot, visibility=visibility)

    def test_explicit_public_authorization_accepts_verified_public_snapshot(self):
        try:
            self.github_snapshot({"private": False}, visibility="public")
        except (TypeError, ValueError) as error:
            self.fail(f"Explicitly authorized public snapshot was rejected: {error}")

    def test_private_remains_the_default_visibility_requirement(self):
        with self.assertRaises(ValueError):
            self.github_snapshot({"private": False})
        self.github_snapshot({"private": True})

    def test_public_authorization_rejects_unknown_or_mismatched_visibility(self):
        for metadata in ({}, {"private": None}, {"private": True}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.github_snapshot(metadata, visibility="public")

    def test_explicit_daily_text_exercise_can_be_archived_and_cleaned(self):
        self.write("03-code_codex/practice.txt", b"1234")
        self.git("add", "03-code_codex/practice.txt")
        self.git("commit", "-m", "Preserve daily text exercise")
        self.snapshot = self.git("rev-parse", "HEAD").strip()
        self.git("push", "origin", "main")
        self.entries.append({"path": "03-code_codex/practice.txt", "group": "Tool practice",
                             "role": "Student", "cleanup": True})
        try:
            self.build()
        except ValueError as error:
            self.fail(f"Explicit daily text exercise was rejected: {error}")
        study_book.clean(self.root, self.book)
        self.assertFalse((self.root / "03-code_codex/practice.txt").exists())
        self.assertTrue((self.root / "03-code_codex/go.bat").exists())


if __name__ == "__main__":
    unittest.main()
