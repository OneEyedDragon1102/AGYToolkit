"""Unit tests for AGYToolkit Swarm CLI commands, MCP tools, and dashboard telemetry."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.dashboard import collect_dashboard_metrics, render_tui
from agy_toolkit.mcp_server import McpServer


class TestSwarmCliAndMcp(unittest.TestCase):
    """Test suite covering Swarm CLI commands, native MCP tool execution, and telemetry."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        self.bus_dir = self.mem_dir / "volatile-bus"
        self.runs_dir = self.bus_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "active-session.md").write_text("# Active Session\n", encoding="utf-8")
        (self.mem_dir / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
        self.server = McpServer(workspace_root=self.workspace_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_swarm_pipelines_cli(self):
        """Verify 'agy-toolkit swarm pipelines' prints standard blueprints catalog."""
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["swarm", "pipelines"])
        out = f.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Standard Multi-Agent Blueprint Catalog", out)
        self.assertIn("feature-sdlc", out)
        self.assertIn("code-review", out)
        self.assertIn("quickfix", out)

    def test_swarm_run_and_status_cli(self):
        """Verify launching a pipeline run and checking its status card via CLI."""
        # 1. Run pipeline
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main([
                "swarm", "run", "feature-sdlc", str(self.workspace_dir),
                "--stack", "spring-boot",
                "--context", '{"feature_id": "AUTH-101"}',
            ])
        out = f.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Launched pipeline 'feature-sdlc'", out)
        self.assertIn("Run ID: run_", out)

        # Extract Run ID
        run_id = None
        for word in out.split():
            if word.startswith("run_"):
                run_id = word.rstrip(")")
                break
        self.assertIsNotNone(run_id)

        # 2. Check status (text format)
        f_status = io.StringIO()
        with redirect_stdout(f_status):
            status_code = main(["swarm", "status", run_id, str(self.workspace_dir)])
        status_out = f_status.getvalue()
        self.assertEqual(status_code, 0)
        self.assertIn(f"Pipeline Run: feature-sdlc", status_out)
        self.assertIn(f"Run ID   : {run_id}", status_out)
        self.assertIn("[DISPATCHED]", status_out)

        # 3. Check status (--json format)
        f_json = io.StringIO()
        with redirect_stdout(f_json):
            json_code = main(["swarm", "status", run_id, str(self.workspace_dir), "--json"])
        self.assertEqual(json_code, 0)
        parsed = json.loads(f_json.getvalue())
        self.assertEqual(parsed["run_id"], run_id)
        self.assertEqual(parsed["pipeline_name"], "feature-sdlc")
        self.assertEqual(parsed["steps"]["plan"]["status"], "DISPATCHED")

    def test_swarm_list_and_cancel_cli(self):
        """Verify listing runs and cancelling an active run via CLI."""
        # Create a run first
        f_run = io.StringIO()
        with redirect_stdout(f_run):
            main(["swarm", "run", "quickfix", str(self.workspace_dir)])
        out_run = f_run.getvalue()
        run_id = [w for w in out_run.split() if w.startswith("run_")][0].rstrip(")")

        # List runs (text format)
        f_list = io.StringIO()
        with redirect_stdout(f_list):
            main(["swarm", "list", str(self.workspace_dir)])
        list_out = f_list.getvalue()
        self.assertIn(run_id, list_out)
        self.assertIn("quickfix", list_out)

        # List runs (--json format)
        f_list_json = io.StringIO()
        with redirect_stdout(f_list_json):
            main(["swarm", "list", str(self.workspace_dir), "--json"])
        runs_array = json.loads(f_list_json.getvalue())
        self.assertIsInstance(runs_array, list)
        self.assertGreaterEqual(len(runs_array), 1)

        # Cancel run
        f_cancel = io.StringIO()
        with redirect_stdout(f_cancel):
            main(["swarm", "cancel", run_id, str(self.workspace_dir), "--reason", "CLI test"])
        cancel_out = f_cancel.getvalue()
        self.assertIn(f"Run '{run_id}' cancelled", cancel_out)

    def test_swarm_advance_cli(self):
        """Verify advancing a step triggers downstream unlocks via CLI."""
        # Launch feature-sdlc
        f_run = io.StringIO()
        with redirect_stdout(f_run):
            main(["swarm", "run", "feature-sdlc", str(self.workspace_dir), "--stack", "node-ts"])
        run_id = [w for w in f_run.getvalue().split() if w.startswith("run_")][0].rstrip(")")

        # Advance step 'plan' to COMPLETED
        f_adv = io.StringIO()
        with redirect_stdout(f_adv):
            main([
                "swarm", "advance", run_id, str(self.workspace_dir),
                "--step", "plan",
                "--status", "COMPLETED",
                "--result", '{"design": "approved"}',
                "--claimer", "architect",
            ])
        adv_out = f_adv.getvalue()
        self.assertIn("Step 'plan' advanced to [COMPLETED]", adv_out)
        self.assertIn("tdd", adv_out)

    def test_swarm_mcp_tools(self):
        """Verify native MCP tool execution for swarm choreography."""
        # 1. agy_swarm_run
        run_res, is_err = self.server.execute_tool("agy_swarm_run", {
            "pipeline": "code-review",
            "context": {"pr_id": 99},
        })
        self.assertFalse(is_err)
        run_data = json.loads(run_res)
        self.assertEqual(run_data["pipeline_name"], "code-review")
        self.assertEqual(run_data["status"], "RUNNING")
        run_id = run_data["run_id"]

        # 2. agy_swarm_status
        status_res, is_err = self.server.execute_tool("agy_swarm_status", {"run_id": run_id})
        self.assertFalse(is_err)
        status_data = json.loads(status_res)
        self.assertEqual(status_data["run_id"], run_id)
        self.assertEqual(status_data["steps"]["security-audit"]["status"], "DISPATCHED")

        # 3. agy_swarm_advance
        adv_res, is_err = self.server.execute_tool("agy_swarm_advance", {
            "run_id": run_id,
            "step": "security-audit",
            "status": "COMPLETED",
            "result": {"vulnerabilities": 0},
            "claimer": "security-auditor",
        })
        self.assertFalse(is_err)
        adv_data = json.loads(adv_res)
        self.assertEqual(adv_data["steps"]["security-audit"]["status"], "COMPLETED")
        self.assertEqual(adv_data["steps"]["quality-review"]["status"], "DISPATCHED")

        # 4. agy_swarm_cancel
        cancel_res, is_err = self.server.execute_tool("agy_swarm_cancel", {
            "run_id": run_id,
            "reason": "MCP cancel test",
        })
        self.assertFalse(is_err)
        self.assertIn("cancelled", cancel_res)

    def test_swarm_mcp_json_rpc_call(self):
        """Verify full JSON-RPC 2.0 stdio tools/call invocation for agy_swarm_run."""
        req = {
            "jsonrpc": "2.0",
            "id": "rpc-swarm-1",
            "method": "tools/call",
            "params": {
                "name": "agy_swarm_run",
                "arguments": {
                    "pipeline": "quickfix",
                    "stack": "python",
                },
            },
        }
        raw_res = self.server.process_line(json.dumps(req))
        self.assertIsNotNone(raw_res)
        res = json.loads(raw_res)
        self.assertEqual(res["id"], "rpc-swarm-1")
        self.assertFalse(res["result"]["isError"])
        content_text = res["result"]["content"][0]["text"]
        payload = json.loads(content_text)
        self.assertEqual(payload["pipeline_name"], "quickfix")
        self.assertEqual(payload["status"], "RUNNING")

    def test_dashboard_swarm_telemetry(self):
        """Verify dashboard metrics collector and terminal cockpit render swarm telemetry."""
        # Create a run in the workspace
        self.server.execute_tool("agy_swarm_run", {"pipeline": "quickfix"})

        metrics = collect_dashboard_metrics(self.workspace_dir)
        self.assertIn("swarm", metrics)
        self.assertEqual(metrics["swarm"]["total_runs_count"], 1)
        self.assertEqual(metrics["swarm"]["active_runs_count"], 1)
        self.assertEqual(len(metrics["swarm"]["recent_runs"]), 1)

        tui_output = render_tui(self.workspace_dir)
        self.assertIn("Swarm Pipeline Runs", tui_output)
        self.assertIn("1 running", tui_output)


if __name__ == "__main__":
    unittest.main()
