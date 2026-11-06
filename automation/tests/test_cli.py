"""Unit tests for AGYToolkit CLI and tool catalog using standard unittest."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import (
    TOOL_CATALOG,
    SKILL_TRACKS,
    print_catalog,
    print_agents,
    print_skills,
    main,
)


class TestCLI(unittest.TestCase):
    def test_tool_catalog_contains_core_categories(self):
        self.assertIn("File System", TOOL_CATALOG)
        self.assertIn("Process & Tasks", TOOL_CATALOG)
        self.assertIn("Scheduling", TOOL_CATALOG)
        self.assertIn("Multi-Agent", TOOL_CATALOG)
        self.assertIn("Customizations", TOOL_CATALOG)

    def test_tool_catalog_contains_essential_tools(self):
        all_tools = [tool for tools in TOOL_CATALOG.values() for tool in tools]
        for tool in [
            "read_file",
            "write_file",
            "edit_file",
            "run_command",
            "manage_task",
            "schedule",
            "define_subagent",
            "invoke_subagent",
        ]:
            self.assertIn(tool, all_tools)

    def test_print_catalog_executes(self):
        f = io.StringIO()
        with redirect_stdout(f):
            print_catalog()
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Supported Tool & Feature Catalog", out)
        self.assertIn("read_file", out)

    def test_print_agents_executes(self):
        f = io.StringIO()
        with redirect_stdout(f):
            print_agents()
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Governed Specialist Subagents (15 Universal Matrix)", out)
        self.assertIn("orchestrator", out)
        self.assertIn("frontend-ui-engineer", out)
        self.assertIn("database-architect", out)

    def test_print_skills_executes(self):
        f = io.StringIO()
        with redirect_stdout(f):
            print_skills()
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Progressive SDLC Skills Catalog (28 Skills across 5 Tracks)", out)
        self.assertIn("adr-architect", out)
        self.assertIn("skill-author", out)

    def test_main_with_list_tools(self):
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--list-tools"])
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Supported Tool & Feature Catalog", out)

    def test_main_with_list_agents(self):
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--list-agents"])
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Governed Specialist Subagents (15 Universal Matrix)", out)

    def test_main_with_list_skills(self):
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--list-skills"])
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Progressive SDLC Skills Catalog (28 Skills across 5 Tracks)", out)

    def test_main_with_mcp_export_schemas(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            schema_dir = tmp_path / "schemas"
            f = io.StringIO()
            with redirect_stdout(f):
                main(["mcp", str(tmp_path), "--export-schemas", str(schema_dir)])
            out = f.getvalue()
            self.assertIn("[AGYToolkit MCP] Exported 7 MCP tool schemas", out)
            self.assertTrue((schema_dir / "agy_update.json").exists())
            self.assertTrue((schema_dir / "agy_doctor.json").exists())
            self.assertTrue((schema_dir / "agy_bus_send.json").exists())

    def test_main_with_bus_watch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            f = io.StringIO()
            with redirect_stdout(f):
                main(["bus", "watch", str(tmp_path), "--timeout", "0.1"])
            out = f.getvalue()
            self.assertIn("[AGYToolkit Bus] Watching volatile bus for events", out)

    def test_main_with_pr_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            f = io.StringIO()
            with redirect_stdout(f):
                main(["pr-review", str(tmp_path)])
            out = f.getvalue()
            self.assertIn("AGYToolkit Autonomous Governance & Health Report", out)
            self.assertIn("<!-- AGYToolkit-PR-Review-Bot -->", out)


if __name__ == "__main__":
    unittest.main()
