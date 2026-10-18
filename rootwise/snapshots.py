
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def _should_exclude(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True

    if path.name == ".env" or path.name.startswith(".env."):
        return True

    return False


def create_snapshot(project_path, output_dir) -> dict:
    project = Path(project_path).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()

    if not project.is_dir():
        raise ValueError("Project path must be an existing directory.")

    if output == project or project in output.parents:
        raise ValueError(
            "Snapshot output must be outside the project directory."
        )

    output.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"{project.name}_{timestamp}"
    archive = output / f"{base_name}.tar.gz"
    manifest_path = output / f"{base_name}.manifest.json"
    counter = 1

    while archive.exists() or manifest_path.exists():
        base_name = f"{project.name}_{timestamp}_{counter}"
        archive = output / f"{base_name}.tar.gz"
        manifest_path = output / f"{base_name}.manifest.json"
        counter += 1

    files = sorted(
        path
        for path in project.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not _should_exclude(path.relative_to(project))
    )

    try:
        with tarfile.open(archive, "x:gz") as bundle:
            for path in files:
                bundle.add(path, arcname=path.relative_to(project))

        digest = hashlib.sha256(archive.read_bytes()).hexdigest()

        manifest = {
            "project": project.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "archive": archive.name,
            "sha256": digest,
            "file_count": len(files),
            "files": [
                str(path.relative_to(project)) for path in files
            ],
        }

        with manifest_path.open("x", encoding="utf-8") as manifest_file:
            json.dump(manifest, manifest_file, indent=2)
            manifest_file.write("\n")

    except Exception:
        archive.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise

    return {
        "archive": str(archive),
        "manifest": str(manifest_path),
        "file_count": len(files),
        "sha256": digest,
    }


def verify_snapshot(archive_path, manifest_path) -> dict:
    archive = Path(archive_path).expanduser().resolve()
    manifest_file = Path(manifest_path).expanduser().resolve()

    if not archive.is_file():
        raise ValueError("Snapshot archive does not exist.")

    if not manifest_file.is_file():
        raise ValueError("Snapshot manifest does not exist.")

    try:
        manifest = json.loads(
            manifest_file.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Snapshot manifest is not valid JSON.") from error

    if not isinstance(manifest, dict):
        raise ValueError("Snapshot manifest must contain a JSON object.")

    expected_hash = manifest.get("sha256")

    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or any(
            char not in "0123456789abcdef"
            for char in expected_hash
        )
    ):
        raise ValueError("Manifest does not contain a valid SHA-256 hash.")

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    return {
        "valid": digest == expected_hash,
        "expected_sha256": expected_hash,
        "actual_sha256": digest,
    }


def restore_snapshot(archive_path, manifest_path, destination) -> dict:
    archive = Path(archive_path).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()

    verification = verify_snapshot(archive, manifest_path)

    if not verification["valid"]:
        raise ValueError("Snapshot archive failed integrity verification.")

    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
    except (tarfile.TarError, OSError) as error:
        raise ValueError("Snapshot archive cannot be read.") from error

    # Validate every archive entry before writing anything.
    checked_members = []
    seen_paths = set()
    file_paths = set()

    for member in members:
        relative = PurePosixPath(member.name)

        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or "\x00" in member.name
        ):
            raise ValueError("Snapshot contains an unsafe archive path.")

        if not (member.isfile() or member.isdir()):
            raise ValueError(
                "Snapshot contains an unsupported file type."
            )

        normalized = relative.as_posix()

        if normalized in seen_paths:
            raise ValueError("Snapshot contains duplicate archive paths.")

        seen_paths.add(normalized)

        target = destination.joinpath(*relative.parts)
        resolved_target = target.resolve()

        if (
            resolved_target == destination
            or destination not in resolved_target.parents
        ):
            raise ValueError("Snapshot path escapes the restore directory.")

        if member.isfile():
            file_paths.add(normalized)

        checked_members.append((member, relative, target))

    # Reject an archive that treats a file as a parent directory.
    for _, relative, _ in checked_members:
        for parent in relative.parents:
            if parent.as_posix() in file_paths:
                raise ValueError(
                    "Snapshot contains conflicting file paths."
                )

    # Preflight existing targets before creating or writing anything.
    for member, _, target in checked_members:
        if target.is_symlink():
            raise ValueError(
                "Restore destination contains a symbolic link."
            )

        if member.isfile() and target.exists():
            raise FileExistsError(
                f"Restore would overwrite an existing file: {target}"
            )

        if member.isdir() and target.exists() and not target.is_dir():
            raise FileExistsError(
                f"Restore directory conflicts with an existing path: {target}"
            )

    destination.mkdir(parents=True, exist_ok=True)

    created_files = []
    created_dirs = []

    def ensure_directory(directory: Path) -> None:
        missing = []

        current = directory
        while current != destination and not current.exists():
            missing.append(current)
            current = current.parent

        for path in reversed(missing):
            path.mkdir()
            created_dirs.append(path)

    try:
        with tarfile.open(archive, "r:gz") as bundle:
            for member, relative, target in checked_members:
                if member.isdir():
                    ensure_directory(target)
                    continue

                ensure_directory(target.parent)

                # Exclusive creation prevents overwriting a file.
                source = bundle.extractfile(member)
                if source is None:
                    raise ValueError(
                        "Snapshot contains a file that cannot be read."
                    )

                with source, target.open("xb") as output_file:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        output_file.write(chunk)

                created_files.append(target)

    except Exception:
        # Remove only files and empty directories created by this restore.
        for path in reversed(created_files):
            path.unlink(missing_ok=True)

        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass

        raise

    restored_files = [
        str(target)
        for member, _, target in checked_members
        if member.isfile()
    ]

    return {
        "destination": str(destination),
        "file_count": len(restored_files),
        "restored_files": restored_files,
    }
