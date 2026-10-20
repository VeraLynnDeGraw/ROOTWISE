"""Safety and behavior tests for local AI handoff generation."""

import tempfile
import unittest
from pathlib import Path

from rootwise.handoff import build_handoff, save_handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text(
            "# Sample Project\nA local project.\n",
            encoding="utf-8",
        )
        (self.root / "app.py").write_text(
            "def answer():\n    return 42\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_handoff_includes_task_readme_and_selected_file(self):
        result = build_handoff(
            self.root,
            "Explain the entry point.",
            selected_files=["app.py"],
        )

        self.assertIn("# ROOTWISE Handoff", result)
        self.assertIn("Explain the entry point.", result)
        self.assertIn("# Sample Project", result)
        self.assertIn("def answer():", result)
        self.assertIn("Nothing has been transmitted.", result)

    def test_handoff_does_not_read_unselected_source_files(self):
        result = build_handoff(self.root, "Summarize the project.")

        self.assertNotIn("def answer():", result)
        self.assertIn("Project tree", result)

    def test_handoff_tree_hides_sensitive_names_and_directory_contents(self):
        secrets_dir = self.root / "credentials"
        secrets_dir.mkdir()
        (secrets_dir / "private.txt").write_text(
            "do not disclose", encoding="utf-8"
        )
        (self.root / ".env").write_text(
            "TOKEN=private", encoding="utf-8"
        )

        result = build_handoff(self.root, "Review this project.")

        self.assertNotIn("credentials/", result)
        self.assertNotIn("private.txt", result)
        self.assertNotIn(".env", result)
        self.assertNotIn("do not disclose", result)

    def test_content_with_backticks_does_not_break_markdown_fence(self):
        (self.root / "example.md").write_text(
            "Example code:\n```\ninside\n```\n",
            encoding="utf-8",
        )

        result = build_handoff(
            self.root,
            "Review Markdown formatting.",
            selected_files=["example.md"],
        )

        self.assertIn(
            "````\nExample code:\n```\ninside\n```\n\n````",
            result,
        )

    def test_rejects_empty_task(self):
        with self.assertRaisesRegex(ValueError, "Describe the task"):
            build_handoff(self.root, " ")

    def test_rejects_missing_project(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            build_handoff(self.root / "missing", "Review this.")

    def test_rejects_path_traversal(self):
        with self.assertRaisesRegex(ValueError, "inside the project"):
            build_handoff(
                self.root,
                "Review this.",
                selected_files=["../outside.txt"],
            )

    def test_rejects_secret_file(self):
        (self.root / ".env").write_text("TOKEN=private\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Sensitive-looking"):
            build_handoff(
                self.root,
                "Review this.",
                selected_files=[".env"],
            )

    def test_rejects_file_inside_sensitive_directory(self):
        secrets_dir = self.root / "secrets"
        secrets_dir.mkdir()
        secret_file = secrets_dir / "notes.md"
        secret_file.write_text("private material", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Sensitive-looking"):
            build_handoff(
                self.root,
                "Review this.",
                selected_files=["secrets/notes.md"],
            )

    def test_rejects_file_inside_credentials_directory(self):
        credentials_dir = self.root / "credentials"
        credentials_dir.mkdir()
        secret_file = credentials_dir / "notes.md"
        secret_file.write_text("private material", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Sensitive-looking"):
            build_handoff(
                self.root,
                "Review this.",
                selected_files=["credentials/notes.md"],
            )

    def test_rejects_sensitive_key_file(self):
        (self.root / "server.pem").write_text("private material", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Sensitive-looking"):
            build_handoff(
                self.root,
                "Review this.",
                selected_files=["server.pem"],
            )

    def test_rejects_symlink(self):
        outside = self.root.parent / "outside-rootwise-test.txt"
        outside.write_text("outside data", encoding="utf-8")
        link = self.root / "linked.txt"

        try:
            link.symlink_to(outside)

            with self.assertRaisesRegex(ValueError, "Symbolic links"):
                build_handoff(
                    self.root,
                    "Review this.",
                    selected_files=["linked.txt"],
                )
        finally:
            outside.unlink(missing_ok=True)

    def test_large_file_is_omitted(self):
        (self.root / "large.txt").write_text(
            "x" * 13_000,
            encoding="utf-8",
        )

        result = build_handoff(
            self.root,
            "Review this.",
            selected_files=["large.txt"],
        )

        self.assertIn("per-file limit", result)
        self.assertNotIn("x" * 500, result)

    def test_binary_file_is_omitted(self):
        (self.root / "image.bin").write_bytes(b"\x00\x01\x02")

        result = build_handoff(
            self.root,
            "Review this.",
            selected_files=["image.bin"],
        )

        self.assertIn("appears to be a binary file", result)

    def test_handoff_never_overwrites_output(self):
        destination = self.root / "handoff.md"
        destination.write_text("keep me", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "already exists"):
            save_handoff("replace me", destination)

        self.assertEqual(destination.read_text(encoding="utf-8"), "keep me")

    def test_saves_to_new_file(self):
        destination = self.root / "handoff.md"

        result = save_handoff("# Handoff\n", destination)

        self.assertEqual(result, destination)
        self.assertEqual(destination.read_text(encoding="utf-8"), "# Handoff\n")


if __name__ == "__main__":
    unittest.main()
