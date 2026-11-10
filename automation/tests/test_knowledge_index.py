"""Unit tests for Tier 3 Permanent Semantic Knowledge Index (SQLite FTS5)."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.knowledge import (
    get_db_path,
    get_knowledge_stats,
    index_workspace,
    parse_decisions_markdown,
    parse_general_markdown,
    parse_sessions_markdown,
    sanitize_fts_query,
    search_knowledge,
)
from agy_toolkit.mcp_knowledge import handle_knowledge_tool
from agy_toolkit.memory import auto_compact_memory


class TestKnowledgeIndex(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="agy_test_know_")
        self.workspace_dir = Path(self.temp_dir).resolve()

        # Create standard directories
        self.mem_dir = self.workspace_dir / ".agents" / "memory"
        self.sessions_dir = self.mem_dir / "sessions"
        self.adr_dir = self.workspace_dir / "docs" / "adr"
        self.docs_dir = self.workspace_dir / "docs"

        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.adr_dir.mkdir(parents=True, exist_ok=True)

        # 1. Sample decisions.md
        decisions_content = """# Binding Architectural Decisions Register

- **2026-11-01 [ARCH]**: Adopt Hexagonal Architecture with inbound ports and outbound JPA adapters.
- **2026-11-02 [BUS]**: Multi-agent IPC event bus utilizing volatile memory with atomic JSON envelopes.
- **2026-11-03 [SEC]**: Enforce strict zero-leakage token boundaries for subagent sandboxes.
"""
        (self.mem_dir / "decisions.md").write_text(decisions_content, encoding="utf-8")

        # 2. Sample archived session
        session_content = """# Active Session Summary

## Goal
Implement swarm task leases and heartbeats.

## Key Outcomes
Implemented background lease renewal thread and atomic reclaim sweeps.

## Open Blockers
None. Concurrency tests passing.
"""
        (self.sessions_dir / "session-2026-11-05_session.md").write_text(
            session_content, encoding="utf-8"
        )

        # 3. Sample decisions history (ADR)
        adr_content = """# Architectural Decisions History (Archived)

- **2026-10-20 [PERF]**: Use SQLite memory-mapped IO and connection pooling for high throughput.
- **2026-10-22 [API]**: Standardize JSON-RPC 2.0 schema envelopes across all MCP tools.
"""
        (self.adr_dir / "decisions-history.md").write_text(adr_content, encoding="utf-8")

        # 4. Sample GEMINI.md
        rules_content = """# Project Coding Standards

## Anti-Bloat Sentinel
Zero emojis in source code files, logs, or comments. Maximum 600 lines per file.
"""
        (self.workspace_dir / "GEMINI.md").write_text(rules_content, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitize_fts_query(self):
        self.assertEqual(sanitize_fts_query("hexagonal architecture"), '"hexagonal"* "architecture"*')
        self.assertEqual(sanitize_fts_query(""), "")
        self.assertEqual(sanitize_fts_query("sqlite! fts5?"), '"sqlite"* "fts5"*')

    def test_parse_decisions_markdown(self):
        text = """
- **2026-11-01 [ARCH]**: Use Hexagonal Architecture.
- **2026-11-02 [BUS]**: Use volatile event bus.
"""
        docs = parse_decisions_markdown(text, ".agents/memory/decisions.md")
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].category, "ARCH")
        self.assertEqual(docs[0].date, "2026-11-01")
        self.assertIn("Hexagonal Architecture", docs[0].content)

    def test_parse_sessions_markdown(self):
        text = """
## Goal
Deploy Swarm worker.

## Outcomes
Worker daemon running.
"""
        docs = parse_sessions_markdown(text, ".agents/memory/sessions/session-2026-11-02.md")
        self.assertGreaterEqual(len(docs), 2)
        self.assertEqual(docs[0].category, "SESSION")
        self.assertIn("Goal", docs[0].title)

    def test_parse_general_markdown(self):
        text = """# Rules

## Section One
First section content here that has sufficient length.

