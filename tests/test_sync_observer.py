"""Tests for ROOTWISE's read-only Git sync observer."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from rootwise.sync_observer import observe_sync_candidates


class SyncObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.git("init", "-q", "--initial-branch=main")
        self.git("config", "user.name", "ROOTWISE Tests")
        self.git("config", "user.email", "rootwise-tests@example.invalid")

        (self.root / "README.md").write_text("# Test project\n")
        self.git("add", "README.md")
        self.git("commit", "-qm", "Initial test commit")

    def tearDown(self):
        self.temp_dir.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_detects_untracked_document(self):
        (self.root / "notes.md").write_text("# Notes\n")

        report = observe_sync_candidates(self.root)

        finding = next(
            item for item in report["findings"]
            if item["path"] == "notes.md"
        )
        self.assertEqual(finding["status"], "untracked")
        self.assertEqual(finding["kind"], "document")
        self.assertTrue(finding["review_required"])

    def test_detects_modified_tracked_file(self):
        (self.root / "README.md").write_text("# Updated project\n")

        report = observe_sync_candidates(self.root)

        finding = next(
            item for item in report["findings"]
            if item["path"] == "README.md"
        )
        self.assertEqual(finding["status"], "modified")

    def test_flags_sensitive_looking_filename(self):
        (self.root / "private_key.pem").write_text("test placeholder")

        report = observe_sync_candidates(self.root)

        finding = next(
            item for item in report["findings"]
            if item["path"] == "private_key.pem"
        )
        self.assertIsNotNone(finding["risk"])
        self.assertEqual(report["summary"]["risk_flags"], 1)

    def test_observation_does_not_stage_changes(self):
        (self.root / "draft.md").write_text("Unpublished draft\n")
        before = self.git("status", "--porcelain").stdout

        observe_sync_candidates(self.root)

        after = self.git("status", "--porcelain").stdout
        self.assertEqual(before, after)
        self.assertIn("?? draft.md", after)

    def test_reports_branch_and_review_status(self):
        report = observe_sync_candidates(self.root)

        self.assertEqual(report["branch"], "main")
        self.assertEqual(report["publication_status"], "REVIEW_REQUIRED")
        self.assertIn(str(self.root), report["repository"])

    def test_classifies_project_configuration(self):
        (self.root / "pyproject.toml").write_text("[project]\nname='example'\n")

        report = observe_sync_candidates(self.root)
        finding = next(
            item for item in report["findings"]
            if item["path"] == "pyproject.toml"
        )

        self.assertEqual(finding["kind"], "project_config")
        self.assertTrue(finding["review_required"])

    def test_classifies_source_and_test_files(self):
        (self.root / "example.py").write_text("print('example')\n")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_example.py").write_text("def test_example(): pass\n")

        report = observe_sync_candidates(self.root)
        kinds = {item["path"]: item["kind"] for item in report["findings"]}

        self.assertEqual(kinds["example.py"], "source_code")
        self.assertEqual(kinds["tests/test_example.py"], "test_code")

    def test_classifies_license_file(self):
        (self.root / "LICENSE").write_text("Example license text\n")

        report = observe_sync_candidates(self.root)
        finding = next(
            item for item in report["findings"]
            if item["path"] == "LICENSE"
        )

        self.assertEqual(finding["kind"], "license")

    def test_rejects_directory_outside_git_repository(self):
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(ValueError):
                observe_sync_candidates(outside)


if __name__ == "__main__":
    unittest.main()
