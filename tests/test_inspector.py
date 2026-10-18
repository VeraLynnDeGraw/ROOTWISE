
import tempfile
import unittest
from pathlib import Path

from rootwise.inspector import inspect_repository


class InspectorTests(unittest.TestCase):
    def test_detects_present_and_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Example\n")
            (root / "LICENSE").write_text("Example license\n")

            report = inspect_repository(root)
            findings = {
                item["check"]: item for item in report["findings"]
            }

            self.assertEqual(
                findings["Project documentation"]["status"],
                "present",
            )
            self.assertEqual(
                findings["License file"]["status"],
                "present",
            )
            self.assertEqual(
                findings["Security policy"]["status"],
                "not_found",
            )

    def test_rejects_nonexistent_target(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist"

            with self.assertRaises(FileNotFoundError):
                inspect_repository(missing)

    def test_report_includes_limitations(self):
        with tempfile.TemporaryDirectory() as directory:
            report = inspect_repository(directory)

            self.assertEqual(report["tool"], "ROOTWISE")
            self.assertGreater(report["checks_run"], 0)
            self.assertTrue(report["limitations"])


if __name__ == "__main__":
    unittest.main()
