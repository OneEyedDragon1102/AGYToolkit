"""End-to-end integration tests for AGYToolkit scaffolding, doctor diagnostics, and global linker."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agy_toolkit.doctor import run_doctor
from agy_toolkit.linker import link_global
from agy_toolkit.scaffolder import scaffold_project


class TestIntegrationHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_e2e_scaffold_and_doctor_pass(self):
        """Scaffold a project and verify doctor reports 0 governance failures."""
        res = scaffold_project(
            target_path=self.target,
            project_name="e2e-order-service",
            stack="spring-boot",
            mode="feature",
        )

        self.assertEqual(res["agents_installed"], 15)
        self.assertEqual(res["skills_installed"], 28)
        self.assertTrue(res["memory_initialized"])

        # Run doctor audit
        report = run_doctor(target_path=self.target)

        # Filter governance, agents, skills, memory checks (exclude host toolchain warnings)
        gov_results = [r for r in report.results if r.category in ["Governance", "Agents", "Skills", "Memory"]]
        gov_failures = [r for r in gov_results if r.status == "FAIL"]

        self.assertEqual(len(gov_failures), 0, f"Unexpected governance failures: {gov_failures}")

        # Check explicit passing items
        pass_names = [r.name for r in gov_results if r.status == "PASS"]
        self.assertIn("Project Rules (GEMINI.md)", pass_names)
        self.assertIn("Agent Instructions (AGENTS.md)", pass_names)
        self.assertIn("Lifecycle Hooks Config (hooks.json)", pass_names)
        self.assertIn("Lifecycle Hook Scripts", pass_names)
        self.assertIn("Specialist Agents Matrix", pass_names)
        self.assertIn("Progressive Skills Catalog", pass_names)
        self.assertIn("Active Session Budget", pass_names)
        self.assertIn("Decisions Log Budget", pass_names)
        self.assertIn("Gitignore Memory Exclusions", pass_names)

    def test_e2e_doctor_detects_memory_overflow(self):
        """Verify doctor flags session memory exceeding 1024 bytes."""
        scaffold_project(target_path=self.target, project_name="overflow-test")

        active_file = self.target / ".agents" / "memory" / "active-session.md"
        # Write 2 KB payload
        active_file.write_text("x" * 2048, encoding="utf-8")

        report = run_doctor(target_path=self.target)
        mem_results = [r for r in report.results if r.name == "Active Session Budget"]
        self.assertEqual(len(mem_results), 1)
        self.assertEqual(mem_results[0].status, "FAIL")
        self.assertIn("exceeds 1024 byte limit", mem_results[0].details)

    def test_e2e_global_linker_mounts_assets(self):
        """Verify link_global mounts 28 skills and 15 agents into custom config dir."""
        config_dir = self.target / "gemini_config"
        stats = link_global(mode="copy", config_dir=config_dir)

        self.assertEqual(stats["skills_linked"], 28)
        self.assertEqual(stats["agents_linked"], 15)
        self.assertEqual(len(stats["errors"]), 0)

        # Verify filesystem in config dir
        skills_path = config_dir / "skills"
        agents_path = config_dir / "agents"
        self.assertEqual(len(list(skills_path.glob("*/SKILL.md"))), 28)
        self.assertEqual(len(list(agents_path.glob("*.md"))), 15)

    def test_e2e_anti_bloat_hook_execution(self):
        """Execute anti-bloat-check.ps1 hook with mock tool inputs."""
        scaffold_project(target_path=self.target, project_name="hook-test")
        hook_ps1 = self.target / ".agents" / "hooks" / "anti-bloat-check.ps1"

        if sys.platform != "win32" or not shutil_which("powershell"):
            return

        # 1. Clean payload -> should pass with decision="allow"
        clean_input = json.dumps({
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "src/App.java",
                    "Content": "public class App { public static void main(String[] args) {} }"
                }
            }
        })
        proc_clean = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(hook_ps1)],
            input=clean_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc_clean.returncode, 0, f"Clean hook failed: {proc_clean.stderr}")
        res_clean = json.loads(proc_clean.stdout.strip())
        self.assertEqual(res_clean.get("decision"), "allow")

        # 2. Bloated payload with emoji -> should deny with decision="deny"
        emoji_char = chr(0x1F680)
        bloat_input = json.dumps({
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "src/App.java",
                    "Content": f"// Rocket ship {emoji_char}\npublic class App {{}}"
                }
            }
        })
        proc_bloat = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(hook_ps1)],
            input=bloat_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc_bloat.returncode, 0, f"Hook invocation failed: {proc_bloat.stderr}")
        res_bloat = json.loads(proc_bloat.stdout.strip())
        self.assertEqual(res_bloat.get("decision"), "deny")
        self.assertIn("emojis detected", res_bloat.get("reason", "").lower())


def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)


if __name__ == "__main__":
    unittest.main()
