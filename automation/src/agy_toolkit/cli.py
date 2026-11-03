"""AGYToolkit CLI - Command line utility for AGY ecosystem inspection, management, and project scaffolding."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from agy_toolkit.agents import list_agents
from agy_toolkit.bus import (
    publish_event,
    read_event,
    list_events,
    consume_events,
    clear_bus,
)
from agy_toolkit.doctor import run_doctor, print_doctor_report
from agy_toolkit.linker import link_global
from agy_toolkit.memory import (
    check_memory_budgets,
    flush_active_session,
    record_decision,
)
from agy_toolkit.scaffolder import scaffold_project

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

SKILL_TRACKS = {
    "Track A: Planning & Architecture": [
        ("adr-architect", "Documents architecture decision records with trade-off matrices"),
        ("plan-approval-gate", "Enforces plan-approval gate before code modifications"),
        ("task-decomposer", "Decomposes complex user epics into atomic tasks"),
        ("context-budgeter", "Manages token budgets and offloads volatile data"),
        ("telemetry-logger", "Structures execution logs and cross-agent handoffs"),
        ("handbook-enforcer", "Enforces repository guidelines and coding rules"),
    ],
    "Track B: TDD & Implementation": [
        ("tdd-spring-boot", "Red-Green-Refactor TDD for Java 23 / Spring Boot"),
        ("tdd-node-ts", "Red-Green-Refactor TDD for Node.js / TypeScript"),
        ("tdd-python", "Isolated Python 3.12 TDD in virtual environments"),
        ("spring-service-generator", "Generates Hexagonal Architecture Spring Boot services"),
        ("node-mcp-builder", "Builds MCP servers and tools using TypeScript SDK"),
        ("ui-component-builder", "Builds accessible, responsive UI components"),
        ("refactor-cleaner", "Structural refactoring and modularization (<600 lines)"),
    ],
    "Track C: Review & Quality Gates": [
        ("code-reviewer", "Production-grade code review on git diffs"),
        ("anti-bloat-linter", "Scans for emojis, chatter, and monolithic files"),
        ("security-scanner", "Audits for credentials, OWASP vulnerabilities, and CVEs"),
        ("coverage-verifier", "Enforces mandatory 80%+ test coverage threshold"),
        ("concurrency-auditor", "Audits multi-threaded code and race conditions"),
        ("api-contract-checker", "Validates API schemas and DTO compatibility"),
    ],
    "Track D: Git, Staging & CI/CD": [
        ("commit-craft", "Drafts atomic Conventional Commits"),
        ("branch-manager", "Governs feature branch workflows and isolation"),
        ("selective-stager", "Granular staging and sign-off verification"),
        ("release-packager", "SemVer calculation, changelog generation, and packaging"),
        ("ci-pipeline-validator", "Validates CI/CD workflow configurations"),
    ],
    "Track E: Meta-Framework & Extensibility": [
        ("agy-inspector", "Audits AGY tools, skills, rules, and MCP servers"),
        ("skill-author", "Authors project-specific domain skills on demand"),
        ("agent-author", "Authors project-specific specialist subagents on demand"),
        ("workspace-doctor", "Diagnoses workspace dependencies and build toolchains"),
    ],
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


def handle_init(args):
    target = Path(args.path or ".").resolve()
    name = args.name or target.name
    stack = args.stack or "node-ts"
    mode = args.mode or "feature"

    print("=" * 60)
    print(f" [AGYToolkit] Initializing Governance for: {name}")
    print(f" Target: {target}")
    print(f" Stack: {stack} | Mode: {mode.upper()}")
    print("=" * 60)

    res = scaffold_project(
        target_path=target,
        project_name=name,
        stack=stack,
        mode=mode,
    )

    print(f"\n Success! Workspace provisioned with:")
    print(f"   - {res['agents_installed']} specialist subagents in .agents/agents/")
    print(f"   - {res['skills_installed']} progressive SDLC skills in .agents/skills/")
    print(f"   - {res['hooks_installed']} lifecycle hook scripts in .agents/hooks/")
    print(f"   - Active session memory initialized (gitignored)")
    print(f"   - GEMINI.md and AGENTS.md project rules generated")
    print("\nNext step: Open this workspace in AGY to activate autonomous governance.")
    print("=" * 60)



def handle_doctor(args):
    target = Path(args.path or ".").resolve()
    report = run_doctor(target_path=target)

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_doctor_report(report)

    if getattr(args, "strict", False) and (report.warnings > 0 or report.failures > 0):
        sys.exit(1)
    elif not report.is_healthy:
        sys.exit(1)


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


def handle_bus(args):
    action = args.bus_action
    target_dir = Path(args.path or ".").resolve() / ".agents" / "memory"

    if action == "send":
        raw_payload = args.payload
        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError):
            payload = raw_payload

        evt = publish_event(
            topic=args.topic,
            sender=args.sender,
            payload=payload,
            recipient=getattr(args, "recipient", "*") or "*",
            ttl_seconds=getattr(args, "ttl", 3600),
            memory_dir=target_dir,
        )
        print(f"[AGYToolkit Bus] Published event {evt.id} to topic '{evt.topic}' (Recipient: {evt.recipient}).")

    elif action == "read":
        if getattr(args, "id", None):
            evt = read_event(event_id=args.id, consume=getattr(args, "consume", False), memory_dir=target_dir)
            if evt:
                print(json.dumps(evt.to_dict(), indent=2))
            else:
                print(f"[AGYToolkit Bus] Event '{args.id}' not found.")
        else:
            if getattr(args, "consume", False):
                events = consume_events(
                    topic=getattr(args, "topic", None),
                    recipient=getattr(args, "recipient", None),
                    sender=getattr(args, "sender", None),
                    memory_dir=target_dir,
                )
            else:
                events = list_events(
                    topic=getattr(args, "topic", None),
                    recipient=getattr(args, "recipient", None),
                    sender=getattr(args, "sender", None),
                    memory_dir=target_dir,
                )
            if getattr(args, "json", False):
                print(json.dumps([e.to_dict() for e in events], indent=2))
            else:
                print(f"[AGYToolkit Bus] Found {len(events)} event(s):")
                for e in events:
                    print(f"  * {e.id} [{e.topic}] {e.sender} -> {e.recipient}")

    elif action == "list":
        events = list_events(memory_dir=target_dir)
        if getattr(args, "json", False):
            print(json.dumps([e.to_dict() for e in events], indent=2))
        else:
            print(f"[AGYToolkit Bus] Active events on volatile bus: {len(events)}")
            for e in events:
                print(f"  * {e.id} [{e.topic}] ({e.sender} -> {e.recipient})")

    elif action == "clear":
        cleared = clear_bus(memory_dir=target_dir)
        print(f"[AGYToolkit Bus] Cleared {cleared} event payload(s) from volatile bus.")

    elif action == "watch":
        from agy_toolkit.bus import watch_events, claim_event, complete_claimed_event

        timeout = getattr(args, "timeout", None)
        consume = getattr(args, "consume", False)
        topic = getattr(args, "topic", None)
        recipient = getattr(args, "recipient", None)
        sender = getattr(args, "sender", None)
        output_json = getattr(args, "json", False)

        if not output_json:
            filt = f" [topic: {topic}]" if topic else ""
            print(f"[AGYToolkit Bus] Watching volatile bus for events{filt} (timeout: {timeout or 'infinite'})...")

        for event in watch_events(
            topic=topic,
            recipient=recipient,
            sender=sender,
            timeout_seconds=timeout,
            memory_dir=target_dir,
        ):
            if consume:
                claimed = claim_event(event.id, claimer="bus-watch-cli", memory_dir=target_dir)
                if claimed:
                    complete_claimed_event(event.id, claimer="bus-watch-cli", memory_dir=target_dir)

            if output_json:
                print(json.dumps(event.to_dict()))
                sys.stdout.flush()
            else:
                print(f"[EVENT] {event.id} [{event.topic}] {event.sender} -> {event.recipient}: {json.dumps(event.payload)}")
                sys.stdout.flush()


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

    # doctor subcommand
    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostic health and governance audit")
    doctor_parser.add_argument("path", nargs="?", default=".", help="Target workspace path (default: current dir)")
    doctor_parser.add_argument("--json", action="store_true", help="Output doctor findings as JSON")
    doctor_parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on any warnings or failures")

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

    # bus subcommand
    bus_parser = subparsers.add_parser("bus", help="Interact with volatile multi-agent event bus")
    bus_sub = bus_parser.add_subparsers(dest="bus_action", required=True)

    bus_send = bus_sub.add_parser("send", help="Publish event to volatile bus")
    bus_send.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_send.add_argument("--topic", required=True, help="Event topic (e.g. handoff, review, gate)")
    bus_send.add_argument("--sender", required=True, help="Sender agent name")
    bus_send.add_argument("--recipient", default="*", help="Recipient agent name or '*' for broadcast")
    bus_send.add_argument("--payload", required=True, help="JSON or plain text payload")
    bus_send.add_argument("--ttl", type=int, default=3600, help="Time-to-live in seconds (default: 3600)")

    bus_read = bus_sub.add_parser("read", help="Read events from volatile bus")
    bus_read.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_read.add_argument("--id", help="Read specific event by ID")
    bus_read.add_argument("--topic", help="Filter by topic")
    bus_read.add_argument("--recipient", help="Filter by recipient")
    bus_read.add_argument("--sender", help="Filter by sender")
    bus_read.add_argument("--consume", action="store_true", help="Delete events upon reading")
    bus_read.add_argument("--json", action="store_true", help="Output events as JSON")

    bus_list = bus_sub.add_parser("list", help="List all events in volatile bus")
    bus_list.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_list.add_argument("--json", action="store_true", help="Output list as JSON")

    bus_clear = bus_sub.add_parser("clear", help="Clear all volatile bus events")
    bus_clear.add_argument("path", nargs="?", default=".", help="Workspace root directory")

    bus_watch = bus_sub.add_parser("watch", help="Watch and stream events from volatile bus in real time")
    bus_watch.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_watch.add_argument("--topic", help="Filter by topic")
    bus_watch.add_argument("--recipient", help="Filter by recipient")
    bus_watch.add_argument("--sender", help="Filter by sender")
    bus_watch.add_argument("--timeout", type=float, help="Timeout in seconds before exiting")
    bus_watch.add_argument("--consume", action="store_true", help="Atomically consume events as they arrive")
    bus_watch.add_argument("--json", action="store_true", help="Stream events as JSON Lines")

    # mcp command
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Start native Antigravity MCP Server over stdio or export schemas",
    )
    mcp_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Workspace root directory (default: current directory)",
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
        help="Workspace root directory (default: current directory)",
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

    args = parser.parse_args(argv)

    if args.command == "init":
        handle_init(args)
    elif args.command == "doctor":
        handle_doctor(args)
    elif args.command == "link-global":
        handle_link_global(args)
    elif args.command == "memory":
        handle_memory(args)
    elif args.command == "bus":
        handle_bus(args)
    elif args.command == "mcp":
        handle_mcp(args)
    elif args.command == "pr-review":
        handle_pr_review(args)
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


if __name__ == "__main__":
    main()
