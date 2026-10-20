"""Neon cyberpunk terminal interface for ROOTWISE."""

from pathlib import Path

from rootwise.inspector import inspect_repository
from rootwise.health_report import build_health_report
from rootwise.snapshots import (
    create_snapshot,
    restore_snapshot,
    verify_snapshot,
)
from rootwise.sync_observer import observe_sync_candidates


from rootwise.cybergarden import (
    Neon,
    ask_path,
    dashboard_header,
    line,
    menu_frame_bottom,
    menu_frame_text,
    menu_frame_top,
    menu_item,
    menu_zone,
    neon_print,
    section,
)


def show_findings(report: dict) -> None:
    section("Repository scan")
    neon_print(f"  TARGET   :: {report['target']}", Neon.CYAN)
    neon_print(f"  SCANNED  :: {report['checks_run']} checks", Neon.DIM)
    neon_print()

    for finding in report["findings"]:
        status = finding["status"].upper()
        severity = finding.get("severity", "info").lower()
        label = finding["check"]
        evidence = finding["evidence"]

        if status == "PRESENT":
            marker = Neon.paint("[+]", Neon.LIME, Neon.BOLD)
        elif severity in {"warning", "error"}:
            marker = Neon.paint("[!]", Neon.AMBER, Neon.BOLD)
        else:
            marker = Neon.paint("[·]", Neon.CYAN)

        print(f"  {marker} {Neon.paint(label, Neon.WHITE)}")
        neon_print(f"      {evidence}", Neon.DIM)

    section("System limitations")
    for limitation in report["limitations"]:
        neon_print(f"  // {limitation}", Neon.PURPLE)


def show_inspection() -> None:
    target = ask_path("Repository path", ".")
    report = inspect_repository(target)
    show_findings(report)


def show_health_report() -> None:
    """Display an evidence-based repository health report."""
    target = ask_path("Repository path", ".")
    report = build_health_report(target)
    summary = report["summary"]
    scope = report["evidence_scope"]

    section("Repository health report")
    neon_print(f"  TARGET :: {report['target']}", Neon.CYAN)
    neon_print(f"  CHECKS :: {summary['checks_run']}", Neon.WHITE)

    section("Summary")
    neon_print(f"  PRESENT        :: {summary['present']}", Neon.LIME)
    neon_print(f"  NOT FOUND      :: {summary['not_found']}", Neon.AMBER)
    neon_print(f"  EMPTY          :: {summary['empty']}", Neon.CYAN)
    neon_print(f"  UNEXPECTED TYPE :: {summary['unexpected_type']}", Neon.AMBER)
    neon_print(f"  UNREADABLE     :: {summary['unreadable']}", Neon.AMBER)
    neon_print(f"  RECOMMENDED    :: {summary['recommendations']}", Neon.CYAN)
    neon_print(f"  WARNINGS       :: {summary['warnings']}", Neon.AMBER)
    neon_print(f"  ERRORS         :: {summary['errors']}", Neon.RED)
    neon_print(f"  INFO           :: {summary['info']}", Neon.CYAN)

    section("Evidence")
    for finding in report["findings"]:
        status = finding["status"].upper()
        severity = finding.get("severity", "info").lower()

        if status == "PRESENT":
            marker, color = "[+]", Neon.LIME
        elif severity in {"warning", "error"}:
            marker, color = "[!]", Neon.AMBER
        else:
            marker, color = "[·]", Neon.CYAN

        neon_print(f"  {marker} {finding['check']}", color)
        neon_print(f"      {finding['evidence']}", Neon.DIM)

    section("Recommendations")
    if report["recommendations"]:
        for item in report["recommendations"]:
            neon_print(
                f"  [>] {item['check']} :: {item['path']}",
                Neon.CYAN,
            )
            neon_print(f"      {item['reason']}", Neon.DIM)
    else:
        neon_print("  No missing recommended files detected.", Neon.LIME)

    section("What was actually checked")
    neon_print(f"  INSPECTION PERFORMED :: {scope['inspection_performed']}", Neon.CYAN)
    neon_print(f"  TESTS EXECUTED       :: {scope['tests_executed']}", Neon.AMBER)
    neon_print(f"  CONTENTS VALIDATED   :: {scope['file_contents_validated']}", Neon.AMBER)
    neon_print(f"  PUBLICATION APPROVED :: {scope['publication_approved']}", Neon.AMBER)

    section("Limitations")
    for limitation in report["limitations"]:
        neon_print(f"  // {limitation}", Neon.PURPLE)


