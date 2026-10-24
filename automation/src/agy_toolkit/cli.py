"""AGYToolkit CLI - Command line utility for AGY ecosystem inspection and recipes."""

import argparse
import sys
from typing import List

from agy_toolkit.agents import list_agents

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


def main(argv: List[str] = None):
    # Ensure safe encoding for Windows command line output when running standalone
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="agy-toolkit",
        description="AGYToolkit CLI: Tools and inspection utilities for AGY.",
    )
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

    if args.list_agents:
        print_agents()
    elif args.list_tools or (argv is not None and len(argv) == 0) or len(sys.argv) == 1:
        print_catalog()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
