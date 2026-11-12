"""MCP Tool definitions and handlers for AGYToolkit Multi-Repository Swarms."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agy_toolkit.multi_repo import (
    MULTI_REPO_BLUEPRINTS,
    audit_workspace,
    format_multi_status_card,
    get_multi_run,
    launch_multi_run,
    load_workspace_manifest,
)

MULTI_REPO_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "agy_workspace_status",
        "description": "Query multi-repository workspace status, member health, detected tech stacks, and governance audit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "manifest_path": {
                    "type": "string",
                    "description": "Optional path to agy-workspace.json or workspace directory.",
                },
            },
        },
    },
    {
        "name": "agy_swarm_multi_run",
        "description": "Launch a cross-repository swarm pipeline run spanning multiple services and git worktrees.",
        "inputSchema": {
            "type": "object",
            "required": ["blueprint"],
            "properties": {
                "blueprint": {
                    "type": "string",
                    "description": f"Multi-repo blueprint name. Available: {list(MULTI_REPO_BLUEPRINTS.keys())}",
                },
                "manifest_path": {
                    "type": "string",
                    "description": "Optional path to agy-workspace.json or workspace directory.",
                },
                "context": {
                    "type": "object",
                    "description": "Initial context dictionary for the cross-repository run.",
                },
            },
        },
    },
    {
        "name": "agy_swarm_multi_status",
        "description": "Query cross-repository swarm pipeline execution topology and step progress card.",
        "inputSchema": {
            "type": "object",
            "required": ["run_id"],
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Unique multi-repository run ID (e.g. mrun-12345678).",
                },
                "manifest_path": {
                    "type": "string",
                    "description": "Optional path to agy-workspace.json or workspace directory.",
                },
            },
        },
    },
]


def handle_multi_repo_tool(
    workspace_root: Path, tool_name: str, arguments: Dict[str, Any]
) -> Optional[Tuple[str, bool]]:
    """Dispatch multi-repository MCP tool invocations. Returns (result_text, is_error) or None."""
    if tool_name not in ("agy_workspace_status", "agy_swarm_multi_run", "agy_swarm_multi_status"):
        return None

    manifest_arg = arguments.get("manifest_path")
    manifest_target = Path(manifest_arg).resolve() if manifest_arg else workspace_root

    try:
        manifest = load_workspace_manifest(manifest_target)
    except FileNotFoundError as ex:
        return f"Error: {str(ex)}", True
    except Exception as ex:
        return f"Error loading workspace manifest: {str(ex)}", True

    if tool_name == "agy_workspace_status":
        audit = audit_workspace(manifest)
        lines = [
            "=" * 70,
            f" [AGYToolkit Multi-Repo Workspace] {manifest.name} (v{manifest.version})",
            f" Root: {manifest.workspace_root}",
            f" Bus : {manifest.shared_bus}",
            "=" * 70,
            f" Status : [{audit['overall_status']}] | Healthy: {audit['healthy_repositories']}/{audit['total_repositories']}",
            "-" * 70,
            f"{'Member':<18} | {'Stack':<14} | {'Role':<14} | {'Health':<10}",
            "-" * 70,
        ]
        for r in audit["repositories"]:
            lines.append(f"{r['name']:<18} | {r['stack']:<14} | {r['role']:<14} | [{r['status']}]")
        lines.append("=" * 70)
        return "\n".join(lines), False

    elif tool_name == "agy_swarm_multi_run":
        blueprint = arguments.get("blueprint", "")
        if not blueprint:
            return "Error: Missing required argument 'blueprint'.", True

        context = arguments.get("context")
        try:
            run = launch_multi_run(manifest, blueprint, context=context)
            card = format_multi_status_card(run, manifest)
            return card, False
        except ValueError as ex:
            return f"Error: {str(ex)}", True
        except Exception as ex:
            return f"Error launching multi-run: {str(ex)}", True

    elif tool_name == "agy_swarm_multi_status":
        run_id = arguments.get("run_id", "")
        if not run_id:
            return "Error: Missing required argument 'run_id'.", True

        run = get_multi_run(manifest, run_id)
        if not run:
            return f"Error: Multi-repo run '{run_id}' not found.", True

        card = format_multi_status_card(run, manifest)
        return card, False

    return None
