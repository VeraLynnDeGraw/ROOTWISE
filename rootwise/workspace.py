"""Workspace utilities for cloning and exploring project repositories."""

import shutil
import subprocess
from pathlib import Path
from rootwise.settings import require_network_access


IGNORED_DIRECTORIES = frozenset({
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
})


def build_tree_lines(
    path: str | Path = ".",
    *,
    include_all: bool = False,
    max_depth: int | None = None,
) -> list[str]:
    """Build a readable directory tree without changing project files."""
    root = Path(path).expanduser()

    if not root.exists():
        raise ValueError(f"Project path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Project path is not a directory: {root}")
    if max_depth is not None and max_depth < 1:
        raise ValueError("Maximum tree depth must be at least 1.")

    root = root.resolve()
    lines = [root.name or str(root)]

    def walk(directory: Path, prefix: str, depth: int) -> None:
        if max_depth is not None and depth >= max_depth:
            return

        entries = list(directory.iterdir())

        def is_directory(entry: Path) -> bool:
            return entry.is_dir() and not entry.is_symlink()

        entries.sort(
            key=lambda entry: (
                not is_directory(entry),
                entry.name.casefold(),
            )
        )

        visible = []
        for entry in entries:
            directory_entry = is_directory(entry)

            if not include_all:
                if directory_entry and (
                    entry.name in IGNORED_DIRECTORIES
                    or entry.name.endswith(".egg-info")
                ):
                    continue
                if entry.is_file() and entry.suffix == ".pyc":
                    continue

            visible.append(entry)

        for index, entry in enumerate(visible):
            last = index == len(visible) - 1
            connector = "└── " if last else "├── "
            is_dir = is_directory(entry)

            suffix = "/" if is_dir else "@" if entry.is_symlink() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")

            if is_dir:
                next_prefix = prefix + ("    " if last else "│   ")
                walk(entry, next_prefix, depth + 1)

    walk(root, "", 0)
    return lines


def clone_repository(
    repository: str,
    destination: str | Path,
) -> Path:
    """Clone a Git repository without replacing an existing destination."""
    url = repository.strip()
    if not url:
        raise ValueError("A Git repository URL or path is required.")

    require_network_access(url)

    git = shutil.which("git")
    if git is None:
        raise ValueError("Git is not installed or is not available on PATH.")

    target = Path(destination).expanduser().absolute()

    if target.exists() or target.is_symlink():
        raise ValueError(
            f"Destination already exists: {target}. "
            "Choose a new destination; ROOTWISE will not overwrite it."
        )

    if not target.parent.is_dir():
        raise ValueError(
            f"Destination parent directory does not exist: {target.parent}. "
            "Create or select an existing parent directory first."
        )

    result = subprocess.run(
        [git, "clone", "--", url, str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        message = detail or "Git did not provide an error description."
        raise ValueError(f"Git clone failed: {message}")

    return target
