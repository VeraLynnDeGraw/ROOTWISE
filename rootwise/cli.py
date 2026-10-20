"""Command-line interface for ROOTWISE."""

import argparse
from pathlib import Path

from rootwise.cybergarden import Neon, neon_print, section
from rootwise.inspector import inspect_repository
from rootwise.health_report import build_health_report
from rootwise.menu import run_menu
from rootwise.sync_observer import observe_sync_candidates
from rootwise.snapshots import (
    create_snapshot,
    restore_snapshot,
    verify_snapshot,
)
from rootwise.workspace import build_tree_lines, clone_repository
from rootwise.handoff import build_handoff, save_handoff
from rootwise.settings import load_settings, save_settings


def _heading(title: str) -> None:
    """Display a consistently styled section heading."""
    section(title)


def _status(label: str, message: str, color: str) -> None:
    """Display a colored status label and message."""
    neon_print(f"[{label.upper()}] ", color, Neon.BOLD, end="")
    neon_print(message)


def _field(label: str, value: object) -> None:
    """Display a labeled value."""
    neon_print(f"  {label:<24}", Neon.CYAN, end="")
    neon_print(str(value), Neon.WHITE)


def _finding(status: str, title: str, evidence: str) -> None:
    """Display a finding using a color appropriate to its status."""
    normalized = status.lower().replace("_", " ")

    if normalized in {
        "present",
        "verified",
        "success",
        "valid",
        "complete",
        "completed",
        "healthy",
    }:
        color = Neon.LIME
    elif normalized in {
        "error",
        "failed",
        "unreadable",
        "blocked",
    }:
        color = Neon.RED
    elif normalized in {
        "not found",
        "empty",
        "warning",
        "unexpected type",
        "recommended",
        "review",
    }:
        color = Neon.AMBER
    else:
        color = Neon.CYAN

    _status(normalized, title, color)
    neon_print(f"  {evidence}", Neon.DIM)


def _value_color(label: str, value: object) -> str:
    """Choose a useful color for a boolean or count field."""
    key = label.lower().replace("_", " ").rstrip(":")

    if isinstance(value, bool):
        return Neon.LIME if value else Neon.AMBER

    if isinstance(value, (int, float)):
        if key in {"errors", "risk flags", "unreadable"}:
            return Neon.RED if value else Neon.LIME
        if key in {"warnings", "not found", "empty", "unexpected type"}:
            return Neon.AMBER if value else Neon.LIME
        return Neon.LIME if value else Neon.DIM

    return Neon.WHITE


def _summary_field(label: str, value: object) -> None:
    """Display a summary value with context-sensitive coloring."""
    if label in {"Recommendations:", "Publication approved:"}:
        # Preserve the existing CLI output contract for health-report tests.
        neon_print(f"  {label}  ", Neon.CYAN, end="")
    else:
        neon_print(f"  {label:<24}", Neon.CYAN, end="")

    neon_print(str(value), _value_color(label, value))


def _limitations(items: list[str]) -> None:
    """Display inspection limitations without hiding uncertainty."""
    _heading("LIMITATIONS")

    if not items:
        neon_print("No limitations reported.", Neon.LIME)
        return

    for item in items:
        neon_print(f"  • {item}", Neon.DIM)


def print_inspection(path: str) -> None:
    """Inspect a repository and display the findings."""
    report = inspect_repository(path)

    _heading("ROOTWISE REPOSITORY INSPECTION")
    _field("Repository:", report["target"])
    _summary_field("Checks run:", report["checks_run"])

    _heading("FINDINGS")
    for finding in report["findings"]:
        _finding(
            finding["status"],
            finding["check"],
            finding["evidence"],
        )

    _limitations(report["limitations"])


