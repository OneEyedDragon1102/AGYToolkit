"""Unit tests for the AGYToolkit volatile event bus and inter-agent communication."""

import datetime
import json
import tempfile
import unittest
from pathlib import Path

from agy_toolkit.bus import (
    BusEvent,
    publish_event,
    read_event,
    list_events,
    consume_events,
    prune_expired_events,
    clear_bus,
)


class TestBus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_publish_and_read_event(self):
        """Verify publishing an event and reading it by id."""
        payload = {"task": "run-linter", "severity": "HIGH"}
        evt = publish_event(
            topic="code-review",
            sender="code-reviewer",
            payload=payload,
            recipient="orchestrator",
            ttl_seconds=1800,
            memory_dir=self.mem_dir,
        )

        self.assertIsNotNone(evt.id)
        self.assertEqual(evt.topic, "code-review")
        self.assertEqual(evt.sender, "code-reviewer")
        self.assertEqual(evt.recipient, "orchestrator")
        self.assertEqual(evt.payload["task"], "run-linter")

        # Read back
        read_back = read_event(evt.id, memory_dir=self.mem_dir)
        self.assertIsNotNone(read_back)
        self.assertEqual(read_back.id, evt.id)
        self.assertEqual(read_back.payload, payload)

    def test_consume_event_deletes_file(self):
        """Verify read with consume=True deletes the payload."""
        evt = publish_event(
            topic="handoff",
            sender="planner-architect",
            payload="proceed-to-tdd",
            memory_dir=self.mem_dir,
        )

        read_first = read_event(evt.id, consume=True, memory_dir=self.mem_dir)
        self.assertIsNotNone(read_first)

        # Second read should return None
        read_second = read_event(evt.id, memory_dir=self.mem_dir)
        self.assertIsNone(read_second)

    def test_list_and_filter_events(self):
        """Verify filtering events by topic, recipient, and sender."""
        publish_event("gate", "security-auditor", "pass", recipient="orchestrator", memory_dir=self.mem_dir)
        publish_event("gate", "anti-bloat-sentinel", "pass", recipient="orchestrator", memory_dir=self.mem_dir)
        publish_event("build", "spring-boot-engineer", "success", recipient="orchestrator", memory_dir=self.mem_dir)
        publish_event("gate", "security-auditor", "pass", recipient="git-craftsman", memory_dir=self.mem_dir)

        # Filter by topic
        gate_events = list_events(topic="gate", memory_dir=self.mem_dir)
        self.assertEqual(len(gate_events), 3)

        # Filter by sender
        sec_events = list_events(sender="security-auditor", memory_dir=self.mem_dir)
        self.assertEqual(len(sec_events), 2)

        # Filter by recipient
        git_events = list_events(recipient="git-craftsman", memory_dir=self.mem_dir)
        self.assertEqual(len(git_events), 1)

    def test_wildcard_recipient_matches_any(self):
        """Verify recipient '*' matches when filtering by recipient."""
        publish_event("broadcast", "orchestrator", "all-halt", recipient="*", memory_dir=self.mem_dir)

        events_for_agent = list_events(recipient="spring-boot-engineer", memory_dir=self.mem_dir)
        self.assertEqual(len(events_for_agent), 1)
        self.assertEqual(events_for_agent[0].payload, "all-halt")

    def test_consume_events_clears_matching(self):
        """Verify consume_events retrieves and deletes matching items."""
        publish_event("queue", "agent-a", 1, memory_dir=self.mem_dir)
        publish_event("queue", "agent-b", 2, memory_dir=self.mem_dir)
        publish_event("other", "agent-a", 3, memory_dir=self.mem_dir)

        consumed = consume_events(topic="queue", memory_dir=self.mem_dir)
        self.assertEqual(len(consumed), 2)

        remaining = list_events(memory_dir=self.mem_dir)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].topic, "other")

    def test_ttl_expiration_and_pruning(self):
        """Verify expired events are omitted and pruned."""
        evt = publish_event("short-lived", "timer", "tick", ttl_seconds=1, memory_dir=self.mem_dir)

        # Simulate expiration
        future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5)
        self.assertTrue(evt.is_expired(current_time=future_time))

        # Manual test of prune_expired_events by backdating file
        bus_file = self.mem_dir / "volatile-bus" / f"{evt.id}.json"
        with open(bus_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()
        data["timestamp"] = old_time
        data["ttl_seconds"] = 60
        with open(bus_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # List should not include expired
        active = list_events(memory_dir=self.mem_dir)
        self.assertEqual(len(active), 0)

        # Prune should delete it
        pruned = prune_expired_events(memory_dir=self.mem_dir)
        self.assertEqual(pruned, 1)

    def test_clear_bus(self):
        """Verify clear_bus removes all event files."""
        publish_event("a", "s1", "1", memory_dir=self.mem_dir)
        publish_event("b", "s2", "2", memory_dir=self.mem_dir)
        publish_event("c", "s3", "3", memory_dir=self.mem_dir)

        cleared = clear_bus(memory_dir=self.mem_dir)
        self.assertEqual(cleared, 3)

        remaining = list_events(memory_dir=self.mem_dir)
        self.assertEqual(len(remaining), 0)


if __name__ == "__main__":
    unittest.main()
