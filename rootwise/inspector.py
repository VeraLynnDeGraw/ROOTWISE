"""Read-only repository inspection for ROOTWISE."""

from pathlib import Path


def inspect_repository(target: str | Path) -> dict:
    """Inspect repository structure and perform limited documentation checks."""
    root = Path(target).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Target does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {root}")

    findings = []

    def check(
        path: str,
        label: str,
        importance: str = "info",
        expected_type: str = "file",
        inspect_content: bool = False,
    ) -> None:
        candidate = root / path

        if not candidate.exists():
            findings.append({
                "check": label,
                "status": "not_found",
                "severity": importance,
                "evidence": f"No {path} found at the repository root",
            })
            return

        if expected_type == "directory":
            correct_type = candidate.is_dir()
        else:
            correct_type = candidate.is_file()

        if not correct_type:
            actual_type = "directory" if candidate.is_dir() else "not a regular file"
            findings.append({
                "check": label,
                "status": "unexpected_type",
                "severity": importance,
                "evidence": (
                    f"Expected {path} to be a {expected_type}; "
                    f"found {actual_type}"
                ),
            })
            return

        if inspect_content:
            try:
                with candidate.open("r", encoding="utf-8") as file:
                    has_content = any(line.strip() for line in file)
            except (OSError, UnicodeError):
                findings.append({
                    "check": label,
                    "status": "unreadable",
                    "severity": importance,
                    "evidence": (
                        f"Found {path}, but its text content could not "
                        "be inspected"
                    ),
                })
                return

            if not has_content:
                findings.append({
                    "check": label,
                    "status": "empty",
                    "severity": "info",
                    "evidence": (
                        f"Found {path}, but the file is empty or contains only whitespace"
                    ),
                })
                return

        findings.append({
            "check": label,
            "status": "present",
            "severity": "info",
            "evidence": f"Found {path}",
        })

    check(
        "README.md",
        "Project documentation",
        "warning",
        inspect_content=True,
    )
    check(
        "LICENSE",
        "License file",
        "warning",
        inspect_content=True,
    )
    check(".git", "Git metadata", "warning", expected_type="directory")
    check(".gitignore", "Ignore rules")
    check("CONTRIBUTING.md", "Contribution guidelines")
    check("SECURITY.md", "Security policy")
    check("pyproject.toml", "Python project configuration")
    check("tests", "Test directory", expected_type="directory")

    return {
        "tool": "ROOTWISE",
        "target": str(root),
        "checks_run": len(findings),
        "findings": findings,
        "limitations": [
            "README.md and LICENSE are checked only for non-whitespace text; their quality and correctness are not validated.",
            "Other checks examine path presence and expected type, not file contents.",
            "A missing or empty file is not proof that a project is defective.",
            "This inspector does not execute project code or run tests.",
        ],
    }