def build_parser() -> argparse.ArgumentParser:
    """Build the ROOTWISE command-line parser."""
    parser = argparse.ArgumentParser(
        prog="rootwise",
        description="Inspect repository foundations and preserve project files.",
        epilog=(
            "Run 'rootwise' or 'rootwise menu' to open the interactive menu. "
            "Colors are automatically disabled for non-interactive output, "
            "NO_COLOR, and TERM=dumb."
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a project repository.",
        description="Check repository foundations and report findings.",
    )
    inspect_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Create a project snapshot.",
        description="Create a preservation snapshot of a project.",
    )
    snapshot_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )
    snapshot_parser.add_argument(
        "--output",
        default=None,
        help="Snapshot output directory.",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a snapshot archive against its manifest.",
        description="Check snapshot integrity against its manifest.",
    )
    verify_parser.add_argument("archive", help="Snapshot archive path.")
    verify_parser.add_argument("manifest", help="Snapshot manifest path.")

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore a snapshot without overwriting existing files.",
        description=(
            "Restore files from a verified snapshot. Existing files are "
            "protected by the snapshot restoration safeguards."
        ),
    )
    restore_parser.add_argument("archive", help="Snapshot archive path.")
    restore_parser.add_argument("manifest", help="Snapshot manifest path.")
    restore_parser.add_argument(
        "destination",
        help="Directory into which the snapshot will be restored.",
    )
    restore_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive RESTORE confirmation prompt.",
    )

    observe_parser = subparsers.add_parser(
        "observe",
        help="Observe local Git changes without modifying the repository.",
        description=(
            "Report local Git changes and potential publication risks. "
            "This command observes; it does not synchronize or publish."
        ),
    )
    observe_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Git repository directory (default: current directory).",
    )

    health_parser = subparsers.add_parser(
        "health",
        help="Build an evidence-based repository health report.",
        description=(
            "Check repository structure and report evidence, recommendations, "
            "and limitations. This does not run tests or approve publication."
        ),
    )
    health_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    clone_parser = subparsers.add_parser(
        "clone",
        help="Clone a Git repository into a new destination.",
        description=(
            "Clone a Git repository without replacing an existing destination."
        ),
    )
    clone_parser.add_argument(
        "repository",
        help="Git repository URL or local repository path.",
    )
    clone_parser.add_argument(
        "destination",
        help="New destination path. It must not already exist.",
    )

    tree_parser = subparsers.add_parser(
        "tree",
        help="Display a project's directory tree.",
        description=(
            "Show project files and directories without executing project code."
        ),
    )
    tree_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )
    tree_parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="Include normally excluded directories and generated files.",
    )
    tree_parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Limit displayed directory depth (minimum: 1).",
    )

    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Prepare a local, recipient-neutral project handoff.",
        description=(
            "Build a reviewable Markdown handoff from project context "
            "and explicitly selected files. Does not execute project code "
            "or transmit the handoff."
        ),
    )
    handoff_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )
    handoff_parser.add_argument(
        "--task",
        required=True,
        help="Task, goal, or context to preserve in the handoff.",
    )
    handoff_parser.add_argument(
        "--file",
        action="append",
        default=[],
        dest="selected_files",
        help="Include a project-relative text file. May be repeated.",
    )
    handoff_parser.add_argument(
        "--output",
        default=None,
        help="Write Markdown to a new file instead of standard output.",
    )
    handoff_parser.add_argument(
        "--max-tree-depth",
        type=int,
        default=3,
        help="Maximum project-tree depth (default: 3).",
    )

    settings_parser = subparsers.add_parser(
        "settings",
        help="Display or change local operator settings.",
        description=(
            "Manage local color and network preferences. Changing network "
            "mode does not initiate a network connection."
        ),
    )
    settings_parser.add_argument(
        "--color", choices=("on", "off"),
        help="Enable or disable terminal color styling.",
    )
    settings_parser.add_argument(
        "--network", choices=("offline", "online"),
        help="Set the mode for explicitly requested remote operations.",
    )

    subparsers.add_parser(
        "menu",
        help="Open the interactive menu.",
        description="Launch the interactive CYBERGARDEN terminal interface.",
    )

    return parser


