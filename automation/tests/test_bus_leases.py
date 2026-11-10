"""Unit and concurrency tests for Task Lease Expiration, Heartbeats, and Self-Healing Event Bus."""

import datetime
import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.bus import (
    claim_event,
    complete_claimed_event,
    get_claim_status,
    heartbeat_claim,
    list_claims,
    publish_event,
    read_event,
    reclaim_expired_claims,
)
from agy_toolkit.cli import main
from agy_toolkit.mcp_server import McpServer


class TestBusLeases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        self.bus_dir = self.mem_dir / "volatile-bus"
        self.bus_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_claim_records_lease_and_payload_metadata(self):
        """Verify claim creates .claim lock with full payload envelope and lease metrics."""
        evt = publish_event(
            topic="unit-test",
            sender="tester",
            payload={"msg": "hello"},
            memory_dir=self.mem_dir,
        )
        claimed = claim_event(
            event_id=evt.id,
            claimer="agent-alpha",
            lease_seconds=120,
            memory_dir=self.mem_dir,
        )
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.id, evt.id)

        # Ensure .json is unlinked and .claim exists
        self.assertFalse((self.bus_dir / f"{evt.id}.json").exists())
        claim_file = self.bus_dir / f"{evt.id}.claim"
        self.assertTrue(claim_file.exists())

        claim_data = json.loads(claim_file.read_text(encoding="utf-8"))
        self.assertEqual(claim_data["claimer"], "agent-alpha")
        self.assertEqual(claim_data["lease_seconds"], 120)
        self.assertIn("claimed_at", claim_data)
        self.assertIn("heartbeat_at", claim_data)
        self.assertEqual(claim_data["event"]["payload"], {"msg": "hello"})

    def test_heartbeat_extends_claim_lease(self):
        """Verify heartbeat_claim refreshes heartbeat timestamp and updates lease duration."""
        evt = publish_event(
            topic="long-task",
            sender="tester",
            payload={"run": "build"},
            memory_dir=self.mem_dir,
        )
        claim_event(evt.id, claimer="worker-1", lease_seconds=10, memory_dir=self.mem_dir)

        # Allow slight delta
        time.sleep(0.05)
        success = heartbeat_claim(
            event_id=evt.id,
            claimer="worker-1",
            extend_seconds=600,
            memory_dir=self.mem_dir,
        )
        self.assertTrue(success)

        status = get_claim_status(evt.id, memory_dir=self.mem_dir)
        self.assertIsNotNone(status)
        self.assertEqual(status["lease_seconds"], 600)
        self.assertFalse(status["is_expired"])
        self.assertGreater(status["remaining_seconds"], 500)

    def test_heartbeat_rejects_unauthorized_agent(self):
        """Verify heartbeat rejects non-owning claimer agents."""
        evt = publish_event(topic="secure", sender="tester", payload={}, memory_dir=self.mem_dir)
        claim_event(evt.id, claimer="worker-legit", memory_dir=self.mem_dir)

        impostor_result = heartbeat_claim(
            event_id=evt.id,
            claimer="worker-impostor",
            memory_dir=self.mem_dir,
        )
        self.assertFalse(impostor_result)

    def test_reclaim_ignores_unexpired_claims(self):
        """Verify unexpired active claims are preserved by reclaimer sweep."""
        evt = publish_event(topic="active", sender="tester", payload={}, memory_dir=self.mem_dir)
        claim_event(evt.id, claimer="worker-busy", lease_seconds=300, memory_dir=self.mem_dir)

        reclaimed = reclaim_expired_claims(memory_dir=self.mem_dir, grace_seconds=0.0)
        self.assertEqual(len(reclaimed), 0)
        self.assertTrue((self.bus_dir / f"{evt.id}.claim").exists())
        self.assertFalse((self.bus_dir / f"{evt.id}.json").exists())

    def test_reclaim_recovers_expired_claim_and_provenance(self):
        """Verify timed-out claims are resurrected with audit provenance metadata."""
        evt = publish_event(
            topic="stalled-task",
            sender="orchestrator",
            payload={"step": 2},
            memory_dir=self.mem_dir,
        )
        claim_event(evt.id, claimer="crashed-agent", lease_seconds=10, memory_dir=self.mem_dir)

        # Simulate expired timestamp in the lock file (120s ago)
        claim_file = self.bus_dir / f"{evt.id}.claim"
        claim_data = json.loads(claim_file.read_text(encoding="utf-8"))
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=120)).isoformat()
        claim_data["heartbeat_at"] = old_time
        claim_data["claimed_at"] = old_time
        claim_file.write_text(json.dumps(claim_data), encoding="utf-8")

        # Run self-healing sweep
        reclaimed = reclaim_expired_claims(memory_dir=self.mem_dir, grace_seconds=5.0)
        self.assertEqual(len(reclaimed), 1)
        self.assertEqual(reclaimed[0]["id"], evt.id)
        self.assertEqual(reclaimed[0]["claimer"], "crashed-agent")

        # Claim lock should be removed and event restored
        self.assertFalse(claim_file.exists())
        restored_file = self.bus_dir / f"{evt.id}.json"
        self.assertTrue(restored_file.exists())

        restored_evt = read_event(evt.id, memory_dir=self.mem_dir)
        self.assertIsNotNone(restored_evt)
        self.assertEqual(restored_evt.metadata["reclaimed_from"], "crashed-agent")
        self.assertEqual(restored_evt.metadata["reclaim_count"], 1)

        # Verify another agent can now claim the restored event
        claimed_again = claim_event(evt.id, claimer="recovery-agent", memory_dir=self.mem_dir)
        self.assertIsNotNone(claimed_again)
        self.assertEqual(claimed_again.metadata["reclaim_count"], 1)

    def test_list_claims_returns_active_and_expired(self):
        """Verify list_claims returns comprehensive status across all locks."""
        evt1 = publish_event(topic="t1", sender="s", payload={}, memory_dir=self.mem_dir)
        evt2 = publish_event(topic="t2", sender="s", payload={}, memory_dir=self.mem_dir)

        claim_event(evt1.id, claimer="worker-a", lease_seconds=100, memory_dir=self.mem_dir)
        claim_event(evt2.id, claimer="worker-b", lease_seconds=200, memory_dir=self.mem_dir)

        claims = list_claims(memory_dir=self.mem_dir)
        self.assertEqual(len(claims), 2)
        claimers = {c["claimer"] for c in claims}
        self.assertEqual(claimers, {"worker-a", "worker-b"})

    def test_cli_heartbeat_and_reclaim_commands(self):
        """Verify agy-toolkit bus heartbeat and reclaim CLI commands."""
        evt = publish_event(topic="cli-test", sender="s", payload={}, memory_dir=self.mem_dir)
        claim_event(evt.id, claimer="cli-worker", lease_seconds=50, memory_dir=self.mem_dir)

        # 1. Heartbeat CLI
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["bus", "heartbeat", str(self.workspace_dir), "--id", evt.id, "--claimer", "cli-worker", "--extend", "150"])
        self.assertEqual(ret, 0)
        self.assertIn("Heartbeat refreshed for event", f.getvalue())

        # 2. Simulate expired and run reclaim CLI with JSON output
        claim_file = self.bus_dir / f"{evt.id}.claim"
        data = json.loads(claim_file.read_text(encoding="utf-8"))
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=500)).isoformat()
        data["heartbeat_at"] = old_time
        claim_file.write_text(json.dumps(data), encoding="utf-8")

        f2 = io.StringIO()
        with redirect_stdout(f2):
            ret2 = main(["bus", "reclaim", str(self.workspace_dir), "--json"])
        self.assertEqual(ret2, 0)
        reclaimed_json = json.loads(f2.getvalue())
        self.assertEqual(len(reclaimed_json), 1)
        self.assertEqual(reclaimed_json[0]["id"], evt.id)

    def test_mcp_heartbeat_and_reclaim_tools(self):
        """Verify native MCP server tools agy_bus_heartbeat and agy_bus_reclaim."""
        server = McpServer(workspace_root=self.workspace_dir)
        evt = publish_event(topic="mcp-test", sender="s", payload={}, memory_dir=self.mem_dir)
        claim_event(evt.id, claimer="mcp-worker", lease_seconds=50, memory_dir=self.mem_dir)

        # 1. MCP heartbeat tool call
        res_text, is_err = server.execute_tool("agy_bus_heartbeat", {
            "event_id": evt.id,
            "claimer": "mcp-worker",
            "extend_seconds": 200,
        })
        self.assertFalse(is_err)
        self.assertIn("Heartbeat refreshed", res_text)

        # 2. Simulate expiration and call MCP reclaim tool
        claim_file = self.bus_dir / f"{evt.id}.claim"
        data = json.loads(claim_file.read_text(encoding="utf-8"))
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=600)).isoformat()
        data["heartbeat_at"] = old_time
        claim_file.write_text(json.dumps(data), encoding="utf-8")

        reclaim_text, is_err2 = server.execute_tool("agy_bus_reclaim", {"grace_seconds": 0.0})
        self.assertFalse(is_err2)
        reclaim_resp = json.loads(reclaim_text)
        self.assertEqual(reclaim_resp["reclaimed_count"], 1)


if __name__ == "__main__":
    unittest.main()
