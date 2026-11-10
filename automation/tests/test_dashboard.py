"""Unit tests for the AGYToolkit Diagnostic Terminal & Web Dashboard Engine."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.dashboard import (
    render_gauge,
    collect_dashboard_metrics,
    render_tui,
    DashboardRequestHandler,
)


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        # Initialize memory directories
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        (self.mem_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "volatile-bus").mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "active-session.md").write_text("# Active Session\n- Goal: Test\n", encoding="utf-8")
        (self.mem_dir / "decisions.md").write_text("# Decisions\n- Decision 1\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_render_gauge_calculations(self):
        """Verify visual progress gauge formatting at various percentages."""
        g0 = render_gauge(0, 100, width=10)
        self.assertIn("0.0%", g0)
        self.assertEqual(g0.count("="), 0)

        g50 = render_gauge(50, 100, width=10)
        self.assertIn("50.0%", g50)
        self.assertEqual(g50.count("="), 5)

        g100 = render_gauge(100, 100, width=10)
        self.assertIn("100.0%", g100)
        self.assertEqual(g100.count("="), 10)

        # Over-capacity clamping
        g150 = render_gauge(150, 100, width=10)
        self.assertIn("150.0%", g150)
        self.assertEqual(g150.count("="), 10)

    def test_collect_dashboard_metrics_structure(self):
        """Verify collected metrics dictionary includes all core system subsystems."""
        metrics = collect_dashboard_metrics(self.workspace_dir)
        self.assertIn("workspace", metrics)
        self.assertIn("toolchains", metrics)
        self.assertIn("governance", metrics)
        self.assertIn("memory", metrics)
        self.assertIn("bus", metrics)
        self.assertIn("agents_count", metrics)
        self.assertIn("skills_count", metrics)

        # Check memory structure
        mem = metrics["memory"]
        self.assertIn("active_session_bytes", mem)
        self.assertIn("active_session_cap", mem)
        self.assertIn("decisions_bytes", mem)
        self.assertIn("decisions_cap", mem)
        self.assertIn("status", mem)

    def test_render_tui_text_output(self):
        """Verify terminal TUI renders formatted panels and metrics."""
        tui = render_tui(self.workspace_dir)
        self.assertIn("AGYToolkit Operational Cockpit", tui)
        self.assertIn("Toolchains & Runtime", tui)
        self.assertIn("Dual-Tier Memory HUD", tui)
        self.assertIn("Volatile IPC Event Bus", tui)
        self.assertIn("Specialist Subagents", tui)

    def test_cli_doctor_tui_flag(self):
        """Verify agy-toolkit doctor --tui invokes the cockpit dashboard."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["doctor", str(self.workspace_dir), "--tui"])
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("AGYToolkit Operational Cockpit", out)

    def test_cli_dashboard_command(self):
        """Verify agy-toolkit dashboard command outputs terminal TUI."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["dashboard", str(self.workspace_dir)])
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("AGYToolkit Operational Cockpit", out)

    def test_web_dashboard_assets_exist_and_valid(self):
        """Verify web dashboard static files in docs/ exist and have required markup."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        index_html = repo_root / "docs" / "index.html"
        dashboard_css = repo_root / "docs" / "dashboard.css"
        dashboard_js = repo_root / "docs" / "dashboard.js"

        self.assertTrue(index_html.exists(), "docs/index.html must exist")
        self.assertTrue(dashboard_css.exists(), "docs/dashboard.css must exist")
        self.assertTrue(dashboard_js.exists(), "docs/dashboard.js must exist")

        html_content = index_html.read_text(encoding="utf-8")
        self.assertIn("AGYToolkit", html_content)
        self.assertIn("Operator Playbook", html_content)
        self.assertIn("Specialist Subagents", html_content)
        self.assertIn("Dual-Tier Memory", html_content)


if __name__ == "__main__":
    unittest.main()
