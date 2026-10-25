"""AGYToolkit CLI - Command line utility for AGY ecosystem inspection, management, and project scaffolding."""

import argparse
import sys
from pathlib import Path
from typing import List

from agy_toolkit.agents import list_agents
from agy_toolkit.scaffolder import scaffold_project

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
    print(" [AGYToolkit] Governed Specialist Subagents (15 Matrix)")
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
    print(f"   - {res['hooks_installed']} lifecycle hook scripts in .agents/hooks/")
    print(f"   - Active session memory initialized (gitignored)")
    print(f"   - GEMINI.md and AGENTS.md project rules generated")
    print("\nNext step: Open this workspace in AGY to activate autonomous governance.")
    print("=" * 60)


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

    args = parser.parse_args(argv)

    if args.command == "init":
        handle_init(args)
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