def _run_observe(path: str) -> int:
    """Display local Git observations."""
    report = observe_sync_candidates(path)

    _heading("ROOTWISE SYNC OBSERVER")
    _field("Repository:", report["repository"])
    _field("Branch:", report["branch"])

    remotes = report["remotes"]
    _field(
        "Remotes:",
        ", ".join(remotes) if remotes else "(none configured)",
    )
    _field("Publication:", report["publication_status"])

    summary = report["summary"]
    _heading("SUMMARY")

    summary_fields = (
        ("Changed files:", "changed_files"),
        ("Documents:", "documents"),
        ("Project configs:", "project_configs"),
        ("Licenses:", "licenses"),
        ("Source files:", "source_files"),
        ("Test files:", "test_files"),
        ("Other files:", "other_files"),
        ("Risk flags:", "risk_flags"),
    )

    for label, key in summary_fields:
        _summary_field(label, summary[key])

    _heading("CHANGES")

    if not report["findings"]:
        neon_print("No tracked or untracked changes detected.", Neon.LIME)

    for item in report["findings"]:
        status = item["status"].replace("_", " ").upper()
        title = f"{item['kind']:<12} {item['path']}"
        color = (
            Neon.AMBER
            if item["risk"]
            else Neon.CYAN
        )
        _status(status, title, color)

        if item["original_path"]:
            _field("Original path:", item["original_path"])

        if item["risk"]:
            _status("REVIEW WARNING", item["risk"], Neon.RED)

    _limitations(report["limitations"])
    return 0


def _run_health(path: str) -> int:
    """Display the repository health report."""
    report = build_health_report(path)
    summary = report["summary"]
    scope = report["evidence_scope"]

    _heading("ROOTWISE REPOSITORY HEALTH REPORT")
    _field("Repository:", report["target"])

    _heading("SUMMARY")

    summary_fields = (
        ("Checks performed:", "checks_run"),
        ("Items present:", "present"),
        ("Items not found:", "not_found"),
        ("Empty files:", "empty"),
        ("Unexpected type:", "unexpected_type"),
        ("Unreadable:", "unreadable"),
        ("Recommendations:", "recommendations"),
        ("Warnings:", "warnings"),
        ("Errors:", "errors"),
        ("Info findings:", "info"),
    )

    for label, key in summary_fields:
        _summary_field(label, summary[key])

    _heading("FINDINGS")
    for item in report["findings"]:
        _finding(
            item["status"],
            item["check"],
            f"Evidence: {item['evidence']}",
        )

    _heading("RECOMMENDATIONS")

    if report["recommendations"]:
        for item in report["recommendations"]:
            _finding(
                "recommended",
                f"{item['check']}: {item['path']}",
                f"Reason: {item['reason']}",
            )
    else:
        neon_print(
            "No missing recommended files detected.",
            Neon.LIME,
        )

    _heading("EVIDENCE SCOPE")

    scope_fields = (
        ("Inspection performed:", "inspection_performed"),
        ("Tests executed:", "tests_executed"),
        ("File contents checked:", "file_contents_validated"),
        ("Publication approved:", "publication_approved"),
    )

    for label, key in scope_fields:
        _summary_field(label, scope[key])

    _limitations(report["limitations"])
    return 0


def _run_snapshot(path: str, output: str | None) -> int:
    """Create a snapshot and display its recorded metadata."""
    if output is None:
        output = str(
            Path.home()
            / ".local"
            / "share"
            / "rootwise"
            / "snapshots"
        )

    result = create_snapshot(path, output)

    _heading("ROOTWISE SNAPSHOT")
    _status("SUCCESS", "Snapshot created.", Neon.LIME)
    _field("Archive:", result["archive"])
    _field("Manifest:", result["manifest"])
    _summary_field("Files:", result["file_count"])
    _field("SHA-256:", result["sha256"])
    return 0


def _run_verify(archive: str, manifest: str) -> int:
    """Verify snapshot integrity and return the appropriate status."""
    result = verify_snapshot(archive, manifest)

    _heading("ROOTWISE SNAPSHOT VERIFICATION")

    if result["valid"]:
        _status(
            "VERIFIED",
            "Snapshot integrity verified.",
            Neon.LIME,
        )
    else:
        _status(
            "FAILED",
            "Snapshot integrity check failed.",
            Neon.RED,
        )

    _field("Expected SHA-256:", result["expected_sha256"])
    _field("Actual SHA-256:", result["actual_sha256"])
    return 0 if result["valid"] else 1


