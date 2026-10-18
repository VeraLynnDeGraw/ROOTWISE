"""Evidence-based repository health reports for ROOTWISE."""

from pathlib import Path

from rootwise.inspector import inspect_repository


RECOMMENDED_FILES = {
    "Contribution guidelines": "CONTRIBUTING.md",
    "Security policy": "SECURITY.md",
}


def build_health_report(target: str | Path = ".") -> dict:
    """Build a health summary from existing repository inspection results."""
    inspection = inspect_repository(target)
    findings = inspection["findings"]

    recommendations = [
        {
            "check": label,
            "path": path,
            "reason": f"Consider adding {path} to document this project practice.",
        }
        for label, path in RECOMMENDED_FILES.items()
        if any(
            item["check"] == label and item["status"] == "not_found"
            for item in findings
        )
    ]

    summary = {
        "checks_run": inspection["checks_run"],
        "present": sum(
            item["status"] == "present" for item in findings
        ),
        "not_found": sum(
            item["status"] == "not_found" for item in findings
        ),
        "recommendations": len(recommendations),
        "errors": sum(
            item["severity"] == "error" for item in findings
        ),
        "warnings": sum(
            item["severity"] == "warning" for item in findings
        ),
        "info": sum(
            item["severity"] == "info" for item in findings
        ),
    }

    return {
        "tool": inspection["tool"],
        "target": inspection["target"],
        "summary": summary,
        "findings": findings,
        "recommendations": recommendations,
        "evidence_scope": {
            "inspection_performed": True,
            "tests_executed": False,
            "file_contents_validated": False,
            "publication_approved": False,
        },
        "limitations": list(inspection["limitations"]) + [
            "This report summarizes configured checks, not overall project quality.",
            "Test files may exist even when tests fail or have never been run.",
            "Recommended files are guidance, not universal requirements.",
            "File presence does not establish the quality of its contents.",
            "No publication or deployment decision is made by this report.",
        ],
    }
