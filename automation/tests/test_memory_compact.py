"""Unit tests for AGYToolkit Dynamic Memory Auto-Compaction Engine."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.memory import (
    auto_compact_memory,
    CompactReport,
    ACTIVE_SESSION_CAP,
    DECISIONS_CAP,
)


class TestMemoryAutoCompact(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        self.sessions_dir = self.mem_dir / "sessions"
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.active_session_file = self.mem_dir / "active-session.md"
        self.decisions_file = self.mem_dir / "decisions.md"

        self.clean_session = (
            "# Active Session State\n\n"
            "- **Active Goal**: Implement core pipeline\n"
            "- **Current Branch**: `feature/core-pipeline`\n"
            "- **Active Agent**: `orchestrator`\n"
            "- **Immediate Next Step**: Run initial test harness\n\n"
            "## Modified Files (Recent)\n"
            "- None\n\n"
            "## Open Blockers\n"
            "- None\n"
        )
        self.clean_decisions = (
            "# Binding Architectural Decisions Register\n\n"
            "- **2026-11-01 [ARCH]**: Core architecture established.\n"
            "- **2026-11-02 [SEC]**: Hardened input validation.\n"
        )

        self.active_session_file.write_text(self.clean_session, encoding="utf-8")
        self.decisions_file.write_text(self.clean_decisions, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_auto_compact_skips_when_under_threshold(self):
        """Verify no compaction occurs if usage is below threshold (85%)."""
        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.85,
        )
        self.assertFalse(report.active_session_compacted)
        self.assertFalse(report.decisions_compacted)
        self.assertEqual(len(list(self.sessions_dir.glob("*.md"))), 0)
        self.assertEqual(self.active_session_file.read_text(encoding="utf-8"), self.clean_session)

    def test_auto_compact_active_session_archives_and_resets(self):
        """Verify active-session.md is archived and pruned when exceeding 85% of 1024B."""
        bloated_files = "\n".join([f"- file_{i}.py: Modified functions and tests with extra verbose notes" for i in range(25)])
        bloated_session = (
            "# Active Session State\n\n"
            "- **Active Goal**: Implement high-volume ingestion\n"
            "- **Current Branch**: `feature/ingestion`\n"
            "- **Active Agent**: `python-automation-lead`\n"
            "- **Immediate Next Step**: Complete batch runner\n\n"
            f"## Modified Files (Recent)\n{bloated_files}\n\n"
            "## Open Blockers\n- Upstream service latency\n"
        )
        self.active_session_file.write_text(bloated_session, encoding="utf-8")
        self.assertGreater(len(bloated_session.encode("utf-8")), int(ACTIVE_SESSION_CAP * 0.85))

        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.85,
        )

        self.assertTrue(report.active_session_compacted)
        self.assertIsNotNone(report.archived_session_path)
        self.assertLess(report.active_session_bytes_after, int(ACTIVE_SESSION_CAP * 0.85))

        # Verify archive snapshot contains original bloated content
        archived_file = Path(report.archived_session_path)
        self.assertTrue(archived_file.exists())
        self.assertEqual(archived_file.read_text(encoding="utf-8"), bloated_session)

        # Verify pruned active session preserves core goals and blockers
        current_session = self.active_session_file.read_text(encoding="utf-8")
        self.assertIn("Implement high-volume ingestion", current_session)
        self.assertIn("feature/ingestion", current_session)
        self.assertIn("Upstream service latency", current_session)
        self.assertTrue(any("Run /compact" in adv for adv in report.advice))

    def test_auto_compact_decisions_evicts_oldest_to_adr(self):
        """Verify decisions.md evicts oldest entries to docs/adr when exceeding 85% of 3072B."""
        decisions_list = [
            f"- **2026-10-{i:02d} [ARCH]**: Binding architectural decision number {i} with extensive rationale."
            for i in range(1, 40)
        ]
        bloated_decisions = "# Binding Architectural Decisions Register\n\n" + "\n".join(decisions_list) + "\n"
        self.decisions_file.write_text(bloated_decisions, encoding="utf-8")
        self.assertGreater(len(bloated_decisions.encode("utf-8")), int(DECISIONS_CAP * 0.85))

        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.85,
        )

        self.assertTrue(report.decisions_compacted)
        self.assertGreater(report.decisions_evicted_count, 0)
        self.assertLess(report.decisions_bytes_after, int(DECISIONS_CAP * 0.85))
        self.assertIsNotNone(report.archived_adr_path)

        # Verify ADR archive exists and contains oldest decisions
        adr_file = Path(report.archived_adr_path)
        self.assertTrue(adr_file.exists())
        adr_content = adr_file.read_text(encoding="utf-8")
        self.assertIn("decision number 1 with extensive rationale", adr_content)

        # Verify decisions.md retained the latest decisions
        new_decisions = self.decisions_file.read_text(encoding="utf-8")
        self.assertIn("decision number 39 with extensive rationale", new_decisions)
        self.assertNotIn("decision number 1 with extensive rationale", new_decisions)

    def test_auto_compact_dry_run_zero_writes(self):
        """Verify dry-run mode computes projections without modifying files on disk."""
        bloated_session = self.clean_session + "\n" + ("extra notes " * 80)
        self.active_session_file.write_text(bloated_session, encoding="utf-8")

        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.85,
            dry_run=True,
        )

        self.assertTrue(report.dry_run)
        self.assertTrue(report.active_session_compacted)
        self.assertEqual(len(list(self.sessions_dir.glob("*.md"))), 0)
        self.assertEqual(self.active_session_file.read_text(encoding="utf-8"), bloated_session)

    def test_auto_compact_custom_threshold_override(self):
        """Verify custom threshold override triggers compaction at lower limit."""
        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.10,
        )
        self.assertTrue(report.active_session_compacted)

    def test_cli_memory_auto_compact_command(self):
        """Verify agy-toolkit memory auto-compact CLI command formats output cleanly."""
        bloated_session = self.clean_session + "\n" + ("verbose line item\n" * 60)
        self.active_session_file.write_text(bloated_session, encoding="utf-8")

        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["memory", "auto-compact", str(self.workspace_dir)])
        self.assertEqual(ret, 0)
        out = f.getvalue()
        self.assertIn("[AGYToolkit Memory Engine] Auto-Compaction", out)

    def test_cli_memory_auto_compact_json_flag(self):
        """Verify agy-toolkit memory auto-compact --json outputs valid JSON report."""
        bloated_session = self.clean_session + "\n" + ("verbose line item\n" * 60)
        self.active_session_file.write_text(bloated_session, encoding="utf-8")

        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["memory", "auto-compact", str(self.workspace_dir), "--json"])
        self.assertEqual(ret, 0)
        out = f.getvalue()
        data = json.loads(out)
        self.assertIn("active_session_compacted", data)
        self.assertTrue(data["active_session_compacted"])


if __name__ == "__main__":
    unittest.main()
