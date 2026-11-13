"""Unit tests for AGYToolkit Multi-Repository and Swarm Orchestrator."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main as cli_main
from agy_toolkit.mcp_multi_repo import handle_multi_repo_tool
from agy_toolkit.multi_repo import (
    WorkspaceManifest,
    WorkspaceMember,
    advance_multi_step,
    audit_workspace,
    broadcast_workspace_event,
    detect_repo_stack,
    format_multi_status_card,
    get_multi_run,
    get_shared_bus_dir,
    init_workspace_manifest,
    launch_multi_run,
    load_workspace_manifest,
)


class TestMultiRepo(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ws_root = Path(self.temp_dir.name)

        # Setup sub-repos: backend (spring-boot), frontend (node-ts), docs (python)
        self.be_dir = self.ws_root / "order-service"
        self.be_dir.mkdir()
        (self.be_dir / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
        (self.be_dir / ".agents").mkdir()
        (self.be_dir / "GEMINI.md").write_text("# Rules\n", encoding="utf-8")
        (self.be_dir / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")

        self.fe_dir = self.ws_root / "web-portal"
        self.fe_dir.mkdir()
        (self.fe_dir / "package.json").write_text('{"name": "web"}\n', encoding="utf-8")
        (self.fe_dir / ".agents").mkdir()
        (self.fe_dir / "GEMINI.md").write_text("# Rules\n", encoding="utf-8")
        (self.fe_dir / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")

        self.docs_dir = self.ws_root / "docs-service"
        self.docs_dir.mkdir()
        (self.docs_dir / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_repo_stack(self):
        """Verify stack detection across Spring Boot, Node-TS, Python, and generic."""
        self.assertEqual(detect_repo_stack(self.be_dir), "spring-boot")
        self.assertEqual(detect_repo_stack(self.fe_dir), "node-ts")
        self.assertEqual(detect_repo_stack(self.docs_dir), "python")

        empty_dir = self.ws_root / "empty-dir"
        empty_dir.mkdir()
        self.assertEqual(detect_repo_stack(empty_dir), "generic")

    def test_init_and_load_workspace_manifest(self):
        """Verify discovering sub-repositories and loading manifest."""
        manifest_file = init_workspace_manifest(self.ws_root, name="fintech-suite")
        self.assertTrue(manifest_file.exists())

        manifest = load_workspace_manifest(self.ws_root)
        self.assertEqual(manifest.name, "fintech-suite")
        self.assertEqual(len(manifest.members), 3)

        be_mem = manifest.get_member("order-service")
        self.assertIsNotNone(be_mem)
        self.assertEqual(be_mem.stack, "spring-boot")
        self.assertEqual(be_mem.role, "backend")
        self.assertTrue(be_mem.is_valid)

        fe_mem = manifest.get_member("web-portal")
        self.assertIsNotNone(fe_mem)
        self.assertEqual(fe_mem.stack, "node-ts")
        self.assertEqual(fe_mem.role, "frontend")

    def test_init_fallback_single_repo(self):
        """Verify fallback to root directory when no sub-repos exist."""
        empty_ws = self.ws_root / "single-repo"
        empty_ws.mkdir()
        (empty_ws / "package.json").write_text('{"name": "root"}\n', encoding="utf-8")

        manifest_file = init_workspace_manifest(empty_ws)
        manifest = load_workspace_manifest(manifest_file)
        self.assertEqual(len(manifest.members), 1)
        self.assertEqual(manifest.members[0].name, "core")
        self.assertEqual(manifest.members[0].stack, "node-ts")

    def test_load_manifest_not_found(self):
        """Verify FileNotFoundError raised when agy-workspace.json is missing."""
        missing_dir = self.ws_root / "missing"
        missing_dir.mkdir()
        with self.assertRaises(FileNotFoundError):
            load_workspace_manifest(missing_dir)

    def test_audit_workspace(self):
        """Verify workspace health audit for healthy and needs_init members."""
        init_workspace_manifest(self.ws_root, name="audit-ws")
        manifest = load_workspace_manifest(self.ws_root)

        audit = audit_workspace(manifest)
        self.assertEqual(audit["workspace_name"], "audit-ws")
        self.assertEqual(audit["total_repositories"], 3)
        self.assertEqual(audit["healthy_repositories"], 2)  # be and fe have .agents + rules
        self.assertEqual(audit["overall_status"], "WARN")  # docs-service needs init

        # Verify docs-service status is NEEDS_INIT
        docs_res = next(r for r in audit["repositories"] if r["name"] == "docs-service")
        self.assertEqual(docs_res["status"], "NEEDS_INIT")

    def test_broadcast_workspace_event(self):
        """Verify publishing cross-repository events to shared bus."""
        init_workspace_manifest(self.ws_root)
        manifest = load_workspace_manifest(self.ws_root)

        bus_dir = get_shared_bus_dir(manifest)
        self.assertTrue(bus_dir.exists())

        evt_id = broadcast_workspace_event(
            manifest,
            topic="cross.repo.sync",
            sender="order-service",
            payload={"version": "2.0.0"},
        )
        self.assertTrue(evt_id.startswith("evt_"))
        self.assertTrue((bus_dir / f"{evt_id}.json").exists())

    def test_multi_run_lifecycle_fullstack_feature(self):
        """Verify end-to-end multi-run launch, advance, dependency unlocking, and completion."""
        init_workspace_manifest(self.ws_root)
        manifest = load_workspace_manifest(self.ws_root)

        run = launch_multi_run(
            manifest,
            blueprint_name="fullstack-feature",
            context={"ticket": "PROJ-101"},
        )
        self.assertEqual(run.status, "RUNNING")
        self.assertTrue(run.run_id.startswith("mrun-"))
        self.assertEqual(run.steps["be-api-spec"].status, "DISPATCHED")
        self.assertEqual(run.steps["be-implementation"].status, "PENDING")

        # Advance first step
        advance_multi_step(manifest, run.run_id, "be-api-spec", "COMPLETED")
        updated = get_multi_run(manifest, run.run_id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.steps["be-api-spec"].status, "COMPLETED")
        self.assertEqual(updated.steps["be-implementation"].status, "DISPATCHED")

        # Advance downstream steps
        advance_multi_step(manifest, run.run_id, "be-implementation", "COMPLETED")
        advance_multi_step(manifest, run.run_id, "fe-client-sync", "COMPLETED")
        advance_multi_step(manifest, run.run_id, "cross-test", "COMPLETED")
        advance_multi_step(manifest, run.run_id, "multi-review", "COMPLETED")

        final_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(final_run.status, "COMPLETED")

    def test_multi_run_failure_handling(self):
        """Verify failing a step marks run as FAILED and skips remaining steps."""
        init_workspace_manifest(self.ws_root)
        manifest = load_workspace_manifest(self.ws_root)

        run = launch_multi_run(manifest, blueprint_name="cross-review")
        advance_multi_step(manifest, run.run_id, "backend-review", "FAILED", error="Syntax error")

        failed_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(failed_run.status, "FAILED")
        self.assertEqual(failed_run.steps["backend-review"].status, "FAILED")
        self.assertEqual(failed_run.steps["security-audit"].status, "SKIPPED")

    def test_format_multi_status_card(self):
        """Verify card formatting contains expected topology markers."""
        init_workspace_manifest(self.ws_root, name="card-test-ws")
        manifest = load_workspace_manifest(self.ws_root)
        run = launch_multi_run(manifest, blueprint_name="cross-review")

        card = format_multi_status_card(run, manifest)
        self.assertIn("[AGYToolkit Multi-Repo Swarm]", card)
        self.assertIn(run.run_id, card)
        self.assertIn("card-test-ws", card)
        self.assertIn("backend-review", card)
        self.assertIn("security-audit", card)

    def test_cli_workspace_subcommands(self):
        """Verify CLI workspace init, list, and check commands."""
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli_main(["workspace", "init", str(self.ws_root), "--name", "cli-ws"])
        self.assertEqual(code, 0)
        self.assertIn("Initialized Manifest", out.getvalue())

        out_list = io.StringIO()
        with redirect_stdout(out_list):
            code = cli_main(["workspace", "list", str(self.ws_root)])
        self.assertEqual(code, 0)
        self.assertIn("cli-ws", out_list.getvalue())
        self.assertIn("order-service", out_list.getvalue())

        out_check = io.StringIO()
        with redirect_stdout(out_check):
            code = cli_main(["workspace", "check", str(self.ws_root)])
        self.assertEqual(code, 0)
        self.assertIn("Healthy Repositories", out_check.getvalue())

    def test_cli_swarm_multi_commands(self):
        """Verify CLI swarm multi-run and multi-status commands."""
        init_workspace_manifest(self.ws_root, name="cli-swarm-ws")

        out_run = io.StringIO()
        with redirect_stdout(out_run):
            cli_main(["swarm", "multi-run", "cross-review", str(self.ws_root)])
        run_output = out_run.getvalue()
        self.assertIn("Launched run 'mrun-", run_output)

        import re
        m = re.search(r"mrun-[0-9a-f]+", run_output)
        self.assertIsNotNone(m)
        run_id = m.group(0)

        out_status = io.StringIO()
        with redirect_stdout(out_status):
            cli_main(["swarm", "multi-status", run_id, str(self.ws_root)])
        self.assertIn(run_id, out_status.getvalue())

    def test_mcp_multi_repo_tool_handler(self):
        """Verify direct MCP multi_repo tool handler execution and errors."""
        init_workspace_manifest(self.ws_root, name="mcp-test-ws")

        # Test workspace status
        res, is_err = handle_multi_repo_tool(self.ws_root, "agy_workspace_status", {})
        self.assertFalse(is_err)
        self.assertIn("mcp-test-ws", res)

        # Test multi run
        res, is_err = handle_multi_repo_tool(
            self.ws_root, "agy_swarm_multi_run", {"blueprint": "cross-review"}
        )
        self.assertFalse(is_err)
        self.assertIn("mrun-", res)

        # Test unknown tool returns None
        unhandled = handle_multi_repo_tool(self.ws_root, "unsupported_tool", {})
        self.assertIsNone(unhandled)


if __name__ == "__main__":
    unittest.main()
