
"""Command-line interface for ROOTWISE."""

import argparse
import sys

from rootwise.inspector import inspect_repository
from rootwise.health_report import build_health_report
from rootwise.menu import run_menu
from rootwise.sync_observer import observe_sync_candidates

from rootwise.snapshots import (
    create_snapshot,
    restore_snapshot,
    verify_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rootwise",
        description="Inspect repository foundations and preserve project files.",
    )

    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a project repository.",
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
    )
    verify_parser.add_argument("archive")
    verify_parser.add_argument("manifest")

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore a snapshot without overwriting existing files.",
    )
    restore_parser.add_argument("archive")
    restore_parser.add_argument("manifest")
    restore_parser.add_argument("destination")
    restore_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm restoration without an interactive prompt.",
    )

    observe_parser = subparsers.add_parser(
        "observe",
        help="Observe local Git changes without modifying the repository.",
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
    )
    health_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    subparsers.add_parser("menu", help="Open the interactive menu.")

    return parser


def print_inspection(path: str) -> None:
    report = inspect_repository(path)

    print(f"ROOTWISE inspection: {report['target']}")
    print(f"Checks run: {report['checks_run']}\n")

    for finding in report["findings"]:
        status = finding["status"].replace("_", " ").upper()
        print(f"[{status}] {finding['check']}")
        print(f"  {finding['evidence']}")

    print("\nLimitations:")
    for limitation in report["limitations"]:
        print(f"  - {limitation}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command in (None, "menu"):
            run_menu()
            return 0

        if args.command == "observe":
            report = observe_sync_candidates(args.path)

            print("ROOTWISE SYNC OBSERVER")
            print(f"Repository: {report['repository']}")
            print(f"Branch:     {report['branch']}")
            remotes = report["remotes"]
            print(f"Remotes:    {', '.join(remotes) if remotes else '(none configured)'}")
            print(f"Publication: {report['publication_status']}")

            summary = report["summary"]
            print("\nSUMMARY")
            print(f"Changed files:   {summary['changed_files']}")
            print(f"Documents:       {summary['documents']}")
            print(f"Project configs: {summary['project_configs']}")
            print(f"Licenses:        {summary['licenses']}")
            print(f"Source files:    {summary['source_files']}")
            print(f"Test files:      {summary['test_files']}")
            print(f"Other files:     {summary['other_files']}")
            print(f"Risk flags:      {summary['risk_flags']}")

            print("\nCHANGES")
            if not report["findings"]:
                print("No tracked or untracked changes detected.")
            for item in report["findings"]:
                print(
                    f"[{item['status'].upper():10}] "
                    f"{item['kind']:12} {item['path']}"
                )
                if item["original_path"]:
                    print(f"  Original path: {item['original_path']}")
                if item["risk"]:
                    print(f"  REVIEW WARNING: {item['risk']}")

            print("\nLIMITATIONS")
            for limitation in report["limitations"]:
                print(f"- {limitation}")
            return 0

        if args.command == "inspect":
            print_inspection(args.path)
            return 0

        if args.command == "health":
            report = build_health_report(args.path)
            summary = report["summary"]
            scope = report["evidence_scope"]

            print("ROOTWISE REPOSITORY HEALTH REPORT")
            print(f"Repository: {report['target']}")
            print("\nSUMMARY")
            print(f"Checks performed: {summary['checks_run']}")
            print(f"Items present:    {summary['present']}")
            print(f"Items not found:  {summary['not_found']}")
            print(f"Warnings:         {summary['warnings']}")
            print(f"Errors:           {summary['errors']}")
            print(f"Info findings:    {summary['info']}")

            print("\nFINDINGS")
            for item in report["findings"]:
                status = item["status"].replace("_", " ").upper()
                print(f"[{status}] {item['check']}")
                print(f"  Evidence: {item['evidence']}")

            print("\nEVIDENCE SCOPE")
            print(f"Inspection performed: {scope['inspection_performed']}")
            print(f"Tests executed:        {scope['tests_executed']}")
            print(f"File contents checked: {scope['file_contents_validated']}")
            print(f"Publication approved:  {scope['publication_approved']}")

            print("\nLIMITATIONS")
            for limitation in report["limitations"]:
                print(f"- {limitation}")
            return 0

        if args.command == "snapshot":
            from pathlib import Path

            output = args.output
            if output is None:
                output = str(
                    Path.home()
                    / ".local"
                    / "share"
                    / "rootwise"
                    / "snapshots"
                )

            result = create_snapshot(args.path, output)
            print("Snapshot created.")
            print(f"Archive:  {result['archive']}")
            print(f"Manifest: {result['manifest']}")
            print(f"Files:    {result['file_count']}")
            print(f"SHA-256:  {result['sha256']}")
            return 0

        if args.command == "verify":
            result = verify_snapshot(args.archive, args.manifest)

            if result["valid"]:
                print("Snapshot integrity verified.")
            else:
                print("WARNING: Snapshot integrity check failed.")

            print(f"Expected SHA-256: {result['expected_sha256']}")
            print(f"Actual SHA-256:   {result['actual_sha256']}")
            return 0 if result["valid"] else 1

        if args.command == "restore":
            if not args.yes:
                print("ROOTWISE will not overwrite existing files.")
                confirmation = input(
                    f"Type RESTORE to proceed into {args.destination}: "
                ).strip()

                if confirmation != "RESTORE":
                    print("Restore cancelled.")
                    return 1

            result = restore_snapshot(
                args.archive,
                args.manifest,
                args.destination,
            )
            print("Restore completed.")
            print(f"Destination: {result['destination']}")
            print(f"Files restored: {result['file_count']}")
            return 0

    except (ValueError, OSError) as error:
        print(f"ROOTWISE error: {error}", file=sys.stderr)
        return 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
