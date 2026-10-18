
"""Read-only repository inspection for ROOTWISE."""

from pathlib import Path


def inspect_repository(target: str | Path) -> dict:
    """Inspect a repository and return structured findings."""
    root = Path(target).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Target does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {root}")

    findings = []

    def check(path: str, label: str, importance: str = "info") -> None:
        if (root / path).exists():
            findings.append({
                "check": label,
                "status": "present",
                "severity": "info",
                "evidence": f"Found {path}",
            })
        else:
            findings.append({
                "check": label,
                "status": "not_found",
                "severity": importance,
                "evidence": f"No {path} found at the repository root",
            })

    check("README.md", "Project documentation", "warning")
    check("LICENSE", "License file", "warning")
    check(".git", "Git metadata", "warning")
    check(".gitignore", "Ignore rules")
    check("CONTRIBUTING.md", "Contribution guidelines")
    check("SECURITY.md", "Security policy")
    check("pyproject.toml", "Python project configuration")
    check("tests", "Test directory")

    return {
        "tool": "ROOTWISE",
        "target": str(root),
        "checks_run": len(findings),
        "findings": findings,
        "limitations": [
            "Presence checks do not validate file contents.",
            "A missing file is not proof that a project is defective.",
            "This initial inspector does not execute project code.",
        ],
    }
