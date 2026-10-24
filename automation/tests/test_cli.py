"""Unit tests for AGYToolkit CLI and tool catalog using standard unittest."""

import io
import sys
import unittest
from contextlib import redirect_stdout

from agy_toolkit.cli import TOOL_CATALOG, print_catalog, main


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

    def test_main_with_list_tools(self):
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--list-tools"])
        out = f.getvalue()
        self.assertIn("[AGYToolkit] Supported Tool & Feature Catalog", out)


if __name__ == "__main__":
    unittest.main()
