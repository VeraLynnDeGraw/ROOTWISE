"""Regression tests for the ROOTWISE Handoff CLI."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from rootwise.cli import main


class HandoffCliTests(unittest.TestCase):
    def test_handoff_prints_clean_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Example project\\n")
            output = io.StringIO()

            with redirect_stdout(output):
                result = main([
                    "handoff", str(root),
                    "--task", "Continue project documentation",
                ])

            self.assertEqual(result, 0)
            rendered = output.getvalue()
            self.assertIn("# ROOTWISE Handoff", rendered)
            self.assertIn("## Task", rendered)
            self.assertIn("Continue project documentation", rendered)
            self.assertNotIn("AI Handoff", rendered)

    def test_handoff_saves_to_a_new_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_path = root / "handoff.md"
            output = io.StringIO()

            with redirect_stdout(output):
                result = main([
                    "handoff", str(root),
                    "--task", "Review the next change",
                    "--output", str(output_path),
                ])

            self.assertEqual(result, 0)
            self.assertTrue(output_path.is_file())
            self.assertIn("# ROOTWISE Handoff", output_path.read_text())
            self.assertIn("Handoff saved locally:", output.getvalue())

    def test_handoff_refuses_to_overwrite_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_path = root / "handoff.md"
            output_path.write_text("preserve this")

            with redirect_stdout(io.StringIO()):
                result = main([
                    "handoff", str(root),
                    "--task", "Test overwrite protection",
                    "--output", str(output_path),
                ])

            self.assertEqual(result, 1)
            self.assertEqual(output_path.read_text(), "preserve this")

    def test_handoff_rejects_missing_task(self):
        with self.assertRaises(SystemExit) as caught:
            main(["handoff", "."])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
