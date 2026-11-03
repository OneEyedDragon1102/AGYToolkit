"""Unit tests for the AGYToolkit Automated PR Review Bot engine."""

import unittest
from pathlib import Path

from agy_toolkit.pr_reviewer import (
    PR_BOT_SIGNATURE,
    audit_diff_content,
    generate_review_card,
)


class TestPRReviewer(unittest.TestCase):
    def test_audit_diff_content_detects_emojis(self):
        """Verify emoji characters in code diff additions trigger anti-bloat violation."""
        emoji_char = chr(0x1F680)
        diff_text = f"""
diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -1,3 +1,4 @@
 def main():
+    print("{emoji_char} Launching")
     return True
"""
        violations = audit_diff_content(diff_text)
        self.assertTrue(any("Emoji detected" in v for v in violations))

    def test_audit_diff_content_detects_monolithic_files(self):
        """Verify files exceeding 600 lines trigger anti-bloat violation."""
        large_content = "\n".join([f"+line_{i} = {i}" for i in range(650)])
        diff_text = f"""
diff --git a/monolith.py b/monolith.py
new file mode 100644
--- /dev/null
+++ b/monolith.py
@@ -0,0 +1,650 @@
{large_content}
"""
        violations = audit_diff_content(diff_text)
        self.assertTrue(any("Monolithic file detected" in v for v in violations))

    def test_audit_diff_content_clean(self):
        """Verify compliant diffs pass with zero violations."""
        diff_text = """
diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -1,3 +1,4 @@
 def calculate(a, b):
+    # Compute total
     return a + b
"""
        violations = audit_diff_content(diff_text)
        self.assertEqual(len(violations), 0)

    def test_generate_review_card_structure(self):
        """Verify formatted review card contains required signature and governance sections."""
        doctor_data = {
            "is_healthy": True,
            "passed": 12,
            "warnings": 0,
            "failures": 0,
            "checks": [
                {"category": "Toolchains", "name": "Python 3.12", "status": "PASS", "details": "Available"}
            ],
        }
        memory_data = {
            "active_session": {"bytes": 450, "cap": 1024, "within_budget": True},
            "decisions": {"bytes": 1050, "cap": 3072, "within_budget": True},
        }
        test_data = {"passed": 81, "failed": 0, "duration": 34.5}
        diff_violations = []

        card = generate_review_card(
            doctor_report=doctor_data,
            memory_budgets=memory_data,
            test_stats=test_data,
            diff_violations=diff_violations,
        )

        self.assertIn(PR_BOT_SIGNATURE, card)
        self.assertIn("AGYToolkit Autonomous Governance & Health Report", card)
        self.assertIn("Toolchains / Python 3.12", card)
        self.assertIn("81 Passed", card)
        self.assertIn("450 / 1024 bytes", card)
        self.assertIn("Anti-Bloat Sentinel", card)
        self.assertIn("Overall Status: **PASS**", card)

    def test_generate_review_card_failure_mode(self):
        """Verify review card reflects failures when violations or test failures occur."""
        doctor_data = {
            "is_healthy": False,
            "passed": 8,
            "warnings": 1,
            "failures": 2,
            "checks": [],
        }
        memory_data = {
            "active_session": {"bytes": 1100, "cap": 1024, "within_budget": False},
            "decisions": {"bytes": 1050, "cap": 3072, "within_budget": True},
        }
        test_data = {"passed": 80, "failed": 1, "duration": 25.0}
        diff_violations = ["Emoji detected in auth.py"]

        card = generate_review_card(
            doctor_report=doctor_data,
            memory_budgets=memory_data,
            test_stats=test_data,
            diff_violations=diff_violations,
        )

        self.assertIn("Overall Status: **FAIL**", card)
        self.assertIn("Emoji detected in auth.py", card)
        self.assertIn("active-session.md: 1100 / 1024 bytes (FAIL)", card)


if __name__ == "__main__":
    unittest.main()
