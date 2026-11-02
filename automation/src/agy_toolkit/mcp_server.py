"""Native Antigravity Model Context Protocol (MCP) Server.

Exposes AGYToolkit health diagnostics, dual-tier memory budgets,
and multi-agent volatile IPC event bus directly to AI agents via stdio JSON-RPC.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agy_toolkit.bus import list_events, publish_event
from agy_toolkit.doctor import run_doctor
from agy_toolkit.memory import check_memory_budgets, record_decision

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "agy-toolkit-mcp"
SERVER_VERSION = "0.1.0"


class McpServer:
    """Standard I/O Model Context Protocol (MCP) server for AGYToolkit."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.mem_dir = self.workspace_root / ".agents" / "memory"

    def get_tools_metadata(self) -> List[Dict[str, Any]]:
        """Return MCP tool descriptors and JSON schema definitions."""
        return [
            {
                "name": "agy_doctor",
                "description": "Execute diagnostic health check and governance audit on the environment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strict": {
                            "type": "boolean",
                            "description": "Enforce strict zero-warning mode for CI/CD gates.",
                            "default": False,
                        }
                    },
                },
            },
            {
                "name": "agy_memory_status",
                "description": "Query memory budget consumption for active-session.md and decisions.md.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "agy_memory_record",
                "description": "Record a binding architectural decision into decisions.md within budget.",
                "inputSchema": {
                    "type": "object",
                    "required": ["decision"],
                    "properties": {
                        "decision": {
                            "type": "string",
                            "description": "The architectural decision statement to record.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Category prefix (e.g. ARCH, GOV, DIST, BUS, TDD).",
                            "default": "ARCH",
                        },
                    },
                },
            },
            {
                "name": "agy_bus_send",
                "description": "Publish a structured JSON event envelope to the volatile multi-agent IPC bus.",
                "inputSchema": {
                    "type": "object",
                    "required": ["topic", "source", "payload"],
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Channel topic name (e.g. task-handoff, lint-alert).",
                        },
                        "source": {
                            "type": "string",
                            "description": "Sender agent identifier.",
                        },
                        "payload": {
                            "type": "object",
                            "description": "Structured dictionary payload for the event.",
                        },
                        "recipient": {
                            "type": "string",
                            "description": "Optional destination agent identifier.",
                        },
                        "ttl_seconds": {
                            "type": "integer",
                            "description": "Event time-to-live in seconds before auto-prune.",
                            "default": 3600,
                        },
                    },
                },
            },
            {
                "name": "agy_bus_read",
                "description": "Read and list active non-expired events on the volatile IPC bus.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Optional topic filter.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of events to retrieve.",
                            "default": 10,
                        },
                    },
                },
            },
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Tuple[str, bool]:
        """Dispatch tool invocation and return (content_text, is_error)."""
        try:
            if name == "agy_doctor":
                strict = bool(arguments.get("strict", False))
                report = run_doctor(target_path=self.workspace_root)
                healthy = (report.warning_count == 0 and report.failure_count == 0) if strict else report.is_healthy
                lines = [
                    f"# AGYToolkit Diagnostic Audit (Healthy: {healthy})",
                    f"- Passed: {report.passed_count}, Failures: {report.failure_count}, Warnings: {report.warning_count}",
                    "",
                    "## Diagnostic Checks",
                ]
                for item in report.results:
                    lines.append(f"- [{item.status}] {item.category} / {item.name}: {item.details}")
                return "\n".join(lines), not healthy

            if name == "agy_memory_status":
                budgets = check_memory_budgets(self.mem_dir)
                act = budgets["active_session"]
                dec = budgets["decisions"]
                passed = act["within_budget"] and dec["within_budget"]
                lines = [
                    "# AGYToolkit Memory Budget Status",
                    f"- Status: {'PASS' if passed else 'FAIL'}",
                    f"- active-session.md: {act['bytes']} / {act['cap']} bytes ({'PASS' if act['within_budget'] else 'OVER BUDGET'})",
                    f"- decisions.md: {dec['bytes']} / {dec['cap']} bytes ({'PASS' if dec['within_budget'] else 'OVER BUDGET'})",
                ]
                return "\n".join(lines), not passed

            if name == "agy_memory_record":
                decision = arguments.get("decision")
                if not decision:
                    return "Error: Missing required argument 'decision'.", True
                category = arguments.get("category", "ARCH")
                record_decision(
                    category=category,
                    decision=decision,
                    memory_dir=self.mem_dir,
                )
                return f"Recorded decision: [{category}] {decision}", False

            if name == "agy_bus_send":
                topic = arguments.get("topic")
                source = arguments.get("source")
                payload = arguments.get("payload")
                if not topic or not source or payload is None:
                    return "Error: 'topic', 'source', and 'payload' are required.", True
                recipient = arguments.get("recipient")
                ttl_seconds = int(arguments.get("ttl_seconds", 3600))

                evt = publish_event(
                    topic=topic,
                    sender=source,
                    payload=payload,
                    recipient=recipient,
                    ttl_seconds=ttl_seconds,
                    memory_dir=self.mem_dir,
                )
                return f"Published event {evt.id} on topic '{evt.topic}' (ttl: {evt.ttl_seconds}s).", False

            if name == "agy_bus_read":
                topic = arguments.get("topic")
                limit = int(arguments.get("limit", 10))
                events = list_events(topic=topic, memory_dir=self.mem_dir)
                sliced = events[:limit]
                serialized = [e.to_dict() for e in sliced]
                return json.dumps(serialized, indent=2), False

            return f"Unknown tool: '{name}'.", True
        except Exception as ex:
            return f"Tool execution failed: {str(ex)}", True

    def process_line(self, line: str) -> Optional[str]:
        """Parse and handle a single line containing a JSON-RPC 2.0 message."""
        raw = line.strip()
        if not raw:
            return None

        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                },
            })

        if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or "method" not in req:
            req_id = req.get("id") if isinstance(req, dict) else None
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: missing jsonrpc or method",
                },
            })

        req_id = req.get("id")
        method = req["method"]
        params = req.get("params", {})

        # Handle notifications (requests without id)
        if req_id is None:
            if method == "notifications/initialized":
                return None
            return None

        # Handle requests
        if method == "initialize":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            })

        if method == "ping":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            })

        if method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.get_tools_metadata(),
                },
            })

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            content_text, is_error = self.execute_tool(tool_name, arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text,
                        }
                    ],
                    "isError": is_error,
                },
            })

        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        })

    def run_stdio(self, stdin=sys.stdin, stdout=sys.stdout) -> None:
        """Run JSON-RPC loop reading from standard input and writing to standard output."""
        for line in stdin:
            res = self.process_line(line)
            if res:
                stdout.write(res + "\n")
                stdout.flush()

    def export_schemas(self, output_dir: Path) -> List[Path]:
        """Export tool definitions as static JSON schema files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        created = []
        for tool in self.get_tools_metadata():
            target = output_dir / f"{tool['name']}.json"
            target.write_text(json.dumps(tool, indent=2) + "\n", encoding="utf-8")
            created.append(target)
        return created
