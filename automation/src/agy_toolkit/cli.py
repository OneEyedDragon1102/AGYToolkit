"""AGYToolkit CLI - Command line utility for AGY ecosystem inspection, management, and project scaffolding."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from agy_toolkit.agents import list_agents
from agy_toolkit.cli_bus import configure_bus_parser, handle_bus
from agy_toolkit.cli_workspace import configure_workspace_parser, handle_workspace
from agy_toolkit.cli_swarm import configure_swarm_parser, handle_swarm
from agy_toolkit.doctor import run_doctor, print_doctor_report
from agy_toolkit.linker import link_global
from agy_toolkit.memory import (
    check_memory_budgets,
    flush_active_session,
    record_decision,
)
from agy_toolkit.scaffolder import scaffold_project
from agy_toolkit.skills_data import SKILL_TRACKS
from agy_toolkit.updater import update_project, format_update_report

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"

TOOL_CATALOG = {
    "File System": ["read_file", "write_file", "edit_file"],
    "Process & Tasks": ["run_command", "manage_task"],
    "Scheduling": ["schedule"],
    "User Interaction": ["ask_question"],
    "Web Intelligence": ["search_web"],
    "Multi-Agent": [
        "define_subagent",
        "invoke_subagent",
        "manage_subagents",
        "send_message",
    ],
    "Customizations": ["skills", "rules", "hooks", "plugins", "mcp_servers"],
}


def print_catalog():
    print("=" * 60)
    print(" [AGYToolkit] Supported Tool & Feature Catalog")
    print("=" * 60)
    for category, tools in TOOL_CATALOG.items():
        print(f"\n* {category}:")
        for tool in tools:
            print(f"   - {tool}")
    print("\n" + "=" * 60)


def print_agents():
    agents = list_agents()
    print("=" * 70)
    print(" [AGYToolkit] Governed Specialist Subagents (15 Universal Matrix)")
    print("=" * 70)
    for a in agents:
        name = a.get("name", "unknown")
        role = a.get("role", "Specialist")
        ws = a.get("recommendedWorkspace", "inherit")
        write = "RW" if a.get("enableWriteTools") else "RO"
        print(f"\n* {name} [{write} | {ws}]")
        print(f"   Role: {role}")
        print(f"   Desc: {a.get('description', '')}")
    print("\n" + "=" * 70)


def print_skills():
    total_skills = sum(len(skills) for skills in SKILL_TRACKS.values())
    print("=" * 75)
    print(f" [AGYToolkit] Progressive SDLC Skills Catalog ({total_skills} Skills across 5 Tracks)")
    print("=" * 75)
    for track, skills in SKILL_TRACKS.items():
        print(f"\n* {track} ({len(skills)} skills):")
        for name, desc in skills:
            print(f"   - {name:<26} : {desc}")
    print("\n" + "=" * 75)


def print_templates():
    from agy_toolkit.scaffolder_stacks import list_available_templates

    templates = list_available_templates()
    print("=" * 75)
    print(" [AGYToolkit] Turnkey Tech-Stack Production Boilerplate Templates")
    print("=" * 75)
    for t in templates:
        name = t.get("name", "unknown")
        lang = t.get("language", "")
        framework = t.get("framework", "")
        arch = t.get("architecture", "")
        desc = t.get("description", "")
        aliases = ", ".join(t.get("aliases", []))
        print(f"\n* {name} [{lang} | {framework}]")
        print(f"   Architecture: {arch}")
        print(f"   Aliases:      {aliases}")
        print(f"   Description:  {desc}")
    print("\n" + "=" * 75)


def handle_init(args):
    if getattr(args, "list_templates", False):
        print_templates()
        return

    target = Path(args.path or ".").resolve()
    name = args.name or target.name
    stack = args.stack or "node-ts"
    mode = args.mode or "feature"
    template = getattr(args, "template", None)

    print("=" * 60)
    print(f" [AGYToolkit] Initializing Governance for: {name}")
    print(f" Target: {target}")
    tmpl_info = f" | Template: {template}" if template else ""
    print(f" Stack: {stack} | Mode: {mode.upper()}{tmpl_info}")
    print("=" * 60)

    res = scaffold_project(
        target_path=target,
        project_name=name,
        stack=stack,
        mode=mode,
        template=template,
    )

    print(f"\n Success! Workspace provisioned with:")
    print(f"   - {res['agents_installed']} specialist subagents in .agents/agents/")
    print(f"   - {res['skills_installed']} progressive SDLC skills in .agents/skills/")
    print(f"   - {res['hooks_installed']} lifecycle hook scripts in .agents/hooks/")
    print(f"   - Active session memory initialized (gitignored)")
    print(f"   - GEMINI.md and AGENTS.md project rules generated")
    if res.get("template"):
        print(f"   - {res['template_files_count']} boilerplate files scaffolded from '{res['template']}'")
    print("\nNext step: Open this workspace in AGY to activate autonomous governance.")
    print("=" * 60)


def handle_update(args) -> int:
    target = Path(args.path or ".").resolve()
    dry_run = getattr(args, "dry_run", False)
    force_rules = getattr(args, "force_rules", False)

    report = update_project(
        target_path=target,
        dry_run=dry_run,
        force_rules=force_rules,
    )

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_update_report(report))

    return 0 if report.success else 1


def handle_doctor(args):
    target = Path(args.path or ".").resolve()
    if getattr(args, "tui", False):
        from agy_toolkit.dashboard import render_tui
        print(render_tui(target))
        return 0

    report = run_doctor(target_path=target)

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_doctor_report(report)

    if getattr(args, "strict", False) and (report.warnings > 0 or report.failures > 0):
        sys.exit(1)
    elif not report.is_healthy:
        sys.exit(1)
    return 0


def handle_dashboard(args):
    target = Path(args.path or ".").resolve()
    if getattr(args, "web", False):
        from agy_toolkit.dashboard import launch_web_dashboard
        port = getattr(args, "port", 8765)
        open_browser = not getattr(args, "no_browser", False)
        launch_web_dashboard(workspace_root=target, port=port, open_browser=open_browser)
    else:
        from agy_toolkit.dashboard import render_tui
        print(render_tui(target))
    return 0


def handle_link_global(args):
    mode = args.mode or "copy"
    dry_run = getattr(args, "dry_run", False)

    prefix = "[DRY-RUN] " if dry_run else ""
    print("=" * 65)
    print(f" {prefix}[AGYToolkit] Mounting Global Capabilities to ~/.gemini/config/")
    print(f" Mode: {mode}")
    print("=" * 65)

    stats = link_global(mode=mode, dry_run=dry_run)
    print("\n Results:")
    print(f"   - Destination: {stats['config_dir']}")
    print(f"   - Skills mounted: {stats['skills_linked']}/28")
    print(f"   - Agents mounted: {stats['agents_linked']}/15")
    if stats["errors"]:
        print(f"   - Errors encountered: {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"     ! {err}")
    else:
        action = "would be discoverable" if dry_run else "are now discoverable"
        print(f"\n Success! All AGYToolkit capabilities {action} machine-wide in AGY.")
    print("=" * 65)


def handle_memory(args):
    action = args.memory_action
    target_dir = Path(args.path or ".").resolve() / ".agents" / "memory"

    if action == "status":
        budgets = check_memory_budgets(memory_dir=target_dir)
        if getattr(args, "json", False):
            print(json.dumps(budgets, indent=2))
        else:
            print("=" * 60)
            print(" [AGYToolkit Memory Engine] Context Budget & Health")
            print("=" * 60)
            for key, data in budgets.items():
                name = "Active Session" if key == "active_session" else "Decisions Register"
                status = "[PASS]" if data["within_budget"] else "[FAIL]"
                pct = (data["bytes"] / data["cap"]) * 100 if data["cap"] else 0
                print(f"  {status} {name:20}: {data['bytes']} / {data['cap']} bytes ({pct:.1f}%)")
            print("=" * 60)

    elif action == "flush":
        archive = not getattr(args, "no_archive", False)
        archive_path = flush_active_session(archive=archive, memory_dir=target_dir)
        if archive_path:
            print(f"[AGYToolkit] Active session flushed and archived to: {archive_path.name}")
        else:
            print("[AGYToolkit] Active session flushed to clean state.")

    elif action == "record":
        category = args.category
        decision = args.decision
        record_decision(category=category, decision=decision, memory_dir=target_dir)
        print(f"[AGYToolkit] Recorded decision under [{category}].")

    elif action == "auto-compact":
        from agy_toolkit.memory import auto_compact_memory, format_compact_report

        ws = Path(args.path or ".").resolve()
        threshold = getattr(args, "threshold", 0.85)
        dry_run = getattr(args, "dry_run", False)
        report = auto_compact_memory(
            memory_dir=target_dir,
            threshold=threshold,
            workspace_root=ws,
            dry_run=dry_run,
        )
        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(format_compact_report(report))

    elif action == "search":
        from agy_toolkit.knowledge import search_knowledge

        ws = Path(args.path or ".").resolve()
        query = args.query
        cat = getattr(args, "category", None)
        limit = getattr(args, "limit", 5)
        results = search_knowledge(ws, query, category=cat, limit=limit)
        if getattr(args, "json", False):
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print("=" * 70)
            print(f" [AGYToolkit Knowledge Search] Query: '{query}'")
            if cat:
                print(f" Filter Category: [{cat}]")
            print(f" Hits: {len(results)}")
            print("=" * 70)
            for idx, r in enumerate(results, 1):
                date_info = f" ({r.date})" if r.date else ""
                print(f"\n{idx}. [{r.category}] {r.title}{date_info}")
                print(f"   Source:  {r.source_file}")
                print(f"   Snippet: {r.snippet}")
            print("\n" + "=" * 70)

    elif action == "reindex":
        from agy_toolkit.knowledge import index_workspace

        ws = Path(args.path or ".").resolve()
        force = getattr(args, "force", False)
        report = index_workspace(ws, force=force)
        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print("=" * 60)
            print(" [AGYToolkit Knowledge Engine] Reindexed Workspace")
            print("=" * 60)
            print(f" Files indexed:    {report.indexed_files}")
            print(f" Files skipped:    {report.skipped_files} (unchanged)")
            print(f" Total documents:  {report.total_documents}")
            print(f" Elapsed:          {report.elapsed_ms} ms")
            print("=" * 60)


def handle_mcp(args):
    target = Path(args.path or ".").resolve()
    from agy_toolkit.mcp_server import McpServer

    server = McpServer(workspace_root=target)
    if getattr(args, "export_schemas", None):
        out_dir = Path(args.export_schemas).resolve()
        exported = server.export_schemas(out_dir)
        print(f"[AGYToolkit MCP] Exported {len(exported)} MCP tool schemas to {out_dir}")
        for p in exported:
            print(f"  * {p.name}")
    else:
        server.run_stdio()


def handle_pr_review(args):
    target = Path(args.path or ".").resolve()
    base_ref = getattr(args, "base", "origin/main")
    output_path = getattr(args, "output", None)
    strict = getattr(args, "strict", False)

    from agy_toolkit.pr_reviewer import run_pr_review

    card, overall_pass = run_pr_review(base_ref=base_ref, workspace_root=target)

    if output_path:
        out_file = Path(output_path).resolve()
        out_file.write_text(card + "\n", encoding="utf-8")
        print(f"[AGYToolkit PR Review] Review card written to: {out_file}")
    else:
        print(card)

    if strict and not overall_pass:
        sys.exit(1)


def main(argv: List[str] = None):
    # Ensure safe encoding for Windows command line output when running standalone
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="agy-toolkit",
        description="AGYToolkit CLI: Autonomous Multi-Agent SDLC Framework for AGY.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Scaffold AGYToolkit into a downstream repository")
    init_parser.add_argument("path", nargs="?", default=".", help="Target project directory path (default: current dir)")
    init_parser.add_argument("--name", help="Project name (defaults to target directory name)")
    init_parser.add_argument("--stack", choices=["spring-boot", "node-ts", "python"], default="node-ts", help="Primary tech stack")
    init_parser.add_argument("--mode", choices=["feature", "spike", "quickfix"], default="feature", help="Operational mode")
    init_parser.add_argument("--template", help="Turnkey production starter template (e.g. spring-boot-hexagonal, node-clean-ts, python-fastapi)")
    init_parser.add_argument("--list-templates", action="store_true", help="List available turnkey production stack templates")

    # update subcommand
    update_parser = subparsers.add_parser("update", help="Update skills, agents, and hooks in an existing downstream repository")
    update_parser.add_argument("path", nargs="?", default=".", help="Target project directory path (default: current dir)")
    update_parser.add_argument("--dry-run", action="store_true", help="Simulate update and preview changes without writing")
    update_parser.add_argument("--force-rules", action="store_true", help="Force refresh GEMINI.md and AGENTS.md rules from latest templates")
    update_parser.add_argument("--json", action="store_true", help="Output update report as JSON")

    # doctor subcommand
    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostic health and governance audit")
    doctor_parser.add_argument("path", nargs="?", default=".", help="Target workspace path (default: current dir)")
    doctor_parser.add_argument("--json", action="store_true", help="Output doctor findings as JSON")
    doctor_parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on any warnings or failures")
    doctor_parser.add_argument("--tui", action="store_true", help="Render diagnostic results in visual terminal TUI cockpit")

    # dashboard subcommand
    dash_parser = subparsers.add_parser("dashboard", help="Launch interactive terminal TUI or browser-based dashboard")
    dash_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    dash_parser.add_argument("--web", action="store_true", help="Launch browser-based web dashboard")
    dash_parser.add_argument("--port", type=int, default=8765, help="Port for web dashboard (default: 8765)")
    dash_parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser")

    # link-global subcommand
    link_parser = subparsers.add_parser("link-global", help="Mount skills and agents to ~/.gemini/config/ for global discovery")
    link_parser.add_argument("--mode", choices=["copy", "symlink"], default="copy", help="Mount method (default: copy)")
    link_parser.add_argument("--dry-run", action="store_true", help="Simulate mounting without writing")

    # memory subcommand
    mem_parser = subparsers.add_parser("memory", help="Inspect and govern tiered agent memory budgets")
    mem_sub = mem_parser.add_subparsers(dest="memory_action", required=True)

    mem_status = mem_sub.add_parser("status", help="Check active session and decisions byte caps")
    mem_status.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_status.add_argument("--json", action="store_true", help="Output memory metrics as JSON")

    mem_flush = mem_sub.add_parser("flush", help="Flush active session working memory")
    mem_flush.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_flush.add_argument("--no-archive", action="store_true", help="Do not archive current session to sessions/ directory")

    mem_record = mem_sub.add_parser("record", help="Record an architectural decision")
    mem_record.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_record.add_argument("--category", required=True, help="Decision category (e.g., ARCH, SEC, API)")
    mem_record.add_argument("--decision", required=True, help="Binding architectural decision statement")

    mem_compact = mem_sub.add_parser("auto-compact", help="Auto-compact session and archive oldest decisions")
    mem_compact.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_compact.add_argument("--threshold", type=float, default=0.85, help="Usage threshold ratio (default: 0.85)")
    mem_compact.add_argument("--dry-run", action="store_true", help="Simulate compaction without writing")
    mem_compact.add_argument("--json", action="store_true", help="Output compaction report as JSON")

    mem_search = mem_sub.add_parser("search", help="Full-text search historical ADRs and sprint sessions")
    mem_search.add_argument("query", help="Full-text search keywords")
    mem_search.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_search.add_argument("--category", help="Optional category filter (e.g. ARCH, BUS, SEC)")
    mem_search.add_argument("--limit", type=int, default=5, help="Maximum results (default: 5)")
    mem_search.add_argument("--json", action="store_true", help="Output results as JSON")

    mem_reindex = mem_sub.add_parser("reindex", help="Rebuild SQLite FTS5 knowledge search index")
    mem_reindex.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    mem_reindex.add_argument("--force", action="store_true", help="Force reindexing all files")
    mem_reindex.add_argument("--json", action="store_true", help="Output report as JSON")

    # bus subcommand
    bus_parser = subparsers.add_parser("bus", help="Interact with volatile multi-agent event bus")
    bus_sub = bus_parser.add_subparsers(dest="bus_action", required=True)
    configure_bus_parser(bus_sub)

    # swarm subcommand
    swarm_parser = subparsers.add_parser(
        "swarm", help="Autonomous multi-agent DAG pipeline choreography"
    )
    swarm_sub = swarm_parser.add_subparsers(dest="swarm_action", required=True)
    configure_swarm_parser(swarm_sub)

    # workspace subcommand
    ws_parser = subparsers.add_parser(
        "workspace", help="Multi-repository workspace manifest management and health audit"
    )
    ws_sub = ws_parser.add_subparsers(dest="workspace_action", required=True)
    configure_workspace_parser(ws_sub)

    # mcp command
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Start native Antigravity MCP Server over stdio or export schemas",
    )
    mcp_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace root directory (default: current dir)",
    )
    mcp_parser.add_argument(
        "--export-schemas",
        dest="export_schemas",
        help="Export tool schema JSON files into target directory and exit",
    )

    # pr-review command
    pr_parser = subparsers.add_parser(
        "pr-review",
        help="Generate autonomous PR review report card and audit pull request diff",
    )
    pr_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace root directory (default: current dir)",
    )
    pr_parser.add_argument(
        "--base",
        default="origin/main",
        help="Base git reference to diff against (default: origin/main)",
    )
    pr_parser.add_argument(
        "--output",
        help="File path to write markdown review card into",
    )
    pr_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code on any governance or anti-bloat failure",
    )

    # flags on root
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all AGY tools cataloged by AGYToolkit",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all 15 governed specialist subagents in AGYToolkit",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List all 28 progressive SDLC skills in AGYToolkit",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available turnkey production stack templates",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        handle_init(args)
    elif args.command == "update":
        return handle_update(args)
    elif args.command == "doctor":
        return handle_doctor(args)
    elif args.command == "dashboard":
        return handle_dashboard(args)
    elif args.command == "link-global":
        handle_link_global(args)
    elif args.command == "memory":
        handle_memory(args)
    elif args.command == "bus":
        handle_bus(args)
    elif args.command == "workspace":
        return handle_workspace(args)
    elif args.command == "swarm":
        handle_swarm(args)
    elif args.command == "mcp":
        handle_mcp(args)
    elif args.command == "pr-review":
        handle_pr_review(args)
    elif args.list_templates:
        print_templates()
    elif args.list_skills:
        print_skills()
    elif args.list_agents:
        print_agents()
    elif args.list_tools:
        print_catalog()
    elif argv is not None and len(argv) == 0:
        print_catalog()
    elif len(sys.argv) == 1:
        print_catalog()
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    main()
