"""Unit tests for the AGYToolkit Persistent Memory Engine."""

import json
import shutil
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

    def test_update_active_session(self):
        update_active_session(
            goal="Implement hexagonal order service",
            branch="feature/order-service",
            active_agent="spring-boot-engineer",
            modified_files=["Order.java", "OrderRepository.java"],
            next_step="Write domain unit tests",
            blockers=["Pending database migration approval"],
            memory_dir=self.mem_dir,
        )

        content = get_active_session(memory_dir=self.mem_dir)
        self.assertIn("Implement hexagonal order service", content)
        self.assertIn("spring-boot-engineer", content)
        self.assertIn("Order.java", content)
        self.assertIn("Pending database migration approval", content)

    def test_active_session_byte_cap(self):
        many_files = [f"src/com/example/order/service/DomainEntity{i}.java" for i in range(100)]
        update_active_session(
            goal="Massive refactor testing the hard byte cap limit",
            branch="feature/mass-refactor",
            active_agent="orchestrator",
            modified_files=many_files,
            next_step="Review diffs",
            memory_dir=self.mem_dir,
        )

        content = get_active_session(memory_dir=self.mem_dir)
        self.assertLessEqual(len(content.encode("utf-8")), ACTIVE_SESSION_BYTE_CAP)

    def test_record_decision(self):
        record_decision(
            category="ARCH",
            decision="Spring Boot services must use Hexagonal Architecture.",
            date_str="2026-10-25",
            memory_dir=self.mem_dir,
        )

        path = self.mem_dir / "decisions.md"
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8")
        self.assertIn("- **2026-10-25 [ARCH]**: Spring Boot services must use Hexagonal Architecture.", content)

    def test_decisions_byte_cap_eviction(self):
        path = self.mem_dir / "decisions.md"
        for i in range(50):
            record_decision(
                category="DECISION",
                decision=f"Decision number {i} with a detailed explanation to take up bytes.",
                date_str="2026-10-25",
                memory_dir=self.mem_dir,
            )

        content = path.read_text(encoding="utf-8")
        self.assertLessEqual(len(content.encode("utf-8")), DECISIONS_BYTE_CAP)
        self.assertIn("Decision number 49", content)

    def test_volatile_bus_read_write(self):
        payload = {"agent": "orchestrator", "task": "handoff", "status": "PENDING"}
        file_path = write_bus_payload("test-payload-01", payload, memory_dir=self.mem_dir)
        self.assertTrue(file_path.exists())

        loaded = read_bus_payload("test-payload-01", memory_dir=self.mem_dir)
        self.assertEqual(loaded["task"], "handoff")

    def test_check_memory_budgets(self):
        budgets = check_memory_budgets()
        self.assertIn("active_session", budgets)
        self.assertIn("decisions", budgets)
        self.assertTrue(budgets["active_session"]["within_budget"])
        self.assertTrue(budgets["decisions"]["within_budget"])

    def test_flush_active_memory_hook_execution(self):
        ps_cmd = shutil.which("powershell") or shutil.which("pwsh")
        if ps_cmd:
            hook_script = HOOKS_DIR / "flush-active-memory.ps1"
            cmd = [
                ps_cmd,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(hook_script),
            ]
        elif shutil.which("bash"):
            hook_script = HOOKS_DIR / "flush-active-memory.sh"
            cmd = ["bash", str(hook_script)]
        else:
            self.skipTest("No powershell or bash available")

        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {"Path": "src/AppService.java"},
            }
        }
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
