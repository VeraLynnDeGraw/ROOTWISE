import subprocess
import tempfile
import unittest
from pathlib import Path

from rootwise.workspace import build_tree_lines, clone_repository


class WorkspaceTreeTests(unittest.TestCase):
    def test_tree_lists_project_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Example\n")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("pass\n")

            output = "\n".join(build_tree_lines(root))

            self.assertIn("README.md", output)
            self.assertIn("src/", output)
            self.assertIn("app.py", output)

    def test_tree_excludes_generated_directories_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            for name in (".git", ".venv", "__pycache__", "node_modules"):
                directory = root / name
                directory.mkdir()
                (directory / "hidden.txt").write_text("generated\n")

            output = "\n".join(build_tree_lines(root))

            for name in (".git/", ".venv/", "__pycache__/", "node_modules/"):
                self.assertNotIn(name, output)

    def test_tree_all_includes_excluded_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".venv").mkdir()
            (root / ".venv" / "marker.txt").write_text("present\n")

            output = "\n".join(build_tree_lines(root, include_all=True))

            self.assertIn(".venv/", output)
            self.assertIn("marker.txt", output)

    def test_tree_depth_limit_hides_nested_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "first").mkdir()
            (root / "first" / "second").mkdir()
            (root / "first" / "second" / "deep.txt").write_text("deep\n")

            output = "\n".join(build_tree_lines(root, max_depth=1))

            self.assertIn("first/", output)
            self.assertNotIn("deep.txt", output)

    def test_tree_rejects_missing_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"

            with self.assertRaises(ValueError):
                build_tree_lines(missing)

    def test_tree_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            file_path = Path(temporary) / "file.txt"
            file_path.write_text("not a directory\n")

            with self.assertRaises(ValueError):
                build_tree_lines(file_path)

    def test_tree_rejects_invalid_depth(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                build_tree_lines(temporary, max_depth=0)


class WorkspaceCloneTests(unittest.TestCase):
    def test_clones_local_git_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()

            subprocess.run(
                ["git", "init", str(source)],
                check=True,
                capture_output=True,
                text=True,
            )
            (source / "README.md").write_text("# Clone test\n")

            subprocess.run(
                ["git", "-C", str(source), "add", "README.md"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(source),
                    "-c", "user.name=ROOTWISE Test",
                    "-c", "user.email=rootwise-test@example.invalid",
                    "commit", "-m", "Add clone test README",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            result = clone_repository(str(source), destination)

            self.assertEqual(result, destination.resolve())
            self.assertTrue((destination / ".git").exists())
            self.assertEqual(
                (destination / "README.md").read_text(),
                "# Clone test\n",
            )

    def test_clone_refuses_existing_destination_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "existing"
            destination.mkdir()
            sentinel = destination / "keep.txt"
            sentinel.write_text("hands off\n")

            with self.assertRaises(ValueError):
                clone_repository("not-a-real-repository", destination)

            self.assertEqual(sentinel.read_text(), "hands off\n")

    def test_clone_rejects_missing_destination_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "missing" / "destination"

            with self.assertRaises(ValueError):
                clone_repository("not-a-real-repository", destination)

    def test_clone_rejects_empty_repository_argument(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "destination"

            with self.assertRaises(ValueError):
                clone_repository("   ", destination)


if __name__ == "__main__":
    unittest.main()
