
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from rootwise.snapshots import (
    create_snapshot,
    restore_snapshot,
    verify_snapshot,
)


class SnapshotTests(unittest.TestCase):
    def test_creates_archive_without_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()

            original = project / "README.md"
            original.write_text("# Example project\n")

            result = create_snapshot(project, output)

            self.assertTrue(Path(result["archive"]).is_file())
            self.assertTrue(Path(result["manifest"]).is_file())
            self.assertEqual(result["file_count"], 1)
            self.assertEqual(original.read_text(), "# Example project\n")

    def test_excludes_secrets_and_git_internals(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()

            (project / "README.md").write_text("# Example\n")
            (project / ".env").write_text("SECRET=do-not-archive\n")
            (project / ".env.local").write_text("TOKEN=do-not-archive\n")

            git_dir = project / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("[core]\n")

            result = create_snapshot(project, output)

            with tarfile.open(result["archive"], "r:gz") as bundle:
                names = bundle.getnames()

            self.assertIn("README.md", names)
            self.assertNotIn(".env", names)
            self.assertNotIn(".env.local", names)
            self.assertNotIn(".git/config", names)
            self.assertEqual(result["file_count"], 1)

    def test_excludes_files_inside_env_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()

            (project / "README.md").write_text("# Example\n")
            env_dir = project / ".env"
            env_dir.mkdir()
            (env_dir / "secrets.txt").write_text("PRIVATE=1\n")

            result = create_snapshot(project, output)

            with tarfile.open(result["archive"], "r:gz") as bundle:
                names = bundle.getnames()

            self.assertIn("README.md", names)
            self.assertFalse(
                any(name.startswith(".env/") for name in names)
            )
            self.assertEqual(result["file_count"], 1)

    def test_verifies_unchanged_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            verification = verify_snapshot(
                result["archive"],
                result["manifest"],
            )

            self.assertTrue(verification["valid"])
            self.assertEqual(
                verification["expected_sha256"],
                verification["actual_sha256"],
            )

    def test_rejects_manifest_for_different_archive_name(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["archive"] = "different-archive.tar.gz"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                verify_snapshot(result["archive"], result["manifest"])

    def test_rejects_inconsistent_manifest_file_count(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["file_count"] = 99
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                verify_snapshot(result["archive"], result["manifest"])

    def test_rejects_manifest_with_non_list_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"] = "README.md"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                verify_snapshot(result["archive"], result["manifest"])

    def test_rejects_manifest_with_duplicate_file_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"] = ["README.md", "README.md"]
            manifest["file_count"] = 2
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                verify_snapshot(result["archive"], result["manifest"])

    def test_rejects_manifest_that_disagrees_with_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\\n")

            result = create_snapshot(project, output)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )

            # Keep the count and archive hash valid while lying about the file.
            manifest["files"] = ["different.txt"]
            manifest_path.write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "file list does not match archive contents",
            ):
                verify_snapshot(result["archive"], result["manifest"])

    def test_detects_modified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)

            with open(result["archive"], "ab") as archive:
                archive.write(b"modified")

            verification = verify_snapshot(
                result["archive"],
                result["manifest"],
            )
            self.assertFalse(verification["valid"])

    def test_rejects_invalid_manifest_json(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()
            (project / "README.md").write_text("# Example\n")

            result = create_snapshot(project, output)
            Path(result["manifest"]).write_text(
                "{not valid JSON",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                verify_snapshot(result["archive"], result["manifest"])

    def test_preserves_multiple_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            project.mkdir()

            source_file = project / "README.md"
            source_file.write_text("Version one\n")

            first = create_snapshot(project, output)
            first_archive = Path(first["archive"])
            first_bytes = first_archive.read_bytes()

            source_file.write_text("Version two\n")
            second = create_snapshot(project, output)

            self.assertNotEqual(first["archive"], second["archive"])
            self.assertTrue(first_archive.is_file())
            self.assertEqual(first_archive.read_bytes(), first_bytes)
            self.assertTrue(Path(second["archive"]).is_file())

            self.assertTrue(
                verify_snapshot(first["archive"], first["manifest"])["valid"]
            )
            self.assertTrue(
                verify_snapshot(second["archive"], second["manifest"])["valid"]
            )

    def test_restores_snapshot_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            destination = base / "restored"
            project.mkdir()

            (project / "README.md").write_text("# ROOTWISE\n")
            (project / "src").mkdir()
            (project / "src" / "main.py").write_text("print('hello')\n")

            result = create_snapshot(project, output)
            restored = restore_snapshot(
                result["archive"],
                result["manifest"],
                destination,
            )

            self.assertEqual(restored["file_count"], 2)
            self.assertEqual(
                (destination / "README.md").read_text(),
                "# ROOTWISE\n",
            )
            self.assertEqual(
                (destination / "src" / "main.py").read_text(),
                "print('hello')\n",
            )

    def test_restore_rejects_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            destination = base / "restored"
            project.mkdir()
            destination.mkdir()

            (project / "README.md").write_text("Original\n")
            result = create_snapshot(project, output)

            existing = destination / "README.md"
            existing.write_text("Keep this file\n")

            with self.assertRaises(FileExistsError):
                restore_snapshot(
                    result["archive"],
                    result["manifest"],
                    destination,
                )

            self.assertEqual(existing.read_text(), "Keep this file\n")

    def test_restore_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "unsafe.tar.gz"
            manifest_path = base / "unsafe.manifest.json"
            destination = base / "restored"
            destination.mkdir()

            with tarfile.open(archive, "w:gz") as bundle:
                data = b"unsafe\n"
                info = tarfile.TarInfo("../../outside.txt")
                info.size = len(data)
                bundle.addfile(info, io.BytesIO(data))

            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = {
                "archive": archive.name,
                "sha256": digest,
                "file_count": 1,
                "files": ["../../outside.txt"],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                restore_snapshot(archive, manifest_path, destination)

            self.assertFalse((base / "outside.txt").exists())
            self.assertFalse((destination.parent / "outside.txt").exists())

    def test_restore_rejects_symbolic_link_members(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "symlink.tar.gz"
            manifest_path = base / "symlink.manifest.json"
            destination = base / "restored"
            destination.mkdir()

            with tarfile.open(archive, "w:gz") as bundle:
                info = tarfile.TarInfo("linked-file")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside.txt"
                bundle.addfile(info)

            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = {
                "archive": archive.name,
                "sha256": digest,
                "file_count": 1,
                "files": ["linked-file"],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                restore_snapshot(archive, manifest_path, destination)

            self.assertFalse((base / "outside.txt").exists())

    def test_restore_does_not_overwrite_sentinel(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            output = base / "snapshots"
            destination = base / "restored"
            project.mkdir()
            destination.mkdir()

            (project / "README.md").write_text("# ROOTWISE\n")
            result = create_snapshot(project, output)

            sentinel = destination / "README.md"
            sentinel.write_text("DO NOT OVERWRITE\n")
            before = hashlib.sha256(sentinel.read_bytes()).hexdigest()

            with self.assertRaises(FileExistsError):
                restore_snapshot(
                    result["archive"],
                    result["manifest"],
                    destination,
                )

            after = hashlib.sha256(sentinel.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertEqual(sentinel.read_text(), "DO NOT OVERWRITE\n")

    def test_restore_rejects_file_parent_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "collision.tar.gz"
            manifest_path = base / "collision.manifest.json"
            destination = base / "restored"
            destination.mkdir()

            with tarfile.open(archive, "w:gz") as bundle:
                data = b"file\n"
                info = tarfile.TarInfo("folder")
                info.size = len(data)
                bundle.addfile(info, io.BytesIO(data))

                nested_data = b"nested\n"
                nested = tarfile.TarInfo("folder/child.txt")
                nested.size = len(nested_data)
                bundle.addfile(nested, io.BytesIO(nested_data))

            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = {
                "archive": archive.name,
                "sha256": digest,
                "file_count": 2,
                "files": ["folder", "folder/child.txt"],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                restore_snapshot(archive, manifest_path, destination)

            self.assertFalse((destination / "folder").exists())


if __name__ == "__main__":
    unittest.main()
