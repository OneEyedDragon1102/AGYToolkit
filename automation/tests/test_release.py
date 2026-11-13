"""Unit tests for AGYToolkit GitOps Automated Release Bot."""

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main as cli_main
from agy_toolkit.mcp_release import handle_release_mcp_tool
from agy_toolkit.release import (
    ConventionalCommit,
    SemVer,
    categorize_commits,
    check_release_branch,
    check_working_tree_clean,
    execute_release,
    generate_changelog_entry,
    get_current_project_version,
    parse_conventional_commit,
    plan_release,
    prepend_changelog,
    sync_version_metadata,
)


class TestRelease(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)

        # Initialize mock git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.repo_dir), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "AGYBot"], cwd=str(self.repo_dir), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "bot@agytoolkit.local"], cwd=str(self.repo_dir), capture_output=True, check=True)

        # Mock pyproject.toml
        self.pyproject = self.repo_dir / "pyproject.toml"
        self.pyproject.write_text('[project]\nname = "test-pkg"\nversion = "0.1.0"\n', encoding="utf-8")

        # Mock __init__.py
        self.init_py = self.repo_dir / "automation" / "src" / "agy_toolkit" / "__init__.py"
        self.init_py.parent.mkdir(parents=True, exist_ok=True)
        self.init_py.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

        # Mock mcp_server.py
        self.mcp_py = self.repo_dir / "automation" / "src" / "agy_toolkit" / "mcp_server.py"
        self.mcp_py.write_text('SERVER_VERSION = "0.1.0"\n', encoding="utf-8")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=str(self.repo_dir), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feat(core): initial framework setup"], cwd=str(self.repo_dir), capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_semver_parse_and_bump(self):
        """Verify SemVer parsing and incrementing for patch, minor, and major."""
        v = SemVer.parse("0.1.0")
        self.assertEqual(str(v), "0.1.0")

        v_patch = v.bump("patch")
        self.assertEqual(str(v_patch), "0.1.1")

        v_minor = v.bump("minor")
        self.assertEqual(str(v_minor), "0.2.0")

        v_major = v.bump("major")
        self.assertEqual(str(v_major), "1.0.0")

        # Invalid bump
        with self.assertRaises(ValueError):
            v.bump("invalid")

        # Invalid parse
        with self.assertRaises(ValueError):
            SemVer.parse("1.2")

    def test_parse_conventional_commits(self):
        """Verify regex extraction of conventional commit components."""
        c1 = parse_conventional_commit("abc1234", "feat(auth): add jwt validation")
        self.assertIsNotNone(c1)
        self.assertEqual(c1.type, "feat")
        self.assertEqual(c1.scope, "auth")
        self.assertEqual(c1.description, "add jwt validation")
        self.assertFalse(c1.breaking)
        self.assertIn("feat(auth)", c1.format_bullet())

        c2 = parse_conventional_commit("def5678", "fix!: drop deprecated endpoints")
        self.assertIsNotNone(c2)
        self.assertEqual(c2.type, "fix")
        self.assertIsNone(c2.scope)
        self.assertTrue(c2.breaking)
        self.assertIn("[BREAKING]", c2.format_bullet())

        c3 = parse_conventional_commit("ghi9012", "Merge branch main")
        self.assertIsNone(c3)

    def test_categorize_commits(self):
        """Verify sorting commits into structured conventional buckets."""
        raw_commits = [
            ("111", "feat(bus): add volatile bus"),
            ("222", "fix(memory): prevent buffer overflow"),
            ("333", "docs: update getting started guide"),
            ("444", "chore: bump dependencies"),
            ("555", "Random unstructured commit"),
        ]
        cats, uncats = categorize_commits(raw_commits)
        self.assertEqual(len(cats["Features"]), 1)
        self.assertEqual(len(cats["Bug Fixes"]), 1)
        self.assertEqual(len(cats["Documentation"]), 1)
        self.assertEqual(len(cats["Maintenance & Dependencies"]), 1)
        self.assertEqual(len(uncats), 1)

    def test_changelog_generation_and_prepend(self):
        """Verify generating changelog markdown and prepending to CHANGELOG.md."""
        raw_commits = [("abc", "feat(cli): add release bot")]
        cats, uncats = categorize_commits(raw_commits)
        entry = generate_changelog_entry("0.2.0", "2026-11-13", cats, uncats)
        self.assertIn("## [v0.2.0] - 2026-11-13", entry)
        self.assertIn("### Features", entry)

        cl_path = prepend_changelog(self.repo_dir, entry)
        self.assertTrue(cl_path.exists())
        text = cl_path.read_text(encoding="utf-8")
        self.assertIn("# Changelog", text)
        self.assertIn("[v0.2.0]", text)

    def test_sync_version_metadata(self):
        """Verify atomic version updates across pyproject.toml and source files."""
        updated = sync_version_metadata(self.repo_dir, "0.2.0")
        self.assertEqual(len(updated), 3)

        self.assertEqual(get_current_project_version(self.repo_dir), "0.2.0")
        self.assertIn('__version__ = "0.2.0"', self.init_py.read_text(encoding="utf-8"))
        self.assertIn('SERVER_VERSION = "0.2.0"', self.mcp_py.read_text(encoding="utf-8"))

    def test_preflight_gates(self):
        """Verify clean working tree and branch checks."""
        # On main with clean tree
        clean, _ = check_working_tree_clean(self.repo_dir)
        self.assertTrue(clean)

        branch_ok, _ = check_release_branch(self.repo_dir, allowed_branches=["main"])
        self.assertTrue(branch_ok)

        # Dirty tree check
        dirty_file = self.repo_dir / "dirty.txt"
        dirty_file.write_text("modified", encoding="utf-8")
        subprocess.run(["git", "add", "dirty.txt"], cwd=str(self.repo_dir), capture_output=True, check=True)
        clean_after, msg = check_working_tree_clean(self.repo_dir)
        self.assertFalse(clean_after)
        self.assertIn("Uncommitted changes", msg)

    def test_plan_release(self):
        """Verify constructing a complete release plan."""
        plan = plan_release(self.repo_dir, "minor")
        self.assertEqual(plan.current_version, "0.1.0")
        self.assertEqual(plan.next_version, "0.2.0")
        self.assertEqual(plan.bump_type, "minor")
        self.assertEqual(plan.commits_count, 1)
        self.assertIn("pyproject.toml", plan.files_to_update)

    def test_execute_release_dry_run(self):
        """Verify dry-run mode returns plan without modifying git state."""
        report = execute_release(
            repo_path=self.repo_dir,
            bump_type="patch",
            dry_run=True,
            skip_tests=True,
            allow_branch=True,
        )
        self.assertEqual(report["status"], "DRY_RUN")
        self.assertEqual(report["plan"]["next_version"], "0.1.1")

        # Version on disk must remain unchanged
        self.assertEqual(get_current_project_version(self.repo_dir), "0.1.0")

    def test_execute_release_live(self):
        """Verify cutting an actual release creates commit and annotated git tag."""
        report = execute_release(
            repo_path=self.repo_dir,
            bump_type="minor",
            dry_run=False,
            skip_tests=True,
            allow_branch=True,
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["tag"], "v0.2.0")
        self.assertEqual(report["version"], "0.2.0")

        # Check git tag was created
        proc = subprocess.run(["git", "tag", "-l"], cwd=str(self.repo_dir), capture_output=True, text=True, check=True)
        self.assertIn("v0.2.0", proc.stdout)

        # Check version updated on disk
        self.assertEqual(get_current_project_version(self.repo_dir), "0.2.0")

    def test_cli_release_commands(self):
        """Verify CLI release --notes-only and --dry-run subcommands."""
        # notes-only
        out_notes = io.StringIO()
        with redirect_stdout(out_notes):
            code = cli_main(["release", "minor", str(self.repo_dir), "--notes-only"])
        self.assertEqual(code, 0)
        self.assertIn("[AGYToolkit Release Plan]", out_notes.getvalue())
        self.assertIn("v0.2.0", out_notes.getvalue())

        # dry-run
        out_dry = io.StringIO()
        with redirect_stdout(out_dry):
            code = cli_main(["release", "patch", str(self.repo_dir), "--dry-run", "--skip-tests", "--allow-branch"])
        self.assertEqual(code, 0)
        self.assertIn("[AGYToolkit Release Simulation]", out_dry.getvalue())

    def test_mcp_release_tools(self):
        """Verify MCP agy_release_plan and agy_release_create handlers."""
        # agy_release_plan
        text, is_err = handle_release_mcp_tool(
            self.repo_dir, "agy_release_plan", {"bump_type": "major"}
        )
        self.assertFalse(is_err)
        self.assertIn("v1.0.0", text)

        # agy_release_create (dry run)
        text_create, is_err_create = handle_release_mcp_tool(
            self.repo_dir,
            "agy_release_create",
            {"bump_type": "patch", "dry_run": True, "skip_tests": True, "allow_branch": True},
        )
        self.assertFalse(is_err_create)
        self.assertIn("DRY RUN ACTIVE", text_create)

        # Invalid bump type error
        _, is_err_bad = handle_release_mcp_tool(
            self.repo_dir, "agy_release_plan", {"bump_type": "invalid"}
        )
        self.assertTrue(is_err_bad)


if __name__ == "__main__":
    unittest.main()
