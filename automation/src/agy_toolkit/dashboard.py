"""AGYToolkit Diagnostic Terminal & Web Dashboard Engine.

Provides real-time terminal TUI cockpit and browser-based operational dashboard
for inspecting host toolchains, governance gates, dual-tier memory budgets,
and multi-agent volatile bus traffic.
"""

import http.server
import json
import socketserver
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.agents import list_agents
from agy_toolkit.bus import list_events
from agy_toolkit.doctor import run_doctor
from agy_toolkit.memory import check_memory_budgets


def render_gauge(current: int, max_val: int, width: int = 20) -> str:
    """Render a text-based progress bar gauge with percentage indicator."""
    if max_val <= 0:
        pct = 0.0
        filled = 0
    else:
        pct = (current / max_val) * 100.0
        ratio = min(1.0, max(0.0, current / max_val))
        filled = int(round(ratio * width))

    empty = width - filled
    bar = "=" * filled + "-" * empty
    return f"[{bar}] {pct:5.1f}%"


def collect_dashboard_metrics(workspace_root: Optional[Path] = None) -> Dict[str, Any]:
    """Gather diagnostic metrics across toolchains, governance, memory, and bus."""
    ws = Path(workspace_root or ".").resolve()
    mem_dir = ws / ".agents" / "memory"
    sessions_dir = mem_dir / "sessions"
    adr_file = ws / "docs" / "adr" / "decisions-history.md"

    # 1. Run doctor diagnostics
    doctor_report = run_doctor(target_path=ws)
    toolchains = []
    governance = []
    for item in doctor_report.results:
        entry = {
            "category": item.category,
            "name": item.name,
            "status": item.status,
            "details": item.details,
        }
        if item.category == "Toolchain":
            toolchains.append(entry)
        else:
            governance.append(entry)

    # 2. Check memory metrics
    budgets = check_memory_budgets(mem_dir)
    act_data = budgets.get("active_session", {"bytes": 0, "cap": 1024, "within_budget": True})
    dec_data = budgets.get("decisions", {"bytes": 0, "cap": 3072, "within_budget": True})

    session_archives = len(list(sessions_dir.glob("*.md"))) if sessions_dir.exists() else 0
    adr_entries = 0
    if adr_file.exists():
        adr_lines = adr_file.read_text(encoding="utf-8").splitlines()
        adr_entries = sum(1 for line in adr_lines if line.strip().startswith("- **"))

    act_ratio = act_data["bytes"] / act_data["cap"] if act_data["cap"] else 0
    dec_ratio = dec_data["bytes"] / dec_data["cap"] if dec_data["cap"] else 0
    max_ratio = max(act_ratio, dec_ratio)

    if max_ratio > 1.0:
        mem_status = "CRITICAL"
    elif max_ratio >= 0.85:
        mem_status = "NEEDS_COMPACT"
    elif max_ratio >= 0.70:
        mem_status = "WARNING"
    else:
        mem_status = "OPTIMAL"

    # 3. Volatile Bus metrics
    bus_events = list_events(memory_dir=mem_dir)
    bus_claimed = sum(1 for e in bus_events if getattr(e, "claimed_by", None))

    # 4. Agent and Skill metrics
    agents = list_agents()

    return {
        "workspace": str(ws),
        "doctor_healthy": doctor_report.is_healthy,
        "passed_checks": doctor_report.passed_count,
        "failed_checks": doctor_report.failure_count,
        "warning_checks": doctor_report.warning_count,
        "toolchains": toolchains,
        "governance": governance,
        "memory": {
            "status": mem_status,
            "active_session_bytes": act_data["bytes"],
            "active_session_cap": act_data["cap"],
            "active_session_within": act_data["within_budget"],
            "decisions_bytes": dec_data["bytes"],
            "decisions_cap": dec_data["cap"],
            "decisions_within": dec_data["within_budget"],
            "session_archives_count": session_archives,
            "adr_history_count": adr_entries,
        },
        "bus": {
            "active_events_count": len(bus_events),
            "claimed_events_count": bus_claimed,
            "recent_events": [e.to_dict() for e in bus_events[:5]],
        },
        "agents_count": len(agents),
        "skills_count": 28,
    }


