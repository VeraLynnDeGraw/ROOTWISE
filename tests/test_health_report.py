import tempfile
import unittest
from pathlib import Path

from rootwise.health_report import build_health_report


class HealthReportTests(unittest.TestCase):
    def test_summary_matches_inspection_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Example\n")
            (root / "LICENSE").write_text("Example license\n")

            report = build_health_report(root)
            summary = report["summary"]

            self.assertEqual(
                summary["checks_run"],
                len(report["findings"]),
            )
            self.assertEqual(
                summary["present"],
                sum(
                    item["status"] == "present"
                    for item in report["findings"]
                ),
            )
            self.assertEqual(
                summary["not_found"],
                sum(
                    item["status"] == "not_found"
                    for item in report["findings"]
                ),
            )

    def test_report_discloses_unperformed_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            report = build_health_report(directory)
            scope = report["evidence_scope"]

            self.assertTrue(scope["inspection_performed"])
            self.assertFalse(scope["tests_executed"])
            self.assertFalse(scope["file_contents_validated"])
            self.assertFalse(scope["publication_approved"])
            self.assertTrue(report["limitations"])

    def test_missing_recommended_files_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            report = build_health_report(directory)

            self.assertEqual(report["summary"]["recommendations"], 2)
            self.assertEqual(
                {item["path"] for item in report["recommendations"]},
                {"CONTRIBUTING.md", "SECURITY.md"},
            )

    def test_present_recommended_files_clear_recommendations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CONTRIBUTING.md").write_text("# Contributions\\n")
            (root / "SECURITY.md").write_text("# Security\\n")

            report = build_health_report(root)

            self.assertEqual(report["summary"]["recommendations"], 0)
            self.assertEqual(report["recommendations"], [])

    def test_rejects_nonexistent_target(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"

            with self.assertRaises(FileNotFoundError):
                build_health_report(missing)


if __name__ == "__main__":
    unittest.main()
