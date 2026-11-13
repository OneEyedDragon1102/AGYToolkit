"""Native Antigravity Model Context Protocol (MCP) Server.

Exposes AGYToolkit health diagnostics, dual-tier memory budgets,
multi-agent volatile IPC event bus, autonomous swarm choreography,
and Tier 3 knowledge full-text search directly to AI agents via stdio JSON-RPC.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agy_toolkit.bus import claim_event, list_events, publish_event
from agy_toolkit.doctor import run_doctor
from agy_toolkit.mcp_knowledge import KNOWLEDGE_TOOLS, handle_knowledge_tool
from agy_toolkit.mcp_multi_repo import MULTI_REPO_TOOLS, handle_multi_repo_tool
from agy_toolkit.mcp_release import RELEASE_TOOLS, handle_release_mcp_tool
from agy_toolkit.mcp_swarm import SWARM_TOOLS, handle_swarm_mcp_tool
from agy_toolkit.memory import check_memory_budgets, record_decision
from agy_toolkit.updater import update_project, format_update_report

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
                            "description": "Binding architectural decision statement.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Decision classification category (default: ARCH).",
                            "default": "ARCH",
                        },
                    },
                },
            },
            {
                "name": "agy_memory_compact",
                "description": "Evaluate memory budgets and auto-compact session and decisions if threshold is exceeded.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "threshold": {
                            "type": "number",
                            "description": "Compaction threshold ratio (0.0 - 1.0, default: 0.85).",
                            "default": 0.85,
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Simulate compaction without writing changes.",
                            "default": False,
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
            {
                "name": "agy_bus_claim",
                "description": "Atomically claim an event on the volatile bus with lease duration to prevent duplicate processing.",
                "inputSchema": {
                    "type": "object",
                    "required": ["event_id", "claimer"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Unique identifier of the event to claim.",
                        },
                        "claimer": {
                            "type": "string",
                            "description": "Identifier of the claiming agent.",
                        },
                        "lease_seconds": {
                            "type": "integer",
                            "description": "Lease duration in seconds (default: 300).",
                            "default": 300,
                        },
                    },
                },
            },
            {
                "name": "agy_bus_heartbeat",
                "description": "Extend active claim lease for a task on volatile bus to signal agent liveness.",
                "inputSchema": {
                    "type": "object",
                    "required": ["event_id", "claimer"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Unique identifier of the claimed event.",
                        },
                        "claimer": {
                            "type": "string",
                            "description": "Identifier of the claiming agent.",
                        },
                        "extend_seconds": {
                            "type": "integer",
                            "description": "Optional new lease duration in seconds.",
                        },
                    },
                },
            },
            {
                "name": "agy_bus_reclaim",
                "description": "Recover expired or orphaned claims on the volatile bus back into active events.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grace_seconds": {
                            "type": "number",
                            "description": "Grace period in seconds beyond the lease expiration (default: 0.0).",
                            "default": 0.0,
                        },
                    },
                },
            },
            {
                "name": "agy_update",
                "description": "Refresh downstream skills, agents, and hooks from AGYToolkit core non-destructively.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dry_run": {
                            "type": "boolean",
                            "description": "Simulate updates without modifying filesystem.",
                            "default": False,
                        },
                        "force_rules": {
                            "type": "boolean",
                            "description": "Force refresh GEMINI.md and AGENTS.md rules from base templates.",
                            "default": False,
                        },
                    },
                },
            },
        ] + SWARM_TOOLS + KNOWLEDGE_TOOLS + MULTI_REPO_TOOLS + RELEASE_TOOLS

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Tuple[str, bool]:
        """Dispatch tool invocation and return (content_text, is_error)."""
        try:
            swarm_res = handle_swarm_mcp_tool(name, arguments, self.mem_dir)
            if swarm_res is not None:
                return swarm_res

            know_res = handle_knowledge_tool(self.workspace_root, name, arguments)
            if know_res is not None:
                text = know_res["content"][0]["text"]
                return text, False

            multi_res = handle_multi_repo_tool(self.workspace_root, name, arguments)
            if multi_res is not None:
                return multi_res

            release_res = handle_release_mcp_tool(self.workspace_root, name, arguments)
            if release_res is not None:
                return release_res

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

            if name == "agy_memory_compact":
                from agy_toolkit.memory import auto_compact_memory, format_compact_report

                threshold = float(arguments.get("threshold", 0.85))
                dry_run = bool(arguments.get("dry_run", False))
                report = auto_compact_memory(
                    memory_dir=self.mem_dir,
                    threshold=threshold,
                    workspace_root=self.workspace_root,
                    dry_run=dry_run,
                )
                return format_compact_report(report), False

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

            if name == "agy_bus_claim":
                event_id = arguments.get("event_id")
                claimer = arguments.get("claimer")
                lease_seconds = int(arguments.get("lease_seconds", 300))
                if not event_id or not claimer:
                    return "Error: 'event_id' and 'claimer' are required.", True
                claimed = claim_event(
                    event_id=event_id,
                    claimer=claimer,
                    lease_seconds=lease_seconds,
                    memory_dir=self.mem_dir,
                )
                if claimed is None:
                    return f"Event {event_id} could not be claimed (already claimed or does not exist).", True
                return json.dumps(claimed.to_dict(), indent=2), False

            if name == "agy_bus_heartbeat":
                from agy_toolkit.bus import heartbeat_claim

                event_id = arguments.get("event_id")
                claimer = arguments.get("claimer")
                extend_seconds = arguments.get("extend_seconds")
                if not event_id or not claimer:
                    return "Error: 'event_id' and 'claimer' are required.", True
                success = heartbeat_claim(
                    event_id=event_id,
                    claimer=claimer,
                    extend_seconds=extend_seconds,
                    memory_dir=self.mem_dir,
                )
                if not success:
                    return f"Failed to refresh heartbeat for event '{event_id}'. Lock missing or claimer mismatch.", True
                return f"Heartbeat refreshed for event '{event_id}' by claimer '{claimer}'.", False

            if name == "agy_bus_reclaim":
                from agy_toolkit.bus import reclaim_expired_claims

                grace = float(arguments.get("grace_seconds", 0.0) or 0.0)
                reclaimed = reclaim_expired_claims(
                    memory_dir=self.mem_dir,
                    grace_seconds=grace,
                )
                return json.dumps({
                    "reclaimed_count": len(reclaimed),
                    "reclaimed_events": reclaimed,
                }, indent=2), False

            if name == "agy_update":
                dry_run = bool(arguments.get("dry_run", False))
                force_rules = bool(arguments.get("force_rules", False))
                report = update_project(
                    target_path=self.workspace_root,
                    dry_run=dry_run,
                    force_rules=force_rules,
                )
                return format_update_report(report), not report.success

            return f"Unknown tool: '{name}'.", True
        except Exception as ex:
            return f"Tool execution failed: {str(ex)}", True

    def process_line(self, line: str) -> Optional[str]:
        """Parse and handle a single line containing a JSON-RPC 2.0 message."""
        line = line.strip()
        if not line:
            return None

        try:
            req = json.loads(line)
        except Exception as ex:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(ex)}",
                },
            })

        req_id = req.get("id")
        method = req.get("method")
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
