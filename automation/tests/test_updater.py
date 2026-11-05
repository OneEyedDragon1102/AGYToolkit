"""Unit tests for the AGYToolkit Downstream Project Updater."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.scaffolder import scaffold_project
from agy_toolkit.updater import update_project, UpdateReport, format_update_report


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_dir.name) / "test-repo"
        self.target.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _scaffold_target(self):
        return scaffold_project(
            target_path=self.target,
            project_name="sample-downstream",
            stack="node-ts",
            mode="feature",
        )

    def test_update_fails_on_nonexistent_directory(self):
        non_existent = Path(self.temp_dir.name) / "does-not-exist"
        report = update_project(non_existent)
        self.assertFalse(report.success)
        self.assertTrue(any("does not exist" in err.lower() for err in report.errors))

    def test_update_fails_on_uninitialized_project(self):
        empty_dir = Path(self.temp_dir.name) / "empty-repo"
        empty_dir.mkdir(parents=True, exist_ok=True)
        report = update_project(empty_dir)
        self.assertFalse(report.success)
        self.assertTrue(any("not initialized" in err.lower() for err in report.errors))

    def test_update_refreshes_skills_and_agents(self):
        self._scaffold_target()

        # Corrupt / delete one skill and one agent
        skill_file = self.target / ".agents" / "skills" / "adr-architect" / "SKILL.md"
        skill_file.write_text("CORRUPTED SKILL CONTENT", encoding="utf-8")

        agent_file = self.target / ".agents" / "agents" / "orchestrator.md"
        agent_file.unlink()

        report = update_project(self.target)
        self.assertTrue(report.success)
        self.assertEqual(report.skills_updated, 28)
        self.assertEqual(report.agents_updated, 15)
        self.assertEqual(report.hooks_updated, 8)

        # Verify restored
        self.assertNotEqual(skill_file.read_text(encoding="utf-8"), "CORRUPTED SKILL CONTENT")
        self.assertTrue(agent_file.exists())

    def test_update_preserves_custom_rules(self):
        self._scaffold_target()

        gemini_md = self.target / "GEMINI.md"
        agents_md = self.target / "AGENTS.md"

        custom_gemini = "# Custom Rules for Sample\n- Do not break stuff"
        custom_agents = "# Custom Agent Protocols\n- Protocol Alpha"

        gemini_md.write_text(custom_gemini, encoding="utf-8")
        agents_md.write_text(custom_agents, encoding="utf-8")

        report = update_project(self.target, force_rules=False)
        self.assertTrue(report.success)
        self.assertTrue(report.rules_preserved)

        self.assertEqual(gemini_md.read_text(encoding="utf-8"), custom_gemini)
        self.assertEqual(agents_md.read_text(encoding="utf-8"), custom_agents)

    def test_update_force_rules_overwrites_when_explicit(self):
        self._scaffold_target()

        gemini_md = self.target / "GEMINI.md"
        gemini_md.write_text("# Custom Rules To Be Overwritten", encoding="utf-8")

        report = update_project(self.target, force_rules=True)
        self.assertTrue(report.success)
        self.assertFalse(report.rules_preserved)

        self.assertNotEqual(gemini_md.read_text(encoding="utf-8"), "# Custom Rules To Be Overwritten")

    def test_update_preserves_memory_state(self):
        self._scaffold_target()

        active_file = self.target / ".agents" / "memory" / "active-session.md"
        decisions_file = self.target / ".agents" / "memory" / "decisions.md"

        custom_session = "# Session\n- Goal: Critical feature in flight\n"
        custom_decisions = "# Decisions\n- Decision 001: Architecture locked\n"

        active_file.write_text(custom_session, encoding="utf-8")
        decisions_file.write_text(custom_decisions, encoding="utf-8")

        report = update_project(self.target)
        self.assertTrue(report.success)
        self.assertTrue(report.memory_preserved)

        self.assertEqual(active_file.read_text(encoding="utf-8"), custom_session)
        self.assertEqual(decisions_file.read_text(encoding="utf-8"), custom_decisions)

    def test_update_dry_run_zero_writes(self):
        self._scaffold_target()

        agent_file = self.target / ".agents" / "agents" / "orchestrator.md"
        agent_file.unlink()

        report = update_project(self.target, dry_run=True)
        self.assertTrue(report.success)
        self.assertTrue(report.dry_run)
        self.assertEqual(report.agents_updated, 15)

        # File must NOT have been restored on disk
        self.assertFalse(agent_file.exists())

    def test_update_gitignore_hygiene(self):
        self._scaffold_target()

        gitignore = self.target / ".gitignore"
        gitignore.write_text("# Custom gitignore\nnode_modules/\n", encoding="utf-8")

        report = update_project(self.target)
        self.assertTrue(report.success)

        content = gitignore.read_text(encoding="utf-8")
        self.assertIn(".agents/memory/active-session.md", content)
        self.assertIn(".agents/memory/volatile-bus/*", content)

    def test_format_update_report_output(self):
        report = UpdateReport(
            target_path=str(self.target),
            success=True,
            skills_updated=28,
            agents_updated=15,
            hooks_updated=4,
            rules_preserved=True,
            memory_preserved=True,
            dry_run=False,
            errors=[],
        )
        formatted = format_update_report(report)
        self.assertIn("Update Summary", formatted)
        self.assertIn("28", formatted)
        self.assertIn("15", formatted)
        self.assertIn("Preserved", formatted)

    def test_cli_update_command(self):
        self._scaffold_target()

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["update", str(self.target)])
        self.assertEqual(ret, 0)
        output = buf.getvalue()
        self.assertIn("AGYToolkit Project Update", output)
        self.assertIn("Success", output)

    def test_cli_update_dry_run_flag(self):
        self._scaffold_target()

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["update", str(self.target), "--dry-run"])
        self.assertEqual(ret, 0)
        output = buf.getvalue()
        self.assertIn("DRY RUN", output)