def show_snapshot() -> None:
    project = ask_path("Project path", ".")

    default_output = str(
        Path.home()
        / ".local"
        / "share"
        / "rootwise"
        / "snapshots"
    )
    output = ask_path("Snapshot destination", default_output)

    result = create_snapshot(project, output)

    section("Snapshot complete")
    neon_print("  [OK] PRESERVATION RECORD CREATED", Neon.LIME, Neon.BOLD)
    neon_print(f"  ARCHIVE  :: {result['archive']}", Neon.CYAN)
    neon_print(f"  MANIFEST :: {result['manifest']}", Neon.CYAN)
    neon_print(f"  FILES    :: {result['file_count']}", Neon.WHITE)
    neon_print(f"  SHA-256  :: {result['sha256']}", Neon.DIM)


def show_verify() -> None:
    archive = ask_path("Snapshot archive")
    manifest = ask_path("Snapshot manifest")

    result = verify_snapshot(archive, manifest)

    section("Integrity diagnostics")

    if result["valid"]:
        neon_print("  [PASS] ARCHIVE MATCHES MANIFEST", Neon.LIME, Neon.BOLD)
    else:
        neon_print("  [ALERT] INTEGRITY CHECK FAILED", Neon.RED, Neon.BOLD)
        neon_print("  Do not rely on this snapshot until investigated.", Neon.AMBER)

    neon_print(f"  EXPECTED :: {result['expected_sha256']}", Neon.DIM)
    neon_print(f"  ACTUAL   :: {result['actual_sha256']}", Neon.DIM)


def show_restore() -> None:
    archive = ask_path("Snapshot archive")
    manifest = ask_path("Snapshot manifest")
    destination = ask_path("Restore destination")

    section("Restore authorization")
    neon_print("  CAUTION :: FILE RESTORATION REQUESTED", Neon.AMBER, Neon.BOLD)
    neon_print("  Existing files will not be overwritten.", Neon.CYAN)
    neon_print(f"  TARGET  :: {destination}", Neon.WHITE)
    neon_print()
    neon_print("  Verify the destination before proceeding.", Neon.DIM)

    confirmation = input(
        Neon.paint("  Type RESTORE to authorize: ", Neon.MAGENTA, Neon.BOLD)
    ).strip()

    if confirmation != "RESTORE":
        neon_print("  [CANCELLED] No restoration was requested.", Neon.DIM)
        return

    result = restore_snapshot(archive, manifest, destination)

    section("Restoration report")
    neon_print("  [OK] RESTORE COMPLETE", Neon.LIME, Neon.BOLD)
    neon_print(f"  DESTINATION :: {result['destination']}", Neon.CYAN)
    neon_print(f"  FILES       :: {result['file_count']}", Neon.WHITE)


def show_observation() -> None:
    """Display local Git changes without staging or publishing them."""
    target = ask_path("Git repository path", ".")
    report = observe_sync_candidates(target)

    section("Sync observation")
    neon_print(f"  REPOSITORY :: {report['repository']}", Neon.CYAN)
    neon_print(f"  BRANCH     :: {report['branch']}", Neon.CYAN)

    remotes = ", ".join(report["remotes"]) or "(none configured)"
    neon_print(f"  REMOTES    :: {remotes}", Neon.DIM)
    neon_print(
        f"  PUBLICATION :: {report['publication_status']}",
        Neon.AMBER,
        Neon.BOLD,
    )

    summary = report["summary"]
    section("Change summary")
    neon_print(f"  CHANGED FILES :: {summary['changed_files']}", Neon.WHITE)
    neon_print(f"  DOCUMENTS     :: {summary['documents']}", Neon.CYAN)
    neon_print(f"  OTHER FILES   :: {summary['other_files']}", Neon.DIM)
    neon_print(f"  RISK FLAGS    :: {summary['risk_flags']}", Neon.AMBER)

    section("Files requiring review")
    if not report["findings"]:
        neon_print("  No tracked or untracked changes detected.", Neon.LIME)

    for item in report["findings"]:
        neon_print(
            f"  [{item['status'].upper()}] {item['path']}",
            Neon.WHITE,
        )
        if item["original_path"]:
            neon_print(f"      Original path :: {item['original_path']}", Neon.DIM)
        if item["risk"]:
            neon_print(f"      REVIEW WARNING :: {item['risk']}", Neon.AMBER)

    section("Observer limitations")
    for limitation in report["limitations"]:
        neon_print(f"  // {limitation}", Neon.PURPLE)


