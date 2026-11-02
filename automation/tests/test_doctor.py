"""Unit and branch tests for agy_toolkit.doctor diagnostic audit suite."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch, MagicMock

from agy_toolkit.doctor import (
    CheckResult,
    DoctorReport,
    audit_toolchain,
    audit_governance,
    run_doctor,
    print_doctor_report,
)


class TestDoctorDiagnostics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_doctor_report_dataclass(self):
        """Verify DoctorReport counts, healthy status, and dictionary conversion."""
        res_pass = CheckResult("Tool", "Test1", "PASS", "ok")
        res_warn = CheckResult("Tool", "Test2", "WARN", "warning", remediation="fix it")
        res_fail = CheckResult("Tool", "Test3", "FAIL", "failed", remediation="redo")

        report = DoctorReport(target_dir=str(self.target), results=[res_pass, res_warn])
        self.assertTrue(report.is_healthy)
        self.assertEqual(report.passed_count, 1)
        self.assertEqual(report.warning_count, 1)
        self.assertEqual(report.failure_count, 0)

        report.results.append(res_fail)
        self.assertFalse(report.is_healthy)
        self.assertEqual(report.failure_count, 1)

        d = report.to_dict()
        self.assertEqual(d["passed"], 1)
        self.assertEqual(d["warnings"], 1)
        self.assertEqual(d["failures"], 1)
        self.assertFalse(d["is_healthy"])
        self.assertEqual(len(d["checks"]), 3)

    def test_print_doctor_report_output(self):
        """Verify print_doctor_report outputs formatted report to stdout."""
        report = DoctorReport(
            target_dir=str(self.target),
            results=[
                CheckResult("Toolchain", "Python Runtime", "PASS", "Python 3.12"),
                CheckResult("Governance", "Rules", "WARN", "Minor warning", remediation="Review GEMINI.md"),
                CheckResult("Memory", "Budget", "FAIL", "Over 1KB", remediation="Flush memory"),
            ],
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            print_doctor_report(report)
        out = buf.getvalue()

        self.assertIn("[AGYToolkit Doctor]", out)
        self.assertIn("Python Runtime", out)
        self.assertIn("ATTENTION REQUIRED", out)
        self.assertIn("Remediation: Flush memory", out)

    def test_audit_toolchain_detections(self):
        """Test toolchain checks with mock subprocess responses."""
        with patch("sys.version_info", (3, 12, 0)), \
             patch("shutil.which", return_value="/bin/mock"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v20.0.0\n")
            results = audit_toolchain()

            names = [r.name for r in results]
            self.assertIn("Python Runtime", names)
            self.assertIn("Node.js", names)
            self.assertIn("Java Development Kit", names)
            self.assertIn("Apache Maven", names)
            self.assertIn("Git Version Control", names)

    def test_audit_governance_missing_and_populated(self):
        """Test governance checks with both missing and populated files."""
        # 1. Missing files
        (self.target / ".gitignore").write_text("# Empty gitignore\n", encoding="utf-8")
        res_missing = audit_governance(self.target)
        statuses_missing = {r.name: r.status for r in res_missing}
        self.assertEqual(statuses_missing.get("Project Rules (GEMINI.md)"), "WARN")
        self.assertEqual(statuses_missing.get("Agent Instructions (AGENTS.md)"), "WARN")
        self.assertEqual(statuses_missing.get("Lifecycle Hooks Config (hooks.json)"), "WARN")
        self.assertEqual(statuses_missing.get("Lifecycle Hook Scripts"), "WARN")
        self.assertEqual(statuses_missing.get("Specialist Agents Matrix"), "WARN")
        self.assertEqual(statuses_missing.get("Progressive Skills Catalog"), "WARN")
        self.assertEqual(statuses_missing.get("Active Session Budget"), "WARN")
        self.assertEqual(statuses_missing.get("Decisions Log Budget"), "WARN")
        self.assertEqual(statuses_missing.get("Gitignore Memory Exclusions"), "FAIL")

        # 2. Populated files
        (self.target / "GEMINI.md").write_text("rules", encoding="utf-8")
        (self.target / "AGENTS.md").write_text("instructions", encoding="utf-8")
        agents_dir = self.target / ".agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "hooks.json").write_text(json.dumps({"hooks": {"PreToolUse": []}}), encoding="utf-8")

        hooks_dir = agents_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        for h in ["anti-bloat-check.ps1", "enforce-branch-rule.ps1", "plan-approval-gate.ps1", "flush-active-memory.ps1"]:
            (hooks_dir / h).write_text("# hook", encoding="utf-8")

        # Agents
        subagents_dir = agents_dir / "agents"
        subagents_dir.mkdir(parents=True)
        agent_names = [
            "orchestrator", "planner-architect", "spring-boot-engineer", "node-ts-engineer",
            "python-automation-lead", "frontend-ui-engineer", "database-architect", "tdd-specialist",
            "security-auditor", "code-reviewer", "anti-bloat-sentinel", "git-craftsman",
            "docs-librarian", "context-budget-guard", "dependency-curator"
        ]
        for name in agent_names:
            (subagents_dir / f"{name}.md").write_text("spec", encoding="utf-8")

        # Skills
        skills_dir = agents_dir / "skills"
        skills_dir.mkdir(parents=True)
        for i in range(1, 29):
            d = skills_dir / f"skill-{i}"
            d.mkdir()
            (d / "SKILL.md").write_text("---", encoding="utf-8")

        # Memory
        mem_dir = agents_dir / "memory"
        mem_dir.mkdir(parents=True)
        (mem_dir / "active-session.md").write_text("Active session", encoding="utf-8")
        (mem_dir / "decisions.md").write_text("Decisions", encoding="utf-8")
        (self.target / ".gitignore").write_text(
            ".agents/memory/active-session.md\n.agents/memory/volatile-bus/*\n", encoding="utf-8"
        )

        res_populated = audit_governance(self.target)
        statuses_pop = {r.name: r.status for r in res_populated}
        self.assertEqual(statuses_pop.get("Project Rules (GEMINI.md)"), "PASS")
        self.assertEqual(statuses_pop.get("Agent Instructions (AGENTS.md)"), "PASS")
        self.assertEqual(statuses_pop.get("Lifecycle Hooks Config (hooks.json)"), "PASS")
        self.assertEqual(statuses_pop.get("Lifecycle Hook Scripts"), "PASS")
        self.assertEqual(statuses_pop.get("Specialist Agents Matrix"), "PASS")
        self.assertEqual(statuses_pop.get("Progressive Skills Catalog"), "PASS")
        self.assertEqual(statuses_pop.get("Active Session Budget"), "PASS")
        self.assertEqual(statuses_pop.get("Decisions Log Budget"), "PASS")
        self.assertEqual(statuses_pop.get("Gitignore Memory Exclusions"), "PASS")

    def test_run_doctor_on_invalid_directory(self):
        """Test run_doctor handles non-existent paths gracefully."""
        bad_path = self.target / "non_existent_subdir"
        report = run_doctor(target_path=bad_path)
        self.assertFalse(report.is_healthy)
        dir_check = [r for r in report.results if r.name == "Directory Exists"]
        self.assertEqual(len(dir_check), 1)
        self.assertEqual(dir_check[0].status, "FAIL")



if __name__ == "__main__":
    unittest.main()
