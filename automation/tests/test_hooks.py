"""Unit tests for AGY lifecycle hooks."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / ".agents" / "hooks"


def run_powershell_hook(script_name: str, payload: dict, cwd: Path = None) -> dict:
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
        cwd=str(cwd) if cwd else None,
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

    def test_blocks_emojis_in_yaml_and_sql(self):
        rocket = chr(0x1F680)
        for ext in ["yml", "yaml", "sql", "json", "sh", "ps1"]:
            payload = {
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": f"infra/config.{ext}",
                        "Content": f"# Configuration with {rocket}",
                    },
                }
            }
            res = run_powershell_hook("anti-bloat-check.ps1", payload)
            self.assertEqual(res.get("decision"), "deny", f"Failed to deny emoji in {ext}")
            self.assertIn("emojis detected", res.get("reason", "").lower())

    def test_blocks_monolithic_yaml_and_sql(self):
        monolithic_content = "\n".join([f"key_{i}: val_{i}" for i in range(650)])
        for ext in ["yml", "sql"]:
            payload = {
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": f"db/migration.{ext}",
                        "Content": monolithic_content,
                    },
                }
            }
            res = run_powershell_hook("anti-bloat-check.ps1", payload)
            self.assertEqual(res.get("decision"), "deny", f"Failed to deny monolithic {ext}")
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


class TestAutoCompactMemoryHook(unittest.TestCase):
    def test_allows_normal_tool_use(self):
        payload = {
            "toolCall": {
                "name": "write_file",
                "args": {"Path": "src/dummy.ts", "Content": "const a = 1;"},
            }
        }
        res = run_powershell_hook("auto-compact-memory.ps1", payload)
        self.assertEqual(res.get("decision"), "allow")


class TestSecretLeakSentinelHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        subprocess.run(["git", "init"], cwd=str(self.repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "TestUser"], cwd=str(self.repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(self.repo_path), check=True, capture_output=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_allows_non_commit_command(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "allow")

    def test_blocks_staging_raw_env_file(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git add .env"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn(".env", res.get("reason", "").lower())

    def test_allows_staging_env_example(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git add .env.example"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "allow")

    def test_blocks_commit_with_private_key(self):
        cert_file = self.repo_path / "cert.txt"
        probe = "-----" + "BEGIN RSA PRIVATE KEY" + "-----\nMIIEowIBAAKCAQEA...\n-----" + "END RSA PRIVATE KEY" + "-----"
        cert_file.write_text(probe, encoding="utf-8")
        subprocess.run(["git", "add", "cert.txt"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add server config'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("private key", res.get("reason", "").lower())

    def test_blocks_commit_with_key_file_extension(self):
        key_file = self.repo_path / "server.key"
        key_file.write_text("dummy key content", encoding="utf-8")
        subprocess.run(["git", "add", "server.key"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add key file'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("sensitive file", res.get("reason", "").lower())

    def test_blocks_commit_with_hardcoded_password(self):
        app_yml = self.repo_path / "application.yml"
        probe = "datasource:\n  " + "pass" + "word: 'ProductionSecret123!'\n"
        app_yml.write_text(probe, encoding="utf-8")
        subprocess.run(["git", "add", "application.yml"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: update config'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("credential", res.get("reason", "").lower())

    def test_blocks_commit_with_host_path_leak(self):
        script_file = self.repo_path / "deploy.sh"
        probe = "export JAVA_HOME='" + "C:\\\\Users\\\\" + "john_developer\\\\jdk-23'\n"
        script_file.write_text(probe, encoding="utf-8")
        subprocess.run(["git", "add", "deploy.sh"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add deploy script'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("host filesystem", res.get("reason", "").lower())

    def test_blocks_commit_with_staged_env_file(self):
        env_file = self.repo_path / ".env"
        env_file.write_text("DB_PASS=secret\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", ".env"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add env'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("sensitive file", res.get("reason", "").lower())

    def test_allows_commit_with_clean_code(self):
        clean_file = self.repo_path / "main.py"
        clean_file.write_text("import os\n\ndef run():\n    db_pass = os.environ.get('DB_PASSWORD')\n    print('Running')\n", encoding="utf-8")
        subprocess.run(["git", "add", "main.py"], cwd=str(self.repo_path), check=True, capture_output=True)

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add clean service'"},
            }
        }
        res = run_powershell_hook("secret-leak-sentinel.ps1", payload, cwd=self.repo_path)
        self.assertEqual(res.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