def show_help() -> None:
    section("Operator reference")

    entries = [
        ("1", "REPOSITORY SCAN", "Inspect common project foundations."),
        ("2", "CREATE SNAPSHOT", "Archive files and write a SHA-256 manifest."),
        ("3", "VERIFY SNAPSHOT", "Check archive integrity against its manifest."),
        ("4", "RESTORE SNAPSHOT", "Restore files without overwriting existing files."),
        ("5", "SYNC OBSERVATION", "Review local Git changes without publishing them."),
        ("6", "REPOSITORY HEALTH", "Summarize checks, evidence, and limitations."),
        ("7", "SYSTEM GUIDE", "Display this reference."),
        ("q", "DISCONNECT", "Exit the menu without changing project files."),
    ]

    for key, title, description in entries:
        neon_print(f"  [{key}] {title}", Neon.CYAN, Neon.BOLD)
        neon_print(f"      {description}", Neon.DIM)
        neon_print()

    section("Core protocols")
    neon_print("  01 // Evidence before assumptions.", Neon.LIME)
    neon_print("  02 // Preserve source files.", Neon.PURPLE)
    neon_print("  03 // Never silently overwrite.", Neon.MAGENTA)
    neon_print("  04 // Report uncertainty honestly.", Neon.CYAN)
    neon_print("  05 // Human remains in control.", Neon.LIME)


def pause() -> bool:
    try:
        input(
            "\n"
            + Neon.paint(
                "  [ENTER] RETURN TO CONSOLE",
                Neon.DIM,
            )
        )
        return True
    except (EOFError, KeyboardInterrupt):
        neon_print("\n  Returning to console.", Neon.DIM)
        return False


def run_menu() -> None:
    actions = {
        "1": ("Repository scan", show_inspection),
        "2": ("Create snapshot", show_snapshot),
        "3": ("Verify snapshot", show_verify),
        "4": ("Restore snapshot", show_restore),
        "5": ("Sync observation", show_observation),
        "6": ("Repository health report", show_health_report),
        "7": ("Operator reference", show_help),
    }

    try:
        while True:
            dashboard_header()

            menu_frame_top()
            menu_frame_text("ROOTWISE CONSOLE", Neon.PURPLE, Neon.BOLD)

            menu_zone("Tend the Garden", Neon.LIME)
            menu_item("1", actions["1"][0])
            menu_item("6", actions["6"][0])

            menu_zone("Preserve", Neon.PURPLE)
            menu_item("2", actions["2"][0])
            menu_item("3", actions["3"][0])
            menu_item("4", actions["4"][0])

            menu_zone("Observe Change", Neon.CYAN)
            menu_item("5", actions["5"][0])

            menu_zone("Field Guide", Neon.PINK)
            menu_item("7", actions["7"][0])

            menu_item("q", "Disconnect", Neon.CYAN, Neon.DIM)
            menu_frame_bottom()

            try:
                choice = input(
                    Neon.paint(
                        "\n  rootwise@local ~> ",
                        Neon.LIME,
                        Neon.BOLD,
                    )
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                neon_print("\n  SESSION CLOSED // YOUR FILES REMAIN YOURS",
                           Neon.CYAN, Neon.BOLD)
                return

            if choice == "q":
                neon_print("\n  SESSION CLOSED // YOUR FILES REMAIN YOURS",
                           Neon.CYAN, Neon.BOLD)
                return

            action_entry = actions.get(choice)

            if action_entry is None:
                neon_print(
                    "\n  [INVALID INPUT] Select 1-7 or q.",
                    Neon.AMBER,
                )
                if not pause():
                    return
                continue

            _, action = action_entry

            try:
                action()
            except (ValueError, OSError) as error:
                neon_print("\n  [OPERATION FAILED]", Neon.RED, Neon.BOLD)
                neon_print(f"  {error}", Neon.AMBER)
            except (EOFError, KeyboardInterrupt):
                neon_print("\n  [CANCELLED] Operation interrupted.", Neon.AMBER)

            if not pause():
                return

    except BrokenPipeError:
        return


if __name__ == "__main__":
    run_menu()