## Section Two
Second section content here with important architectural details.
"""
        docs = parse_general_markdown(text, "GEMINI.md", default_category="RULE")
        self.assertGreaterEqual(len(docs), 2)
        self.assertEqual(docs[0].category, "RULE")

    def test_index_workspace_and_search(self):
        report = index_workspace(self.workspace_dir)
        self.assertGreater(report.indexed_files, 0)
        self.assertGreater(report.total_documents, 0)

        db_path = get_db_path(self.workspace_dir)
        self.assertTrue(db_path.exists())

        # Full-text search for Hexagonal
        results = search_knowledge(self.workspace_dir, "Hexagonal")
        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertEqual(top.category, "ARCH")
        self.assertIn("Hexagonal", top.title + top.snippet)
        self.assertIn(".agents/memory/decisions.md", top.source_file)

        # Full-text search for SQLite in ADR history
        results_sqlite = search_knowledge(self.workspace_dir, "SQLite")
        self.assertGreaterEqual(len(results_sqlite), 1)
        self.assertEqual(results_sqlite[0].category, "PERF")

    def test_search_with_category_filter(self):
        index_workspace(self.workspace_dir)

        # Search with matching category
        results_bus = search_knowledge(self.workspace_dir, "volatile", category="BUS")
        self.assertEqual(len(results_bus), 1)
        self.assertEqual(results_bus[0].category, "BUS")

        # Search with non-matching category
        results_none = search_knowledge(self.workspace_dir, "volatile", category="ARCH")
        self.assertEqual(len(results_none), 0)

    def test_search_no_match_returns_empty(self):
        index_workspace(self.workspace_dir)
        results = search_knowledge(self.workspace_dir, "nonexistentphrasexyz123")
        self.assertEqual(len(results), 0)

    def test_incremental_indexing(self):
        report1 = index_workspace(self.workspace_dir)
        self.assertGreater(report1.indexed_files, 0)

        # Second indexing without changes should skip files
        report2 = index_workspace(self.workspace_dir)
        self.assertEqual(report2.indexed_files, 0)
        self.assertEqual(report2.skipped_files, report1.indexed_files)

        # Force reindexing should re-read all
        report3 = index_workspace(self.workspace_dir, force=True)
        self.assertGreater(report3.indexed_files, 0)

    def test_get_knowledge_stats(self):
        index_workspace(self.workspace_dir)
        stats = get_knowledge_stats(self.workspace_dir)
        self.assertTrue(stats["exists"])
        self.assertGreater(stats["total_documents"], 0)
        self.assertIn("ARCH", stats["categories"])
        self.assertGreater(stats["size_bytes"], 0)

    def test_cli_memory_search_and_reindex(self):
        # 1. Reindex via CLI
        buf_reindex = io.StringIO()
        with redirect_stdout(buf_reindex):
            ret_reindex = main(["memory", "reindex", str(self.workspace_dir), "--force"])
        self.assertEqual(ret_reindex, 0)
        self.assertIn("Reindexed Workspace", buf_reindex.getvalue())

        # 2. Search via CLI in text mode
        buf_search = io.StringIO()
        with redirect_stdout(buf_search):
            ret_search = main(["memory", "search", "Hexagonal", str(self.workspace_dir)])
        self.assertEqual(ret_search, 0)
        out_search = buf_search.getvalue()
        self.assertIn("Knowledge Search", out_search)
        self.assertIn("Hexagonal", out_search)

        # 3. Search via CLI in JSON mode
        buf_json = io.StringIO()
        with redirect_stdout(buf_json):
            ret_json = main(["memory", "search", "Hexagonal", str(self.workspace_dir), "--json"])
        self.assertEqual(ret_json, 0)
        self.assertIn('"category": "ARCH"', buf_json.getvalue())

    def test_mcp_knowledge_tools(self):
        # Test agy_memory_reindex
        res_reindex = handle_knowledge_tool(self.workspace_dir, "agy_memory_reindex", {"force": True})
        self.assertIsNotNone(res_reindex)
        self.assertIn("Knowledge Index Rebuilt", res_reindex["content"][0]["text"])

        # Test agy_memory_search
        res_search = handle_knowledge_tool(
            self.workspace_dir, "agy_memory_search", {"query": "Hexagonal"}
        )
        self.assertIsNotNone(res_search)
        self.assertIn("Knowledge Search Results", res_search["content"][0]["text"])
        self.assertGreater(len(res_search["data"]), 0)

    def test_auto_compact_triggers_indexing(self):
        # Inflate decisions beyond threshold
        fat_decisions = "# Binding Decisions\n\n" + "\n".join(
            f"- **2026-11-{i:02d} [TEST]**: Decision number {i:03d} detailing system constraints."
            for i in range(1, 40)
        )
        (self.mem_dir / "decisions.md").write_text(fat_decisions, encoding="utf-8")

        # Run compaction
        report = auto_compact_memory(
            memory_dir=self.mem_dir,
            workspace_root=self.workspace_dir,
            threshold=0.50,
            dry_run=False,
        )
        self.assertTrue(report.decisions_compacted)

        # Verify knowledge database indexed the newly evicted ADRs
        db_path = get_db_path(self.workspace_dir)
        self.assertTrue(db_path.exists())

        results = search_knowledge(self.workspace_dir, "constraints", category="TEST")
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
