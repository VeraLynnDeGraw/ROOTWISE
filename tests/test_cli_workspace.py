import subprocess
import tempfile
import unittest
from pathlib import Path

from rootwise.cli import main


class WorkspaceCliTests(unittest.TestCase):
    def test_tree_command_displays_project_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Example\\n")
            result = main(["tree", str(root)])
            self.assertEqual(result, 0)

    def test_tree_all_includes_generated_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".venv").mkdir()
            (root / ".venv" / "marker.txt").write_text("generated")
            result = main(["tree", str(root), "--all"])
            self.assertEqual(result, 0)

    def test_tree_invalid_path_returns_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            result = main(["tree", str(missing)])
            self.assertEqual(result, 1)

    def test_tree_hides_egg_info_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = root / "example.egg-info"
            metadata.mkdir()
            (metadata / "PKG-INFO").write_text("metadata")
            lines = __import__(
                "rootwise.workspace", fromlist=["build_tree_lines"]
            ).build_tree_lines(root)
            rendered = "\\n".join(lines)
            self.assertNotIn("example.egg-info", rendered)

    def test_clone_command_clones_local_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init", str(source)], check=True,
                           capture_output=True)
            (source / "README.md").write_text("# Clone test\\n")
            subprocess.run(
                ["git", "-C", str(source), "add", "README.md"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "-c", "user.name=ROOTWISE Test",
                 "-c", "user.email=rootwise-test@example.invalid",
                 "-C", str(source), "commit", "-m", "Initial commit"],
                check=True, capture_output=True,
            )

            destination = root / "cloned"
            result = main(["clone", str(source), str(destination)])
            self.assertEqual(result, 0)
            self.assertTrue((destination / "README.md").is_file())

    def test_clone_does_not_replace_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init", str(source)], check=True,
                           capture_output=True)
            destination = root / "existing"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("preserve")

            result = main(["clone", str(source), str(destination)])
            self.assertEqual(result, 1)
            self.assertEqual(marker.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
