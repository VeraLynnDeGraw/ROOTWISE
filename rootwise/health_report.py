"""Evidence-based repository health reports for ROOTWISE."""

from pathlib import Path

from rootwise.inspector import inspect_repository


def build_health_report(target: str | Path = ".") -> dict:
    """Build a health summary from existing repository inspection results."""
    inspection = inspect_repository(target)
    findings = inspection["findings"]

    summary = {
        "checks_run": inspection["checks_run"],
        "present": sum(
            item["status"] == "present" for item in findings
        ),
        "not_found": sum(
            item["status"] == "not_found" for item in findings
        ),
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
        "evidence_scope": {
            "inspection_performed": True,
            "tests_executed": False,
            "file_contents_validated": False,
            "publication_approved": False,
        },
        "limitations": list(inspection["limitations"]) + [
            "This report summarizes configured checks, not overall project quality.",
            "Test files may exist even when tests fail or have never been run.",
            "No publication or deployment decision is made by this report.",
        ],
    }
