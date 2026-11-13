"""CLI handlers and parser configuration for AGYToolkit Multi-Repository Workspaces."""

import json
import sys
from pathlib import Path
from typing import Any

from agy_toolkit.multi_repo import (
    audit_workspace,
    init_workspace_manifest,
    load_workspace_manifest,
)


def handle_workspace(args) -> int:
    """Handle all subcommands under 'agy-toolkit workspace'."""
    action = args.workspace_action
    target_path = Path(getattr(args, "path", ".") or ".").resolve()

    if action == "init":
        name = getattr(args, "name", None)
        manifest_file = init_workspace_manifest(target_path, name=name)
        manifest = load_workspace_manifest(manifest_file)
        print("=" * 70)
        print(f" [AGYToolkit Workspace] Initialized Manifest: {manifest_file.name}")
        print(f" Workspace: {manifest.name} (v{manifest.version})")
        print(f" Root     : {manifest.workspace_root}")
        print(f" Bus      : {manifest.shared_bus}")
        print("=" * 70)
        print(f"{'Repository':<20} | {'Path':<20} | {'Stack':<12} | {'Role':<12}")
        print("-" * 70)
        for m in manifest.members:
            print(f"{m.name:<20} | {m.path:<20} | {m.stack:<12} | {m.role:<12}")
        print("=" * 70)
        return 0

    elif action == "list":
        try:
            manifest = load_workspace_manifest(target_path)
        except Exception as ex:
            print(f"[AGYToolkit Workspace] Error: {str(ex)}")
            return 1

        if getattr(args, "json", False):
            print(json.dumps(manifest.to_dict(), indent=2))
            return 0

        print("=" * 70)
        print(f" [AGYToolkit Workspace] {manifest.name} (v{manifest.version})")
        print(f" Root: {manifest.workspace_root}")
        print(f" Bus : {manifest.shared_bus}")
        print("=" * 70)
        print(f"{'Repository':<20} | {'Path':<20} | {'Stack':<12} | {'Role':<12} | {'Valid':<5}")
        print("-" * 70)
        for m in manifest.members:
            valid_str = "YES" if m.is_valid else "NO"
            print(f"{m.name:<20} | {m.path:<20} | {m.stack:<12} | {m.role:<12} | {valid_str:<5}")
        print("=" * 70)
        return 0

    elif action == "check":
        try:
            manifest = load_workspace_manifest(target_path)
        except Exception as ex:
            print(f"[AGYToolkit Workspace] Error: {str(ex)}")
            return 1

        audit = audit_workspace(manifest)

        if getattr(args, "json", False):
            print(json.dumps(audit, indent=2))
            if getattr(args, "strict", False) and audit["overall_status"] != "PASS":
                return 1
            return 0

        print("=" * 70)
        print(f" [AGYToolkit Workspace Audit] {manifest.name} | Status: [{audit['overall_status']}]")
        print(f" Healthy Repositories: {audit['healthy_repositories']} / {audit['total_repositories']}")
        print("=" * 70)
        print(f"{'Repository':<18} | {'Stack':<12} | {'Role':<12} | {'Agents':<8} | {'Rules':<8} | {'Status':<10}")
        print("-" * 70)
        for r in audit["repositories"]:
            has_ag = "YES" if r["has_agents"] else "NO"
            has_ru = "YES" if r["has_rules"] else "NO"
            print(f"{r['name']:<18} | {r['stack']:<12} | {r['role']:<12} | {has_ag:<8} | {has_ru:<8} | [{r['status']}]")
        print("=" * 70)

        if getattr(args, "strict", False) and audit["overall_status"] != "PASS":
            return 1
        return 0

    return 0


def configure_workspace_parser(ws_sub):
    """Register all subparser arguments for 'agy-toolkit workspace'."""
    # init
    init_parser = ws_sub.add_parser("init", help="Auto-discover child repos and generate agy-workspace.json")
    init_parser.add_argument("path", nargs="?", default=".", help="Target workspace root directory")
    init_parser.add_argument("--name", help="Workspace name override")

    # list
    list_parser = ws_sub.add_parser("list", help="List registered repositories in workspace manifest")
    list_parser.add_argument("path", nargs="?", default=".", help="Workspace root or manifest path")
    list_parser.add_argument("--json", action="store_true", help="Output members as JSON")

    # check
    check_parser = ws_sub.add_parser("check", help="Audit member repositories health, rules, and agents")
    check_parser.add_argument("path", nargs="?", default=".", help="Workspace root or manifest path")
    check_parser.add_argument("--strict", action="store_true", help="Exit non-zero if any repository needs init")
    check_parser.add_argument("--json", action="store_true", help="Output audit report as JSON")
