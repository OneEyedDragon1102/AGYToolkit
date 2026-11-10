"""Unit tests for AGYToolkit Swarm Worker daemon, heartbeat supervisor, and execution engine."""

import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.bus import claim_event, get_claim_status, publish_event
from agy_toolkit.choreographer import create_pipeline_run, load_pipeline_run
from agy_toolkit.cli import main
from agy_toolkit.mcp_server import McpServer
from agy_toolkit.worker import HeartbeatSupervisor, StepExecutionResult, SwarmWorker, execute_step_task


class TestSwarmWorker(unittest.TestCase):
    """Test suite covering autonomous swarm worker execution, heartbeats, and lifecycle states."""

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

    def test_worker_discovers_and_claims_step(self):
        """Verify worker automatically claims dispatched step, advances DAG, and unlocks downstream step."""
        # Create pipeline run
        run = create_pipeline_run("feature-sdlc", memory_dir=self.mem_dir)
        self.assertEqual(run.steps["plan"].status, "DISPATCHED")

        # Worker discovers and executes step 'plan'
        worker = SwarmWorker(memory_dir=self.mem_dir, workspace_root=self.workspace_dir)
        ready = worker.get_ready_step_events()
        self.assertEqual(len(ready), 1)

        res = worker.run_once()
        self.assertIsNotNone(res)
        self.assertEqual(res.step_name, "plan")
        self.assertEqual(res.status, "COMPLETED")

        # Verify pipeline state updated
        updated_run = load_pipeline_run(run.run_id, memory_dir=self.mem_dir)
        self.assertIsNotNone(updated_run)
        self.assertEqual(updated_run.steps["plan"].status, "COMPLETED")
        self.assertEqual(updated_run.steps["tdd"].status, "DISPATCHED")

    def test_worker_heartbeat_supervisor(self):
        """Verify background heartbeat thread refreshes lock heartbeat timestamp."""
        evt = publish_event("test.topic", "sender", {"test": True}, memory_dir=self.mem_dir)
        claim_event(evt.id, claimer="hb_worker", lease_seconds=10, memory_dir=self.mem_dir)

        initial_status = get_claim_status(evt.id, memory_dir=self.mem_dir)
        self.assertIsNotNone(initial_status)
        initial_hb = initial_status["heartbeat_at"]

        # Run supervisor with small interval
        supervisor = HeartbeatSupervisor(
            event_id=evt.id,
            claimer="hb_worker",
            interval_seconds=0.1,
            extend_seconds=30,
            memory_dir=self.mem_dir,
        )
        supervisor.start()
        time.sleep(0.35)
        supervisor.stop()

        updated_status = get_claim_status(evt.id, memory_dir=self.mem_dir)
        self.assertIsNotNone(updated_status)
        self.assertGreaterEqual(updated_status["heartbeat_at"], initial_hb)
        self.assertEqual(updated_status["lease_seconds"], 30)

    def test_worker_command_execution_success(self):
        """Verify executing an explicit shell command in a step succeeds and captures output."""
        context = {
            "step_commands": {
                "reproduce-test": "python -c \"print('reproduction verified')\"",
            }
        }
        run = create_pipeline_run("quickfix", context=context, memory_dir=self.mem_dir)
        worker = SwarmWorker(memory_dir=self.mem_dir, workspace_root=self.workspace_dir)

        res = worker.run_once()
        self.assertIsNotNone(res)
        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("reproduction verified", res.result.get("stdout", ""))

        updated_run = load_pipeline_run(run.run_id, memory_dir=self.mem_dir)
        self.assertEqual(updated_run.steps["reproduce-test"].status, "COMPLETED")
        self.assertEqual(updated_run.steps["patch"].status, "DISPATCHED")

    def test_worker_command_execution_failure(self):
        """Verify failed shell command marks step and pipeline as FAILED and skips remaining steps."""
        context = {
            "step_commands": {
                "reproduce-test": "python -c \"import sys; sys.exit(7)\"",
            }
        }
        run = create_pipeline_run("quickfix", context=context, memory_dir=self.mem_dir)
        worker = SwarmWorker(memory_dir=self.mem_dir, workspace_root=self.workspace_dir)

        res = worker.run_once()
        self.assertIsNotNone(res)
        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.exit_code, 7)

        updated_run = load_pipeline_run(run.run_id, memory_dir=self.mem_dir)
        self.assertEqual(updated_run.status, "FAILED")
        self.assertEqual(updated_run.steps["reproduce-test"].status, "FAILED")
        self.assertEqual(updated_run.steps["patch"].status, "SKIPPED")
        self.assertEqual(updated_run.steps["verify-review"].status, "SKIPPED")

    def test_worker_command_timeout(self):
        """Verify command exceeding execution timeout aborts and records failure."""
        payload = {
            "run_id": "test_run",
            "step": "long-task",
            "role": "engineer",
            "context": {"command": "python -c \"import time; time.sleep(3)\""},
        }
        res = execute_step_task(payload, timeout_seconds=1, workspace_root=self.workspace_dir)
        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.exit_code, 124)
        self.assertIn("timed out", res.error)

    def test_worker_run_loop_drives_full_pipeline(self):
        """Verify worker loop executes all 3 steps of quickfix pipeline to completion."""
        run = create_pipeline_run("quickfix", memory_dir=self.mem_dir)
        worker = SwarmWorker(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            poll_interval=0.05,
        )

        results = worker.run_loop(max_cycles=3)
        self.assertEqual(len(results), 3)
        self.assertEqual([r.step_name for r in results], ["reproduce-test", "patch", "verify-review"])

        final_run = load_pipeline_run(run.run_id, memory_dir=self.mem_dir)
        self.assertEqual(final_run.status, "COMPLETED")
        for step in final_run.steps.values():
            self.assertEqual(step.status, "COMPLETED")

    def test_worker_cli_command(self):
        """Verify 'agy-toolkit swarm worker --run-once' runs from CLI."""
        create_pipeline_run("quickfix", memory_dir=self.mem_dir)
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main(["swarm", "worker", str(self.workspace_dir), "--run-once"])
        out = f.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[AGYToolkit Swarm Worker] Running single worker cycle", out)
        self.assertIn("reproduce-test", out)
        self.assertIn("[COMPLETED]", out)

    def test_worker_mcp_tools(self):
        """Verify native MCP tools agy_swarm_worker_status and agy_swarm_worker_cycle."""
        # Launch pipeline
        self.server.execute_tool("agy_swarm_run", {"pipeline": "quickfix"})

        # Check worker status via MCP
        status_raw, is_err = self.server.execute_tool("agy_swarm_worker_status", {})
        self.assertFalse(is_err)
        status_data = json.loads(status_raw)
        self.assertTrue(status_data["worker_ready"])
        self.assertEqual(status_data["ready_steps_count"], 1)
        self.assertEqual(status_data["ready_steps"][0]["step"], "reproduce-test")

        # Execute single cycle via MCP
        cycle_raw, is_err = self.server.execute_tool("agy_swarm_worker_cycle", {})
        self.assertFalse(is_err)
        cycle_data = json.loads(cycle_raw)
        self.assertTrue(cycle_data["processed"])
        self.assertEqual(cycle_data["step"], "reproduce-test")
        self.assertEqual(cycle_data["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
