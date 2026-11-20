"""End-to-End Enterprise Dogfooding & Integration Test Suite.

Simulates a complete real-world Realtime CDC & Outbox streaming platform across
Spring Boot Hexagonal services, Node.js/TypeScript consumers, ADR memory compaction,
SQLite FTS5 knowledge search, multi-repo swarm DAG choreography, and GitOps release bot.
"""

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main as cli_main
from agy_toolkit.knowledge import index_workspace, search_knowledge
from agy_toolkit.memory import auto_compact_memory, record_decision
from agy_toolkit.multi_repo import (
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
from agy_toolkit.release import execute_release, plan_release


class TestE2EDogfood(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)

        # Initialize mock git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.workspace_root), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "AGYBot"], cwd=str(self.workspace_root), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "bot@agytoolkit.local"], cwd=str(self.workspace_root), capture_output=True, check=True)

        # 1. Microservice A: order-service (Java / Spring Boot Hexagonal with Outbox)
        self.order_svc = self.workspace_root / "order-service"
        self.order_svc.mkdir()
        (self.order_svc / "pom.xml").write_text("<project><artifactId>order-service</artifactId></project>\n", encoding="utf-8")
        (self.order_svc / ".agents").mkdir()
        (self.order_svc / "GEMINI.md").write_text("# Order Service Rules\n", encoding="utf-8")
        (self.order_svc / "AGENTS.md").write_text("# Order Service Agent Instructions\n", encoding="utf-8")

        # 2. Microservice B: search-indexer (Node.js / TypeScript OpenSearch CDC Consumer)
        self.search_indexer = self.workspace_root / "search-indexer"
        self.search_indexer.mkdir()
        (self.search_indexer / "package.json").write_text('{"name": "search-indexer", "version": "1.0.0"}\n', encoding="utf-8")
        (self.search_indexer / ".agents").mkdir()
        (self.search_indexer / "GEMINI.md").write_text("# Search Indexer Rules\n", encoding="utf-8")
        (self.search_indexer / "AGENTS.md").write_text("# Search Indexer Instructions\n", encoding="utf-8")

        # 3. Infrastructure: infra-cdk (AWS CDK TypeScript Stacks)
        self.infra_cdk = self.workspace_root / "infra-cdk"
        self.infra_cdk.mkdir()
        (self.infra_cdk / "package.json").write_text('{"name": "infra-cdk"}\n', encoding="utf-8")
        (self.infra_cdk / "cdk.json").write_text('{"app": "npx ts-node bin/app.ts"}\n', encoding="utf-8")

        # Root governance & memory directories
        self.agents_dir = self.workspace_root / ".agents"
        self.mem_dir = self.agents_dir / "memory"
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        (self.mem_dir / "active-session.md").write_text("# Active Session: Realtime CDC Platform\n", encoding="utf-8")
        (self.mem_dir / "decisions.md").write_text("# Architectural Decisions\n\n", encoding="utf-8")

        # Root pyproject.toml for GitOps release bot
        (self.workspace_root / "pyproject.toml").write_text('[project]\nname = "realtime-cdc-stream"\nversion = "0.1.0"\n', encoding="utf-8")
        (self.workspace_root / "automation" / "src" / "agy_toolkit").mkdir(parents=True, exist_ok=True)
        (self.workspace_root / "automation" / "src" / "agy_toolkit" / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
        (self.workspace_root / "automation" / "src" / "agy_toolkit" / "mcp_server.py").write_text('SERVER_VERSION = "0.1.0"\n', encoding="utf-8")

        # Initial root commit
        subprocess.run(["git", "add", "."], cwd=str(self.workspace_root), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feat(foundation): initial cdc streaming architecture"], cwd=str(self.workspace_root), capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_e2e_workspace_scaffolding_and_stack_detection(self):
        """E2E Test: Multi-repo workspace manifest discovery, stack detection, and governance audit."""
        self.assertEqual(detect_repo_stack(self.order_svc), "spring-boot")
        self.assertEqual(detect_repo_stack(self.search_indexer), "node-ts")
        self.assertEqual(detect_repo_stack(self.infra_cdk), "node-ts")

        # Generate agy-workspace.json
        manifest_path = init_workspace_manifest(self.workspace_root, name="realtime-cdc-platform")
        self.assertTrue(manifest_path.exists())

        manifest = load_workspace_manifest(self.workspace_root)
        self.assertEqual(manifest.name, "realtime-cdc-platform")
        self.assertEqual(len(manifest.members), 3)

        # Audit workspace
        audit = audit_workspace(manifest)
        self.assertEqual(audit["total_repositories"], 3)
        self.assertEqual(audit["healthy_repositories"], 2)  # order-service and search-indexer have .agents + rules
        self.assertEqual(audit["overall_status"], "WARN")  # infra-cdk lacks .agents

    def test_e2e_adr_memory_compaction_and_knowledge_search(self):
        """E2E Test: Memory budget pressure, auto-compaction, cold-storage archival, and FTS5 search."""
        # Record multiple detailed ADRs to simulate realistic memory budget pressure
        for i in range(1, 16):
            record_decision(
                category=f"ARCH_{i}",
                decision=f"ADR-{i:03d}: Realtime CDC architectural decision #{i} regarding PostgreSQL WAL streaming, Debezium pgoutput replication, Transactional Outbox dual-write guarantees, and OpenSearch real-time indexer.",
                memory_dir=self.mem_dir,
            )

        decisions_file = self.mem_dir / "decisions.md"
        self.assertTrue(decisions_file.exists())
        self.assertIn("Transactional Outbox", decisions_file.read_text(encoding="utf-8"))

        # Trigger auto-compaction
        report = auto_compact_memory(
            threshold=0.01,  # Force compaction
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_root,
        )
        self.assertTrue(report.decisions_compacted)
        self.assertTrue(report.decisions_evicted_count > 0)

        # Verify cold storage archival in docs/adr/
        history_file = self.workspace_root / "docs" / "adr" / "decisions-history.md"
        self.assertTrue(history_file.exists())
        self.assertIn("ADR-001", history_file.read_text(encoding="utf-8"))
        self.assertIn("Transactional Outbox", history_file.read_text(encoding="utf-8"))

        # Verify sub-millisecond SQLite FTS5 search queries across indexed ADRs
        index_workspace(workspace_root=self.workspace_root, force=True)

        results_outbox = search_knowledge(self.workspace_root, query="Transactional Outbox dual-write")
        self.assertTrue(len(results_outbox) > 0)
        self.assertIn("Transactional", results_outbox[0].snippet)

        results_adr001 = search_knowledge(self.workspace_root, query="ADR-001")
        self.assertTrue(len(results_adr001) > 0)
        self.assertIn("001", results_adr001[0].snippet)
        self.assertIn("decision #1", results_adr001[0].snippet)

        results_wal = search_knowledge(self.workspace_root, query="Debezium WAL pgoutput")
        self.assertTrue(len(results_wal) > 0)
        self.assertIn("Debezium", results_wal[0].snippet)

        results_opensearch = search_knowledge(self.workspace_root, query="OpenSearch indexer")
        self.assertTrue(len(results_opensearch) > 0)

    def test_e2e_cross_repo_swarm_dag_lifecycle(self):
        """E2E Test: Cross-repository swarm execution, dependency propagation, and event bus bridge."""
        init_workspace_manifest(self.workspace_root, name="cdc-swarm-ws")
        manifest = load_workspace_manifest(self.workspace_root)

        # Broadcast event across service boundaries
        bus_dir = get_shared_bus_dir(manifest)
        evt_id = broadcast_workspace_event(
            manifest=manifest,
            topic="cdc.outbox.order_created",
            sender="order-service",
            payload={"order_id": "ord-9988", "amount": 149.99, "currency": "USD"},
        )
        self.assertTrue(evt_id.startswith("evt_"))
        self.assertTrue((bus_dir / f"{evt_id}.json").exists())

        # Launch fullstack-feature pipeline across order-service and search-indexer
        run = launch_multi_run(
            manifest=manifest,
            blueprint_name="fullstack-feature",
            context={"feature": "cdc-outbox-streaming", "issue": 101},
        )
        self.assertEqual(run.status, "RUNNING")
        self.assertEqual(run.steps["be-api-spec"].status, "DISPATCHED")
        self.assertEqual(run.steps["be-implementation"].status, "PENDING")

        # Step 1: Architect specifies outbox schema -> COMPLETED
        advance_multi_step(manifest, run.run_id, "be-api-spec", "COMPLETED", result={"schema": "outbox_events"})
        step1_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(step1_run.steps["be-api-spec"].status, "COMPLETED")
        self.assertEqual(step1_run.steps["be-implementation"].status, "DISPATCHED")

        # Step 2: Spring Boot engineer implements entity & outbox write -> COMPLETED
        advance_multi_step(manifest, run.run_id, "be-implementation", "COMPLETED")
        step2_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(step2_run.steps["fe-client-sync"].status, "DISPATCHED")

        # Step 3: Node.js engineer implements OpenSearch streaming consumer -> COMPLETED
        advance_multi_step(manifest, run.run_id, "fe-client-sync", "COMPLETED")
        step3_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(step3_run.steps["cross-test"].status, "DISPATCHED")

        # Step 4: TDD specialist runs cross-boundary integration tests -> COMPLETED
        advance_multi_step(manifest, run.run_id, "cross-test", "COMPLETED")
        step4_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(step4_run.steps["multi-review"].status, "DISPATCHED")

        # Step 5: Code reviewer reviews diffs and anti-bloat compliance -> COMPLETED
        advance_multi_step(manifest, run.run_id, "multi-review", "COMPLETED")
        final_run = get_multi_run(manifest, run.run_id)
        self.assertEqual(final_run.status, "COMPLETED")

        # Status card formatting verification
        card = format_multi_status_card(final_run, manifest)
        self.assertIn("[AGYToolkit Multi-Repo Swarm]", card)
        self.assertIn(final_run.run_id, card)
        self.assertIn("COMPLETED", card)

    def test_e2e_gitops_release_pipeline(self):
        """E2E Test: Conventional commit categorization, SemVer bump, and GitOps release execution."""
        # Add feature commits
        subprocess.run(["git", "commit", "--allow-empty", "-m", "feat(cdc): add debezium outbox connector"], cwd=str(self.workspace_root), capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "fix(consumer): handle consumer idempotency on duplicate events"], cwd=str(self.workspace_root), capture_output=True, check=True)

        # Plan release
        plan = plan_release(self.workspace_root, bump_type="minor")
        self.assertEqual(plan.current_version, "0.1.0")
        self.assertEqual(plan.next_version, "0.2.0")
        self.assertIn("### Features", plan.changelog_snippet)
        self.assertIn("### Bug Fixes", plan.changelog_snippet)
        self.assertIn("add debezium outbox connector", plan.changelog_snippet)
        self.assertIn("handle consumer idempotency", plan.changelog_snippet)

        # Execute release in dry-run mode
        report = execute_release(
            repo_path=self.workspace_root,
            bump_type="minor",
            dry_run=True,
            skip_tests=True,
            allow_branch=True,
        )
        self.assertEqual(report["status"], "DRY_RUN")
        self.assertEqual(report["plan"]["next_version"], "0.2.0")

        # Execute live release: bumps metadata, prepends CHANGELOG.md, and creates git tag v0.2.0
        live_report = execute_release(
            repo_path=self.workspace_root,
            bump_type="minor",
            dry_run=False,
            skip_tests=True,
            allow_branch=True,
        )
        self.assertEqual(live_report["status"], "SUCCESS")
        self.assertEqual(live_report["tag"], "v0.2.0")

        # Verify CHANGELOG.md created
        changelog = self.workspace_root / "CHANGELOG.md"
        self.assertTrue(changelog.exists())
        self.assertIn("## [v0.2.0]", changelog.read_text(encoding="utf-8"))

        # Verify git tag exists
        proc = subprocess.run(["git", "tag", "-l"], cwd=str(self.workspace_root), capture_output=True, text=True, check=True)
        self.assertIn("v0.2.0", proc.stdout)


if __name__ == "__main__":
    unittest.main()
