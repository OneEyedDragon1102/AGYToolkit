"""Concurrency, multithreading, and race condition tests for AGYToolkit event bus."""

import tempfile
import threading
import time
import unittest
from pathlib import Path

from agy_toolkit.bus import (
    publish_event,
    claim_event,
    complete_claimed_event,
    watch_events,
    list_events,
)


class TestBusConcurrency(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_concurrent_publish_no_torn_reads(self):
        """Verify high-volume concurrent publishing produces valid uncorrupted JSON envelopes."""
        num_threads = 5
        events_per_thread = 8
        barrier = threading.Barrier(num_threads)
        errors = []

        def worker(thread_idx: int):
            try:
                barrier.wait(timeout=5.0)
                for i in range(events_per_thread):
                    publish_event(
                        topic=f"thread-{thread_idx}",
                        sender=f"worker-{thread_idx}",
                        payload={"idx": i, "data": "x" * 500},
                        memory_dir=self.mem_dir,
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        self.assertEqual(len(errors), 0, f"Concurrent publishing had errors: {errors}")
        all_events = list_events(memory_dir=self.mem_dir)
        self.assertEqual(len(all_events), num_threads * events_per_thread)

    def test_concurrent_double_claim_race(self):
        """Verify atomic claiming under race conditions: exactly one winner, zero crashes."""
        evt = publish_event(
            topic="high-priority-task",
            sender="orchestrator",
            payload={"task_id": "PR-42"},
            memory_dir=self.mem_dir,
        )

        num_competitors = 6
        barrier = threading.Barrier(num_competitors)
        claims = []
        errors = []

        def claim_worker(worker_id: str):
            try:
                barrier.wait(timeout=5.0)
                result = claim_event(
                    event_id=evt.id,
                    claimer=worker_id,
                    memory_dir=self.mem_dir,
                )
                if result is not None:
                    claims.append((worker_id, result))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=claim_worker, args=(f"worker-{i}",))
            for i in range(num_competitors)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        self.assertEqual(len(errors), 0, f"Claiming threw unhandled errors: {errors}")
        self.assertEqual(len(claims), 1, f"Expected exactly 1 claim winner, got {len(claims)}")

        winner_id, claimed_evt = claims[0]
        self.assertEqual(claimed_evt.id, evt.id)

        # Winner completes the claimed event
        success = complete_claimed_event(
            event_id=evt.id,
            claimer=winner_id,
            memory_dir=self.mem_dir,
        )
        self.assertTrue(success)

    def test_watch_events_realtime_streaming(self):
        """Verify watch_events streams newly arriving events without polling latency."""
        received = []

        def publisher():
            time.sleep(0.08)
            publish_event(
                topic="streaming-test",
                sender="agent-alpha",
                payload={"seq": 1},
                memory_dir=self.mem_dir,
            )
            time.sleep(0.04)
            publish_event(
                topic="streaming-test",
                sender="agent-beta",
                payload={"seq": 2},
                memory_dir=self.mem_dir,
            )

        pub_thread = threading.Thread(target=publisher)
        pub_thread.start()

        for event in watch_events(
            topic="streaming-test",
            stop_after=2,
            timeout_seconds=3.0,
            poll_interval=0.02,
            memory_dir=self.mem_dir,
        ):
            received.append(event)

        pub_thread.join(timeout=2.0)
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0].payload["seq"], 1)
        self.assertEqual(received[1].payload["seq"], 2)

    def test_watch_events_timeout_prevents_deadlock(self):
        """Verify watch_events gracefully terminates on timeout without hanging."""
        start = time.time()
        events = list(
            watch_events(
                topic="non-existent",
                timeout_seconds=0.15,
                poll_interval=0.02,
                memory_dir=self.mem_dir,
            )
        )
        duration = time.time() - start
        self.assertEqual(len(events), 0)
        self.assertGreaterEqual(duration, 0.14)
        self.assertLess(duration, 1.0)

    def test_watch_events_topic_filter(self):
        """Verify watcher strictly filters by topic."""
        publish_event(topic="ignore-this", sender="s", payload={}, memory_dir=self.mem_dir)
        publish_event(topic="target-topic", sender="s", payload={"hit": True}, memory_dir=self.mem_dir)

        matched = list(
            watch_events(
                topic="target-topic",
                stop_after=1,
                timeout_seconds=1.0,
                memory_dir=self.mem_dir,
            )
        )
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].topic, "target-topic")
        self.assertTrue(matched[0].payload.get("hit"))


if __name__ == "__main__":
    unittest.main()
