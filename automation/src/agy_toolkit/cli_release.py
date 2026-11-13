"""CLI handlers and parser configuration for AGYToolkit GitOps Release Bot."""

import json
import sys
from pathlib import Path
from typing import Any

from agy_toolkit.release import execute_release, plan_release


def handle_release(args) -> int:
    """Handle 'agy-toolkit release' command."""
    target_path = Path(getattr(args, "path", ".") or ".").resolve()
    bump_type = args.bump.lower()
    dry_run = getattr(args, "dry_run", False)
    skip_tests = getattr(args, "skip_tests", False)
    allow_branch = getattr(args, "allow_branch", False)
    notes_only = getattr(args, "notes_only", False)
    as_json = getattr(args, "json", False)

    if notes_only:
        try:
            plan = plan_release(target_path, bump_type)
        except Exception as ex:
            print(f"[AGYToolkit Release] Error planning release: {str(ex)}")
            return 1

        if as_json:
            print(json.dumps(plan.to_dict(), indent=2))
        else:
            print("=" * 70)
            print(f" [AGYToolkit Release Plan] v{plan.current_version} -> v{plan.next_version} ({bump_type.upper()})")
            print(f" Commits since tag '{plan.previous_tag or 'initial'}': {plan.commits_count}")
            print("=" * 70)
            print(plan.changelog_snippet)
            print("=" * 70)
        return 0

    try:
        report = execute_release(
            repo_path=target_path,
            bump_type=bump_type,
            dry_run=dry_run,
            skip_tests=skip_tests,
            allow_branch=allow_branch,
        )
    except Exception as ex:
        print(f"[AGYToolkit Release] Release Gate Failed: {str(ex)}")
        return 1

    if as_json:
        print(json.dumps(report, indent=2))
        return 0

    if report.get("status") == "DRY_RUN":
        plan_dict = report["plan"]
        print("=" * 70)
        print(" [AGYToolkit Release Simulation] DRY RUN ACTIVE")
        print(f" Target Version : v{plan_dict['next_version']} ({plan_dict['bump_type'].upper()})")
        print(f" Current Version: v{plan_dict['current_version']}")
        print(f" Commits Count  : {plan_dict['commits_count']}")
        print(" Files to Update:")
        for f in plan_dict["files_to_update"]:
            print(f"  * {f}")
        print("-" * 70)
        print(" Projected Changelog:")
        print(plan_dict["changelog_snippet"])
        print("=" * 70)
        print(" (Run without --dry-run to commit, bump, and tag release)")
    else:
        print("=" * 70)
        print(f" [AGYToolkit Release] Release {report['tag']} Cut Successfully!")
        print(f" Version : v{report['version']} ({report['bump_type'].upper()})")
        print(f" Git Tag : {report['tag']}")
        print(f" Commits : {report['commits_count']} commits indexed")
        print(" Updated Metadata:")
        for f in report["updated_files"]:
            print(f"  * {f}")
        print("=" * 70)
        print(" Next Steps:")
        print(f"  1. Push release commit: git push origin main")
        print(f"  2. Push release tag   : git push origin {report['tag']}")
        print("=" * 70)

    return 0


def configure_release_parser(release_parser):
    """Register arguments for 'agy-toolkit release' command."""
    release_parser.add_argument(
        "bump",
        choices=["patch", "minor", "major"],
        help="Semantic version increment type",
    )
    release_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    release_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate release without modifying files or git tags",
    )
    release_parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Bypass test suite verification gate (use with caution)",
    )
    release_parser.add_argument(
        "--allow-branch",
        action="store_true",
        help="Permit cutting a release from a branch other than main",
    )
    release_parser.add_argument(
        "--notes-only",
        action="store_true",
        help="Print projected changelog entry and exit without modifying repository",
    )
    release_parser.add_argument(
        "--json",
        action="store_true",
        help="Output release report or plan as JSON",
    )
