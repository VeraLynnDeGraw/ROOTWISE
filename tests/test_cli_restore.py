import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rootwise.cli import main
from rootwise.snapshots import create_snapshot


class RestoreCommandTests(unittest.TestCase):
    def make_snapshot(self, base: Path) -> dict:
        project = base / "project"
        output = base / "snapshots"
        project.mkdir()
        (project / "README.md").write_text("# Preserved project\n")

        return create_snapshot(project, output)

    def test_declining_confirmation_cancels_without_writing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            snapshot = self.make_snapshot(base)
            destination = base / "restored"
            output = io.StringIO()

            with (
                patch("builtins.input", return_value="no") as prompt,
                contextlib.redirect_stdout(output),
            ):
                result = main([
                    "restore",
                    snapshot["archive"],
                    snapshot["manifest"],
                    str(destination),
                ])

            self.assertEqual(result, 1)
            self.assertTrue(prompt.called)
            self.assertIn("Restore cancelled.", output.getvalue())
            self.assertFalse(destination.exists())

    def test_invalid_manifest_is_rejected_without_restoring_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            snapshot = self.make_snapshot(base)
            destination = base / "restored"

            manifest_path = Path(snapshot["manifest"])
            manifest = json.loads(manifest_path.read_text())
            manifest["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest))

            output = io.StringIO()

            with (
                patch("builtins.input", return_value="RESTORE") as prompt,
                contextlib.redirect_stdout(output),
            ):
                result = main([
                    "restore",
                    snapshot["archive"],
                    snapshot["manifest"],
                    str(destination),
                ])

            self.assertEqual(result, 1)
            prompt.assert_not_called()
            self.assertIn("integrity verification", output.getvalue())
            self.assertFalse(destination.exists())

    def test_yes_restores_valid_snapshot_without_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            snapshot = self.make_snapshot(base)
            destination = base / "restored"
            output = io.StringIO()

            with (
                patch("builtins.input") as prompt,
                contextlib.redirect_stdout(output),
            ):
                result = main([
                    "restore",
                    snapshot["archive"],
                    snapshot["manifest"],
                    str(destination),
                    "--yes",
                ])

            self.assertEqual(result, 0)
            prompt.assert_not_called()
            self.assertEqual(
                (destination / "README.md").read_text(),
                "# Preserved project\n",
            )
            self.assertIn("Restore completed.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
