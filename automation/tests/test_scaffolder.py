"""Unit tests for the AGYToolkit Project Scaffolder."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.scaffolder import scaffold_project
from agy_toolkit.cli import main


class TestScaffolder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scaffold_project_creates_structure(self):
        res = scaffold_project(
            target_path=self.target,
            project_name="clash-of-clans-bot",
            stack="node-ts",
            mode="spike",
        )

        self.assertEqual(res["project_name"], "clash-of-clans-bot")
        self.assertEqual(res["mode"], "spike")
        self.assertEqual(res["agents_installed"], 15)
        self.assertTrue(res["memory_initialized"])

        # Verify filesystem
        agents_dir = self.target / ".agents" / "agents"
        self.assertTrue((agents_dir / "orchestrator.md").exists())
        self.assertTrue((agents_dir / "adb-device-master.md").exists())

        # Verify active session customized
        active_sess = (self.target / ".agents" / "memory" / "active-session.md").read_text(encoding="utf-8")
        self.assertIn("clash-of-clans-bot", active_sess)
        self.assertIn("SPIKE", active_sess)

        # Verify rules customized
        gemini_rules = (self.target / "GEMINI.md").read_text(encoding="utf-8")
        self.assertIn("clash-of-clans-bot", gemini_rules)
        self.assertIn("node-ts", gemini_rules)

        # Verify gitignore ignores active-session.md
        gitignore = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".agents/memory/active-session.md", gitignore)
        self.assertIn(".agents/memory/volatile-bus/*", gitignore)

    def test_cli_init_command(self):
        f = io.StringIO()
        with redirect_stdout(f):
            main(["init", str(self.target), "--name", "market-trader", "--stack", "spring-boot", "--mode", "feature"])

        out = f.getvalue()
        self.assertIn("Initializing Governance for: market-trader", out)
        self.assertIn("Success! Workspace provisioned", out)
        self.assertTrue((self.target / "GEMINI.md").exists())


if __name__ == "__main__":
    unittest.main()
