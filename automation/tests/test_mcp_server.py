"""Unit tests for the AGYToolkit native Antigravity MCP Server."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from agy_toolkit.mcp_server import McpServer


class TestMcpServer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        # Initialize memory directories
        self.agents_dir = self.workspace_dir / ".agents"
        self.mem_dir = self.agents_dir / "memory"
        self.bus_dir = self.mem_dir / "volatile-bus"
        self.bus_dir.mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "active-session.md").write_text("# Active Session\n", encoding="utf-8")
        (self.mem_dir / "decisions.md").write_text("# Decisions\n", encoding="utf-8")

        self.server = McpServer(workspace_root=self.workspace_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialize(self):
        """Verify initialize handshake response structure."""
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        res_raw = self.server.process_line(json.dumps(req))
        self.assertIsNotNone(res_raw)
        res = json.loads(res_raw)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 1)
        self.assertEqual(res["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(res["result"]["serverInfo"]["name"], "agy-toolkit-mcp")
        self.assertIn("tools", res["result"]["capabilities"])

    def test_notification_initialized(self):
        """Verify initialized notification produces no response."""
        req = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        res_raw = self.server.process_line(json.dumps(req))
        self.assertIsNone(res_raw)

    def test_ping(self):
        """Verify ping probe returns empty result."""
        req = {
            "jsonrpc": "2.0",
            "id": "ping-42",
            "method": "ping"
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], "ping-42")
        self.assertEqual(res["result"], {})

    def test_tools_list(self):
        """Verify tools/list exposes all required tool contracts."""
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        self.assertIn("agy_doctor", tool_names)
        self.assertIn("agy_memory_status", tool_names)
        self.assertIn("agy_memory_record", tool_names)
        self.assertIn("agy_bus_send", tool_names)
        self.assertIn("agy_bus_read", tool_names)
        self.assertIn("agy_bus_claim", tool_names)

        # Inspect inputSchema contracts
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_tool_call_doctor(self):
        """Verify agy_doctor tool execution."""
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "agy_doctor",
                "arguments": {"strict": False}
            }
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], 3)
        self.assertFalse(res["result"]["isError"])
        self.assertTrue(len(res["result"]["content"]) > 0)
        self.assertEqual(res["result"]["content"][0]["type"], "text")
        self.assertIn("AGYToolkit Diagnostic Audit", res["result"]["content"][0]["text"])

    def test_tool_call_memory_status(self):
        """Verify agy_memory_status tool execution."""
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "agy_memory_status",
                "arguments": {}
            }
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], 4)
        self.assertFalse(res["result"]["isError"])
        text = res["result"]["content"][0]["text"]
        self.assertIn("active-session.md", text)
        self.assertIn("decisions.md", text)

    def test_tool_call_memory_record(self):
        """Verify agy_memory_record appends decisions within budget."""
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "agy_memory_record",
                "arguments": {
                    "decision": "Use JSON-RPC 2.0 stdio transport for native MCP",
                    "category": "ARCH"
                }
            }
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], 5)
        self.assertFalse(res["result"]["isError"])
        self.assertIn("Recorded decision", res["result"]["content"][0]["text"])

        # Check file content
        decisions_content = (self.mem_dir / "decisions.md").read_text(encoding="utf-8")
        self.assertIn("Use JSON-RPC 2.0 stdio transport", decisions_content)

    def test_tool_call_bus_send_and_read(self):
        """Verify inter-agent bus send and read via MCP tools."""
        send_req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "agy_bus_send",
                "arguments": {
                    "topic": "task-handoff",
                    "source": "architect",
                    "payload": {"next_agent": "tdd-architect", "status": "READY"},
                    "ttl_seconds": 3600
                }
            }
        }
        send_res_raw = self.server.process_line(json.dumps(send_req))
        send_res = json.loads(send_res_raw)
        self.assertEqual(send_res["id"], 6)
        self.assertFalse(send_res["result"]["isError"])
        self.assertIn("Published event", send_res["result"]["content"][0]["text"])

        read_req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "agy_bus_read",
                "arguments": {
                    "topic": "task-handoff"
                }
            }
        }
        read_res_raw = self.server.process_line(json.dumps(read_req))
        read_res = json.loads(read_res_raw)
        self.assertEqual(read_res["id"], 7)
        self.assertFalse(read_res["result"]["isError"])
        read_events = json.loads(read_res["result"]["content"][0]["text"])
        self.assertEqual(len(read_events), 1)
        self.assertEqual(read_events[0]["topic"], "task-handoff")
        self.assertEqual(read_events[0]["sender"], "architect")
        self.assertEqual(read_events[0]["payload"]["next_agent"], "tdd-architect")

    def test_tool_call_bus_claim(self):
        """Verify agy_bus_claim atomically claims event."""
        send_req = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": "agy_bus_send",
                "arguments": {"topic": "claim-test", "source": "s", "payload": {"foo": "bar"}}
            }
        }
        send_res = json.loads(self.server.process_line(json.dumps(send_req)))
        self.assertFalse(send_res["result"]["isError"])

        read_req = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {"name": "agy_bus_read", "arguments": {"topic": "claim-test"}}
        }
        events = json.loads(json.loads(self.server.process_line(json.dumps(read_req)))["result"]["content"][0]["text"])
        evt_id = events[0]["id"]

        claim_req = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {"name": "agy_bus_claim", "arguments": {"event_id": evt_id, "claimer": "worker-1"}}
        }
        claim_res = json.loads(self.server.process_line(json.dumps(claim_req)))
        self.assertFalse(claim_res["result"]["isError"])
        claimed_data = json.loads(claim_res["result"]["content"][0]["text"])
        self.assertEqual(claimed_data["id"], evt_id)

        # Second claim attempt must fail
        claim_again = json.loads(self.server.process_line(json.dumps(claim_req)))
        self.assertTrue(claim_again["result"]["isError"])

    def test_tool_call_unknown_tool(self):
        """Verify calling an unknown tool returns isError=True."""
        req = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool",
                "arguments": {}
            }
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], 8)
        self.assertTrue(res["result"]["isError"])
        self.assertIn("Unknown tool", res["result"]["content"][0]["text"])

    def test_parse_error(self):
        """Verify invalid JSON input produces parse error code -32700."""
        res_raw = self.server.process_line("{invalid-json-content")
        res = json.loads(res_raw)
        self.assertIsNone(res["id"])
        self.assertEqual(res["error"]["code"], -32700)
        self.assertEqual(res["error"]["message"], "Parse error")

    def test_invalid_request(self):
        """Verify malformed JSON-RPC request produces code -32600."""
        res_raw = self.server.process_line(json.dumps({"id": 9}))
        res = json.loads(res_raw)
        self.assertEqual(res["error"]["code"], -32600)
        self.assertIn("Invalid Request", res["error"]["message"])

    def test_method_not_found(self):
        """Verify unknown method produces code -32601."""
        req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "unsupported/method",
            "params": {}
        }
        res_raw = self.server.process_line(json.dumps(req))
        res = json.loads(res_raw)
        self.assertEqual(res["id"], 10)
        self.assertEqual(res["error"]["code"], -32601)
        self.assertIn("Method not found", res["error"]["message"])

    def test_export_schemas(self):
        """Verify exporting tool schemas to static directory."""
        schema_dir = self.workspace_dir / "schemas"
        exported = self.server.export_schemas(schema_dir)
        self.assertEqual(len(exported), 6)
        for path in exported:
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("name", data)
            self.assertIn("inputSchema", data)

    def test_run_stdio_stream(self):
        """Verify run_stdio processes stream lines and handles EOF."""
        req1 = json.dumps({"jsonrpc": "2.0", "id": "stream-1", "method": "ping"})
        req2 = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        in_stream = io.StringIO(f"{req1}\n{req2}\n")
        out_stream = io.StringIO()

        self.server.run_stdio(stdin=in_stream, stdout=out_stream)

        lines = [line.strip() for line in out_stream.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        res = json.loads(lines[0])
        self.assertEqual(res["id"], "stream-1")
        self.assertEqual(res["result"], {})


if __name__ == "__main__":
    unittest.main()
