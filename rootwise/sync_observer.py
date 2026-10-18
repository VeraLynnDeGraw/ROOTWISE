"""Read-only observation of local Git changes for ROOTWISE."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


DOCUMENT_SUFFIXES = {
    ".md", ".mdx", ".rst", ".txt", ".adoc", ".org",
}

SENSITIVE_NAME_PARTS = {
    ".env",
    "secret",
    "credential",
    "password",
    "token",
    "private_key",
    "private-key",
    "id_rsa",
    "id_ed25519",
}

SENSITIVE_SUFFIXES = {
    ".pem", ".p12", ".pfx", ".key",
}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a read-only Git query and return its result."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _status_label(code: str) -> str:
    if code == "??":
        return "untracked"
    if "U" in code or code == "AA" or code == "DD":
        return "conflicted"
    if "R" in code:
        return "renamed"
    if "D" in code:
        return "deleted"
    if "A" in code:
        return "added"
    return "modified"


def _sensitivity(path: str) -> str | None:
    candidate = Path(path)
    name = candidate.name.lower()

    if name in {".env", ".env.local", ".env.production"}:
        return "Sensitive-looking filename; inspect before publication."

    if any(part in name for part in SENSITIVE_NAME_PARTS):
        return "Filename may indicate credentials or private data."

    if candidate.suffix.lower() in SENSITIVE_SUFFIXES:
        return "Potential key or certificate file; inspect before publication."

    return None


def _parse_status(output: str) -> list[dict[str, Any]]:
    """Parse Git's NUL-delimited porcelain status, including renames."""
    fields = output.split("\0")
    findings: list[dict[str, Any]] = []
    index = 0

    while index < len(fields):
        entry = fields[index]
        index += 1

        if not entry:
            continue

        if len(entry) < 4:
            continue

        code = entry[:2]
        path = entry[3:]

        # With porcelain -z, rename/copy entries include the original
        # path as the next NUL-delimited field.
        original_path = None
        if "R" in code or "C" in code:
            if index < len(fields):
                original_path = fields[index] or None
                index += 1

        label = _status_label(code)
        sensitivity = _sensitivity(path)
        suffix = Path(path).suffix.lower()
        is_document = suffix in DOCUMENT_SUFFIXES

        findings.append(
            {
                "path": path,
                "status_code": code,
                "status": label,
                "kind": "document" if is_document else "other_file",
                "original_path": original_path,
                "review_required": True,
                "risk": sensitivity,
            }
        )

    return findings


def observe_sync_candidates(project_path: str | Path = ".") -> dict[str, Any]:
    """Report local Git changes without modifying the repository."""
    requested_path = Path(project_path).expanduser().resolve()

    top_level = _git(requested_path, "rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        raise ValueError(
            f"Not inside a Git repository: {requested_path}"
        )

    root = Path(top_level.stdout.strip()).resolve()

    status = _git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    if status.returncode != 0:
        raise OSError(status.stderr.strip() or "Could not inspect Git status.")

    branch = _git(root, "branch", "--show-current")
    remotes = _git(root, "remote")

    if branch.returncode != 0 or remotes.returncode != 0:
        raise OSError("Could not read the repository branch or remotes.")

    findings = _parse_status(status.stdout)
    risks = [item for item in findings if item["risk"]]

    return {
        "repository": str(root),
        "branch": branch.stdout.strip() or "(detached HEAD)",
        "remotes": [
            line.strip()
            for line in remotes.stdout.splitlines()
            if line.strip()
        ],
        "findings": findings,
        "summary": {
            "changed_files": len(findings),
            "documents": sum(
                item["kind"] == "document" for item in findings
            ),
            "other_files": sum(
                item["kind"] == "other_file" for item in findings
            ),
            "risk_flags": len(risks),
            "review_required": len(findings),
        },
        "publication_status": "REVIEW_REQUIRED",
        "limitations": [
            "This is a local Git status report, not a publication approval.",
            "Ignored files are not included in the candidate list.",
            "Filename checks cannot establish whether file contents contain secrets.",
            "Remote configuration does not establish whether GitHub is reachable.",
            "No files were staged, committed, uploaded, or modified.",
        ],
    }
