"""MCP Tool definitions and handlers for AGYToolkit GitOps Release Bot."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agy_toolkit.release import execute_release, plan_release

RELEASE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "agy_release_plan",
        "description": "Preview projected release plan, SemVer transition, Conventional Commits categorization, and CHANGELOG.md diff.",
        "inputSchema": {
            "type": "object",
            "required": ["bump_type"],
            "properties": {
                "bump_type": {
                    "type": "string",
                    "enum": ["patch", "minor", "major"],
                    "description": "Semantic version increment type.",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Optional repository path (defaults to current workspace).",
                },
            },
        },
    },
    {
        "name": "agy_release_create",
        "description": "Execute automated GitOps release pipeline: pre-flight checks, SemVer bump across metadata, CHANGELOG.md generation, and git tag creation.",
        "inputSchema": {
            "type": "object",
            "required": ["bump_type"],
            "properties": {
                "bump_type": {
                    "type": "string",
                    "enum": ["patch", "minor", "major"],
                    "description": "Semantic version increment type.",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Optional repository path (defaults to current workspace).",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate release without modifying files or git tags (default: false).",
                    "default": False,
                },
                "skip_tests": {
                    "type": "boolean",
                    "description": "Bypass automated test suite verification gate (default: false).",
                    "default": False,
                },
                "allow_branch": {
                    "type": "boolean",
                    "description": "Permit cutting a release from a branch other than main (default: false).",
                    "default": False,
                },
            },
        },
    },
]


def handle_release_mcp_tool(
    workspace_root: Path, tool_name: str, arguments: Dict[str, Any]
) -> Optional[Tuple[str, bool]]:
    """Dispatch release MCP tool calls. Returns (result_text, is_error) or None."""
    if tool_name not in ("agy_release_plan", "agy_release_create"):
        return None

    bump_type = arguments.get("bump_type", "").lower()
    if not bump_type or bump_type not in ("patch", "minor", "major"):
        return "Error: Argument 'bump_type' must be one of 'patch', 'minor', 'major'.", True

    repo_arg = arguments.get("repo_path")
    repo_path = Path(repo_arg).resolve() if repo_arg else workspace_root

    if tool_name == "agy_release_plan":
        try:
            plan = plan_release(repo_path, bump_type)
            lines = [
                "=" * 70,
                f" [AGYToolkit Release Plan] v{plan.current_version} -> v{plan.next_version} ({bump_type.upper()})",
                f" Commits since tag '{plan.previous_tag or 'initial'}': {plan.commits_count}",
                "=" * 70,
                plan.changelog_snippet,
                "=" * 70,
            ]
            return "\n".join(lines), False
        except Exception as ex:
            return f"Error planning release: {str(ex)}", True

    elif tool_name == "agy_release_create":
        dry_run = bool(arguments.get("dry_run", False))
        skip_tests = bool(arguments.get("skip_tests", False))
        allow_branch = bool(arguments.get("allow_branch", False))

        try:
            report = execute_release(
                repo_path=repo_path,
                bump_type=bump_type,
                dry_run=dry_run,
                skip_tests=skip_tests,
                allow_branch=allow_branch,
            )
            if report.get("status") == "DRY_RUN":
                plan_dict = report["plan"]
                lines = [
                    "=" * 70,
                    " [AGYToolkit Release Simulation] DRY RUN ACTIVE",
                    f" Target Version : v{plan_dict['next_version']} ({plan_dict['bump_type'].upper()})",
                    f" Current Version: v{plan_dict['current_version']}",
                    f" Commits Count  : {plan_dict['commits_count']}",
                    " Files to Update:",
                ]
                for f in plan_dict["files_to_update"]:
                    lines.append(f"  * {f}")
                lines.append("-" * 70)
                lines.append(" Projected Changelog:")
                lines.append(plan_dict["changelog_snippet"])
                lines.append("=" * 70)
                return "\n".join(lines), False

            lines = [
                "=" * 70,
                f" [AGYToolkit Release] Release {report['tag']} Cut Successfully!",
                f" Version : v{report['version']} ({report['bump_type'].upper()})",
                f" Git Tag : {report['tag']}",
                f" Commits : {report['commits_count']} commits indexed",
                " Updated Metadata:",
            ]
            for f in report["updated_files"]:
                lines.append(f"  * {f}")
            lines.append("=" * 70)
            return "\n".join(lines), False
        except Exception as ex:
            return f"Release Gate Failed: {str(ex)}", True

    return None
