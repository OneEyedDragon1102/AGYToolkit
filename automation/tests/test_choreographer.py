"""Unit tests for the AGYToolkit Swarm Choreographer Engine."""

import json
import tempfile
import unittest
from pathlib import Path

from agy_toolkit.bus import read_event
from agy_toolkit.choreographer import (
    STANDARD_PIPELINES,
    advance_step,
    cancel_pipeline_run,
    create_pipeline_run,
    get_pipeline_definition,
    list_available_pipelines,
    list_pipeline_runs,
    load_pipeline_run,
    resolve_role_for_stack,
)


class TestChoreographer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = Path(self.temp_dir.name)
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        self.bus_dir = self.mem_dir / "volatile-bus"
        self.bus_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_available_pipelines(self):
        """Verify built-in blueprint catalog contains core SDLC workflows."""
        pipelines = list_available_pipelines()
        names = {p["name"] for p in pipelines}
        self.assertIn("feature-sdlc", names)
        self.assertIn("code-review", names)
        self.assertIn("quickfix", names)

        feature = next(p for p in pipelines if p["name"] == "feature-sdlc")
        self.assertEqual(feature["steps_count"], 5)
        step_names = [s["name"] for s in feature["steps"]]
        self.assertEqual(step_names, ["plan", "tdd", "implement", "review", "stage"])

    def test_resolve_role_for_stack(self):
        """Verify stack mapping to specialized subagents."""
        self.assertEqual(resolve_role_for_stack("stack-engineer", "spring-boot"), "spring-boot-engineer")
        self.assertEqual(resolve_role_for_stack("stack-engineer", "Java Spring Boot"), "spring-boot-engineer")
        self.assertEqual(resolve_role_for_stack("stack-engineer", "node-ts"), "node-ts-engineer")
        self.assertEqual(resolve_role_for_stack("stack-engineer", "typescript"), "node-ts-engineer")
        self.assertEqual(resolve_role_for_stack("stack-engineer", "python"), "python-automation-lead")
        self.assertEqual(resolve_role_for_stack("stack-engineer", None), "stack-engineer")
        self.assertEqual(resolve_role_for_stack("code-reviewer", "node-ts"), "code-reviewer")

    def test_create_pipeline_run_dispatches_initial_step(self):
        """Verify creating a feature-sdlc run dispatches the unblocked plan step."""
        run = create_pipeline_run(
            pipeline_name="feature-sdlc",
            context={"task": "add-billing", "stack": "spring-boot"},
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.status, "RUNNING")
        self.assertIn("plan", run.steps)
        self.assertEqual(run.steps["plan"].status, "DISPATCHED")
        self.assertIsNotNone(run.steps["plan"].event_id)
        self.assertEqual(run.steps["implement"].role, "spring-boot-engineer")

        # Downstream steps with dependencies must remain PENDING
        self.assertEqual(run.steps["tdd"].status, "PENDING")
        self.assertEqual(run.steps["implement"].status, "PENDING")
        self.assertEqual(run.steps["review"].status, "PENDING")
        self.assertEqual(run.steps["stage"].status, "PENDING")

        # Verify event on volatile bus
        evt = read_event(run.steps["plan"].event_id, memory_dir=self.mem_dir)
        self.assertIsNotNone(evt)
        self.assertEqual(evt.topic, "swarm:plan")
        self.assertEqual(evt.recipient, "planner-architect")
        self.assertEqual(evt.payload["step"], "plan")
        self.assertEqual(evt.payload["context"]["task"], "add-billing")

    def test_parallel_initial_steps_dispatch(self):
        """Verify code-review pipeline with multiple zero-dependency steps dispatches all in parallel."""
        run = create_pipeline_run(
            pipeline_name="code-review",
            context={"pr": 42},
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.status, "RUNNING")
        self.assertEqual(run.steps["security-audit"].status, "DISPATCHED")
        self.assertEqual(run.steps["quality-review"].status, "DISPATCHED")
        self.assertEqual(run.steps["anti-bloat-check"].status, "DISPATCHED")

        # Ensure all 3 events were published
        for step_name in ["security-audit", "quality-review", "anti-bloat-check"]:
            evt_id = run.steps[step_name].event_id
            self.assertIsNotNone(evt_id)
            evt = read_event(evt_id, memory_dir=self.mem_dir)
            self.assertIsNotNone(evt)

    def test_advance_step_unlocks_downstream_and_propagates_context(self):
        """Verify completing a step unlocks downstream steps and passes upstream artifacts in payload."""
        run = create_pipeline_run(
            pipeline_name="feature-sdlc",
            context={"task": "auth-service", "stack": "node-ts"},
            memory_dir=self.mem_dir,
        )

        # 1. Complete 'plan' step
        plan_result = {"spec_file": "docs/auth-spec.md", "endpoints": ["/login", "/refresh"]}
        run = advance_step(
            run_id=run.run_id,
            step_name="plan",
            status="COMPLETED",
            result=plan_result,
            claimer="planner-architect",
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.steps["plan"].status, "COMPLETED")
        self.assertEqual(run.steps["plan"].result, plan_result)

        # 'tdd' step should now be unlocked and DISPATCHED
        self.assertEqual(run.steps["tdd"].status, "DISPATCHED")
        tdd_evt = read_event(run.steps["tdd"].event_id, memory_dir=self.mem_dir)
        self.assertIsNotNone(tdd_evt)
        self.assertEqual(tdd_evt.recipient, "tdd-specialist")
        self.assertEqual(tdd_evt.payload["upstream_results"]["plan"], plan_result)

        # 2. Complete 'tdd' step
        tdd_result = {"test_files": ["tests/auth.test.ts"], "tests_count": 8}
        run = advance_step(
            run_id=run.run_id,
            step_name="tdd",
            status="COMPLETED",
            result=tdd_result,
            claimer="tdd-specialist",
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.steps["tdd"].status, "COMPLETED")

        # 'implement' step should now be DISPATCHED for node-ts-engineer
        self.assertEqual(run.steps["implement"].status, "DISPATCHED")
        self.assertEqual(run.steps["implement"].role, "node-ts-engineer")
        impl_evt = read_event(run.steps["implement"].event_id, memory_dir=self.mem_dir)
        self.assertIsNotNone(impl_evt)
        self.assertEqual(impl_evt.recipient, "node-ts-engineer")
        self.assertEqual(impl_evt.payload["upstream_results"]["tdd"], tdd_result)

    def test_pipeline_run_full_completion(self):
        """Verify full execution lifecycle of quickfix pipeline to COMPLETED."""
        run = create_pipeline_run(
            pipeline_name="quickfix",
            context={"issue": "NullPointerException in user service"},
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.status, "RUNNING")

        # Step 1: reproduce-test
        run = advance_step(run.run_id, "reproduce-test", "COMPLETED", {"reproduced": True}, memory_dir=self.mem_dir)
        self.assertEqual(run.status, "RUNNING")

        # Step 2: patch
        run = advance_step(run.run_id, "patch", "COMPLETED", {"patch_lines": 5}, memory_dir=self.mem_dir)
        self.assertEqual(run.status, "RUNNING")

        # Step 3: verify-review
        run = advance_step(run.run_id, "verify-review", "COMPLETED", {"passed": True}, memory_dir=self.mem_dir)
        self.assertEqual(run.status, "COMPLETED")
        self.assertTrue(all(s.status == "COMPLETED" for s in run.steps.values()))

    def test_pipeline_run_failure(self):
        """Verify failing a step marks the overall run as FAILED."""
        run = create_pipeline_run(
            pipeline_name="quickfix",
            context={"issue": "flaky test"},
            memory_dir=self.mem_dir,
        )
        run = advance_step(
            run_id=run.run_id,
            step_name="reproduce-test",
            status="FAILED",
            error="Could not reproduce issue after 3 attempts.",
            memory_dir=self.mem_dir,
        )
        self.assertEqual(run.status, "FAILED")
        self.assertEqual(run.steps["reproduce-test"].error, "Could not reproduce issue after 3 attempts.")

    def test_cancel_pipeline_run(self):
        """Verify cancelling an active run sets CANCELLED and marks pending steps SKIPPED."""
        run = create_pipeline_run(
            pipeline_name="feature-sdlc",
            context={"task": "cancel-me"},
            memory_dir=self.mem_dir,
        )
        cancelled = cancel_pipeline_run(run.run_id, reason="User requested abort", memory_dir=self.mem_dir)
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled.status, "CANCELLED")
        self.assertEqual(cancelled.context["cancel_reason"], "User requested abort")
        for s in cancelled.steps.values():
            self.assertIn(s.status, ("SKIPPED", "DISPATCHED"))

    def test_load_and_list_pipeline_runs(self):
        """Verify runs are correctly persisted to disk and queryable."""
        run1 = create_pipeline_run("code-review", {"id": 1}, memory_dir=self.mem_dir)
        run2 = create_pipeline_run("quickfix", {"id": 2}, memory_dir=self.mem_dir)

        loaded = load_pipeline_run(run1.run_id, memory_dir=self.mem_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.pipeline_name, "code-review")

        all_runs = list_pipeline_runs(memory_dir=self.mem_dir)
        self.assertEqual(len(all_runs), 2)
        run_ids = {r.run_id for r in all_runs}
        self.assertEqual(run_ids, {run1.run_id, run2.run_id})

    def test_invalid_pipeline_raises(self):
        """Verify invalid pipeline template name raises ValueError."""
        with self.assertRaises(ValueError):
            create_pipeline_run("non-existent-blueprint", memory_dir=self.mem_dir)


if __name__ == "__main__":
    unittest.main()
