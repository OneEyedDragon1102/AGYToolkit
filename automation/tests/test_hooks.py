"""Unit tests for AGY lifecycle hooks."""

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / ".agents" / "hooks"


def run_powershell_hook(script_name: str, payload: dict) -> dict:
    script_path = HOOKS_DIR / script_name
    input_str = json.dumps(payload)
    ps_cmd = shutil.which("powershell") or shutil.which("pwsh")

    if ps_cmd:
        cmd = [
            ps_cmd,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ]
    elif shutil.which("bash"):
        sh_name = script_name.replace(".ps1", ".sh")
        script_path = HOOKS_DIR / sh_name
        cmd = ["bash", str(script_path)]
    else:
        return {"decision": "allow"}

    proc = subprocess.run(
        cmd,
        input=input_str,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, f"Hook failed: {proc.stderr}"
    stdout = proc.stdout.strip()
    return json.loads(stdout)


class TestAntiBloatHook(unittest.TestCase):
    def test_allows_clean_code(self):
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "src/App.java",
                    "Content": "public class App { public static void main(String[] args) {} }",
                },
            }
        }
        res = run_powershell_hook("anti-bloat-check.ps1", payload)
        self.assertEqual(res.get("decision"), "allow")

    def test_blocks_emojis_in_code(self):
        rocket = chr(0x1F680)
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "src/service.ts",
                    "Content": f"const greeting = 'hello {rocket}';",
                },
            }
        }
        res = run_powershell_hook("anti-bloat-check.ps1", payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("emojis detected", res.get("reason", "").lower())

    def test_allows_emojis_in_markdown(self):
        rocket = chr(0x1F680)
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "README.md",
                    "Content": f"# Hello World {rocket}",
                },
            }
        }
        res = run_powershell_hook("anti-bloat-check.ps1", payload)
        self.assertEqual(res.get("decision"), "allow")

    def test_blocks_monolithic_dump(self):
        monolithic_content = "\n".join([f"line_{i} = {i}" for i in range(650)])
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "src/monolith.py",
                    "Content": monolithic_content,
                },
            }
        }
        res = run_powershell_hook("anti-bloat-check.ps1", payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("monolithic file", res.get("reason", "").lower())


class TestBranchRuleHook(unittest.TestCase):
    def test_allows_standard_command(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npm test"},
            }
        }
        res = run_powershell_hook("enforce-branch-rule.ps1", payload)
        self.assertEqual(res.get("decision"), "allow")

    def test_allows_git_status(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            }
        }
        res = run_powershell_hook("enforce-branch-rule.ps1", payload)
        self.assertEqual(res.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