def render_tui(workspace_root: Optional[Path] = None) -> str:
    """Format full operational dashboard into high-signal terminal display."""
    metrics = collect_dashboard_metrics(workspace_root)
    mem = metrics["memory"]
    bus = metrics["bus"]

    sep = "=" * 78
    sub_sep = "-" * 78

    lines = [
        sep,
        " AGYToolkit Operational Cockpit & Diagnostic Health Monitor",
        f" Workspace: {metrics['workspace']}",
        sep,
        "",
        "[1] Toolchains & Runtime Environment",
        sub_sep,
    ]

    for tc in metrics["toolchains"]:
        status_box = f"[{tc['status']}]"
        lines.append(f"  {status_box:8} {tc['name']:18} : {tc['details']}")

    lines.extend([
        "",
        "[2] Governance, Rules & Quality Gates",
        sub_sep,
    ])
    for gov in metrics["governance"][:6]:
        status_box = f"[{gov['status']}]"
        lines.append(f"  {status_box:8} {gov['name']:18} : {gov['details']}")

    lines.extend([
        "",
        "[3] Dual-Tier Memory HUD & Budget Gauges",
        sub_sep,
        f"  Overall Memory Status : {mem['status']}",
        f"  Active Session        : {render_gauge(mem['active_session_bytes'], mem['active_session_cap'])} ({mem['active_session_bytes']}/{mem['active_session_cap']} B)",
        f"  Decisions Register    : {render_gauge(mem['decisions_bytes'], mem['decisions_cap'])} ({mem['decisions_bytes']}/{mem['decisions_cap']} B)",
        f"  Archived Sessions     : {mem['session_archives_count']} snapshot(s) in .agents/memory/sessions/",
        f"  Evicted ADR History   : {mem['adr_history_count']} record(s) in docs/adr/decisions-history.md",
        "",
        "[4] Volatile IPC Event Bus & Autonomous Swarm",
        sub_sep,
        f"  Active Bus Envelopes  : {bus['active_events_count']} active ({bus['claimed_events_count']} claimed)",
        f"  Specialist Subagents  : {metrics['agents_count']} universal agents registered",
        f"  Progressive Skills    : {metrics['skills_count']} SDLC skills mounted across 5 tracks",
    ])

    if bus["recent_events"]:
        lines.append("\n  Recent IPC Events:")
        for e in bus["recent_events"]:
            lines.append(f"    * {e.get('id', '')} [{e.get('topic', '')}] {e.get('sender', '')} -> {e.get('recipient', '')}")

    lines.extend([
        "",
        sep,
        " Health Summary: "
        + f"Passed: {metrics['passed_checks']}, "
        + f"Warnings: {metrics['warning_checks']}, "
        + f"Failures: {metrics['failed_checks']} "
        + f"| System: {'HEALTHY' if metrics['doctor_healthy'] else 'DEGRADED'}",
        sep,
    ])

    return "\n".join(lines)


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving dashboard assets and live diagnostic JSON API."""

    def __init__(self, *args, workspace_root: Optional[Path] = None, docs_dir: Optional[Path] = None, **kwargs):
        self.workspace_root = workspace_root
        self.docs_dir = str(docs_dir) if docs_dir else "."
        super().__init__(*args, directory=self.docs_dir, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = collect_dashboard_metrics(self.workspace_root)
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
        else:
            super().do_GET()

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep terminal clean
        pass


def launch_web_dashboard(
    workspace_root: Optional[Path] = None,
    port: int = 8765,
    open_browser: bool = True,
    docs_dir: Optional[Path] = None,
) -> None:
    """Launch local HTTP server and display the web dashboard in browser."""
    ws = Path(workspace_root or ".").resolve()
    target_docs = docs_dir or (Path(__file__).resolve().parent.parent.parent.parent / "docs")

    if not target_docs.exists():
        print(f"[Error] Docs directory not found at: {target_docs}")
        sys.exit(1)

    handler = lambda *args, **kwargs: DashboardRequestHandler(
        *args, workspace_root=ws, docs_dir=target_docs, **kwargs
    )

    # Enable socket reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}/"
        print("=" * 68)
        print(" [AGYToolkit] Operational Web Dashboard Online")
        print(f" URL: {url}")
        print(" Press Ctrl+C to stop local dashboard server.")
        print("=" * 68)

        if open_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[AGYToolkit] Stopping dashboard server...")
            httpd.server_close()
