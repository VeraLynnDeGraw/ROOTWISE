import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rootwise.cli import main


class HealthCommandTests(unittest.TestCase):
    def test_health_command_displays_recommendations_and_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(["health", directory])

            rendered = output.getvalue()

            self.assertEqual(result, 0)
            self.assertIn("ROOTWISE REPOSITORY HEALTH REPORT", rendered)
            self.assertIn("Recommendations:  2", rendered)
            self.assertIn("RECOMMENDATIONS", rendered)
            self.assertIn("CONTRIBUTING.md", rendered)
            self.assertIn("SECURITY.md", rendered)
            self.assertIn("EVIDENCE SCOPE", rendered)
            self.assertIn("Publication approved:  False", rendered)

    def test_health_command_reports_no_recommendations_when_files_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CONTRIBUTING.md").write_text("# Contributions\n")
            (root / "SECURITY.md").write_text("# Security\n")
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(["health", str(root)])

            rendered = output.getvalue()

            self.assertEqual(result, 0)
            self.assertIn("Recommendations:  0", rendered)
            self.assertIn("No missing recommended files detected.", rendered)


if __name__ == "__main__":
    unittest.main()