def _run_restore(
    archive: str,
    manifest: str,
    destination: str,
    confirmed: bool,
) -> int:
    """Restore a snapshot using the existing confirmation safeguards."""
    try:
        verification = verify_snapshot(archive, manifest)
    except (ValueError, OSError) as error:
        _status(
            "ERROR",
            f"ROOTWISE error: {error}",
            Neon.RED,
        )
        return 1

    if not verification["valid"]:
        _status(
            "ERROR",
            "Snapshot integrity verification failed.",
            Neon.RED,
        )
        return 1

    if not confirmed:
        neon_print(
            "ROOTWISE will not overwrite existing files.",
            Neon.AMBER,
            Neon.BOLD,
        )

        prompt = Neon.paint(
            f"Type RESTORE to proceed into {destination}: ",
            Neon.CYAN,
            Neon.BOLD,
        )
        confirmation = input(prompt).strip()

        if confirmation != "RESTORE":
            _status(
                "CANCELLED",
                "Restore cancelled.",
                Neon.AMBER,
            )
            return 1

    result = restore_snapshot(
        archive,
        manifest,
        destination,
    )

    _heading("ROOTWISE RESTORE")
    _status("SUCCESS", "Restore completed.", Neon.LIME)
    _field("Destination:", result["destination"])
    _summary_field("Files restored:", result["file_count"])
    return 0


def _run_settings(
    color: str | None = None,
    network: str | None = None,
) -> int:
    """Display or update persistent local operator settings."""
    current = load_settings()

    if color is not None:
        current["color_enabled"] = color == "on"
    if network is not None:
        current["network_mode"] = network

    if color is not None or network is not None:
        destination = save_settings(current)
        print(f"Settings saved locally: {destination}")

    current = load_settings()
    print("\nROOTWISE OPERATOR SETTINGS")
    print("--------------------------")
    print(f"Color styling: {'ON' if current['color_enabled'] else 'OFF'}")
    print(f"Network mode:  {current['network_mode'].upper()}")
    print("Network access occurs only for explicitly requested operations.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run a ROOTWISE command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command in (None, "menu"):
            run_menu()
            return 0

        if args.command == "settings":
            return _run_settings(args.color, args.network)

        if args.command == "observe":
            return _run_observe(args.path)

        if args.command == "clone":
            target = clone_repository(args.repository, args.destination)
            _heading("ROOTWISE REPOSITORY CLONE")
            _status("SUCCESS", "Repository cloned.", Neon.LIME)
            _field("Source:", args.repository)
            _field("Destination:", target)
            return 0

        if args.command == "tree":
            lines = build_tree_lines(
                args.path,
                include_all=args.show_all,
                max_depth=args.max_depth,
            )
            _heading("ROOTWISE PROJECT TREE")
            for index, tree_line in enumerate(lines):
                color = Neon.LIME if index == 0 else Neon.CYAN
                neon_print(tree_line, color)
            return 0

        if args.command == "handoff":
            content = build_handoff(
                project_path=args.path,
                task=args.task,
                selected_files=args.selected_files,
                max_tree_depth=args.max_tree_depth,
            )
            if args.output:
                destination = save_handoff(content, args.output)
                print(f"Handoff saved locally: {destination}")
            else:
                print(content, end="")
            return 0

        if args.command == "inspect":
            print_inspection(args.path)
            return 0

        if args.command == "health":
            return _run_health(args.path)

        if args.command == "snapshot":
            return _run_snapshot(args.path, args.output)

        if args.command == "verify":
            return _run_verify(args.archive, args.manifest)

        if args.command == "restore":
            return _run_restore(
                args.archive,
                args.manifest,
                args.destination,
                args.yes,
            )

    except (ValueError, OSError) as error:
        _status("ERROR", f"ROOTWISE error: {error}", Neon.RED)
        return 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
