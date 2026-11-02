"""Integration and CLI tests for memory and bus subcommands."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.memory import ensure_memory_dirs, update_active_session


class TestMemoryAndBusCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.mem_dir = self.root / ".agents" / "memory"
        ensure_memory_dirs(self.mem_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_cli(self, args_list):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(args_list)
        return buf.getvalue()

    def test_memory_status_text_and_json(self):
        """Verify 'agy-toolkit memory status' returns metrics."""
        update_active_session("Test Goal", "feature/test", "agent-x", ["file1.py"], "Step 1", memory_dir=self.mem_dir)

        # Text output
        out = self._run_cli(["memory", "status", str(self.root)])
        self.assertIn("Active Session", out)
        self.assertIn("Decisions Register", out)
        self.assertIn("[PASS]", out)

        # JSON output
        json_out = self._run_cli(["memory", "status", str(self.root), "--json"])
        data = json.loads(json_out)
        self.assertIn("active_session", data)
        self.assertIn("decisions", data)
        self.assertTrue(data["active_session"]["within_budget"])

    def test_memory_record_and_flush(self):
        """Verify recording decisions and flushing active session."""
        # 1. Record decision
        self._run_cli([
            "memory", "record", str(self.root),
            "--category", "ARCH",
            "--decision", "Use Hexagonal Architecture for Spring Boot microservices.",
        ])

        decisions_file = self.mem_dir / "decisions.md"
        self.assertTrue(decisions_file.exists())
        content = decisions_file.read_text(encoding="utf-8")
        self.assertIn("[ARCH]", content)
        self.assertIn("Hexagonal Architecture", content)

        # 2. Flush active session with archive
        update_active_session("Goal 1", "main", "orch", ["a.ts"], "Done", memory_dir=self.mem_dir)
        flush_out = self._run_cli(["memory", "flush", str(self.root)])
        self.assertIn("flushed and archived", flush_out)

        # Verify archive created in sessions/
        archives = list((self.mem_dir / "sessions").glob("*.md"))
        self.assertGreaterEqual(len(archives), 1)

        # 3. Flush without archive
        flush_no_arc = self._run_cli(["memory", "flush", str(self.root), "--no-archive"])
        self.assertIn("flushed to clean state", flush_no_arc)

    def test_bus_send_read_list_clear(self):
        """Verify full lifecycle of volatile bus CLI."""
        # 1. Send event
        send_out = self._run_cli([
            "bus", "send", str(self.root),
            "--topic", "review",
            "--sender", "code-reviewer",
            "--recipient", "node-ts-engineer",
            "--payload", '{"findings": 0, "status": "APPROVED"}',
        ])
        self.assertIn("Published event", send_out)
        self.assertIn("topic 'review'", send_out)

        # 2. List events
        list_out = self._run_cli(["bus", "list", str(self.root)])
        self.assertIn("Active events on volatile bus: 1", list_out)
        self.assertIn("code-reviewer -> node-ts-engineer", list_out)

        # 3. Read events with filter
        read_out = self._run_cli([
            "bus", "read", str(self.root),
            "--topic", "review",
            "--recipient", "node-ts-engineer",
            "--json",
        ])
        events = json.loads(read_out)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["payload"]["status"], "APPROVED")

        # 4. Clear bus
        clear_out = self._run_cli(["bus", "clear", str(self.root)])
        self.assertIn("Cleared 1 event payload(s)", clear_out)

        # Verify 0 events remaining
        empty_list = self._run_cli(["bus", "list", str(self.root)])
        self.assertIn("Active events on volatile bus: 0", empty_list)


if __name__ == "__main__":
    unittest.main()
