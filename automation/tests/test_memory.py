"""Unit tests for the AGYToolkit Persistent Memory Engine."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agy_toolkit.memory import (
    get_active_session,
    update_active_session,
    record_decision,
    write_bus_payload,
    read_bus_payload,
    check_memory_budgets,
    ACTIVE_SESSION_BYTE_CAP,
    DECISIONS_BYTE_CAP,
)

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / ".agents" / "hooks"


class TestMemoryEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_active_session_lifecycle_and_cap(self):
        update_active_session(
            goal="Test Goal",
            branch="feature/test-branch",
            active_agent="orchestrator",
            modified_files=["file1.ts", "file2.ts"],
            next_step="Run verification tests",
            memory_dir=self.mem_dir,
        )

        content = get_active_session(memory_dir=self.mem_dir)
        self.assertIn("Test Goal", content)
        self.assertIn("feature/test-branch", content)
        self.assertIn("file1.ts", content)
        self.assertLessEqual(len(content.encode("utf-8")), ACTIVE_SESSION_BYTE_CAP)

    def test_active_session_pruning_on_cap_exceeded(self):
        # Create a large list of files that would exceed 1KB
        many_files = [f"src/deeply/nested/path/to/module_{i}/service.ts" for i in range(50)]
        update_active_session(
            goal="Test Long File List",
            branch="feature/test-branch",
            active_agent="orchestrator",
            modified_files=many_files,
            next_step="Check pruning",
            memory_dir=self.mem_dir,
        )

        content = get_active_session(memory_dir=self.mem_dir)
        self.assertIn("Modified Files (Recent)", content)
        self.assertLessEqual(len(content.encode("utf-8")), ACTIVE_SESSION_BYTE_CAP)

    def test_decisions_recording_and_budget_cap(self):
        for i in range(5):
            record_decision(
                category="Architecture",
                decision=f"Decision number {i}: standard pattern established",
                date_str="2026-10-25",
                memory_dir=self.mem_dir,
            )

        decisions_file = self.mem_dir / "decisions.md"
        self.assertTrue(decisions_file.exists())
        content = decisions_file.read_text(encoding="utf-8")
        self.assertIn("Decision number 4", content)
        self.assertLessEqual(len(content.encode("utf-8")), DECISIONS_BYTE_CAP)

    def test_decisions_eviction_when_cap_exceeded(self):
        # Insert enough large entries to exceed 3KB
        for i in range(40):
            record_decision(
                category="Scalability",
                decision=f"Decision index {i}: detailed architectural rationale with extensive notes to test eviction logic.",
                date_str="2026-10-25",
                memory_dir=self.mem_dir,
            )

        decisions_file = self.mem_dir / "decisions.md"
        content = decisions_file.read_text(encoding="utf-8")
        self.assertLessEqual(len(content.encode("utf-8")), DECISIONS_BYTE_CAP)
        # Most recent decision must be retained
        self.assertIn("Decision index 39", content)

    def test_volatile_bus_roundtrip(self):
        payload_data = {
            "taskId": "task-42",
            "changes": ["Class A", "Class B"],
            "metrics": {"coverage": 87.5, "testsPassed": 14},
        }

        path = write_bus_payload("test-payload-01", payload_data, memory_dir=self.mem_dir)
        self.assertTrue(path.exists())

        loaded = read_bus_payload("test-payload-01", memory_dir=self.mem_dir)
        self.assertEqual(loaded["taskId"], "task-42")
        self.assertEqual(loaded["metrics"]["coverage"], 87.5)

    def test_check_memory_budgets(self):
        # Default repo memory dir
        budgets = check_memory_budgets()
        self.assertIn("active_session", budgets)
        self.assertIn("decisions", budgets)
        self.assertTrue(budgets["active_session"]["within_budget"])
        self.assertTrue(budgets["decisions"]["within_budget"])

    def test_flush_active_memory_hook_execution(self):
        hook_script = HOOKS_DIR / "flush-active-memory.ps1"
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {"Path": "src/AppService.java"},
            }
        }
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(hook_script),
        ]
        proc = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "{}")


if __name__ == "__main__":
    unittest.main()
