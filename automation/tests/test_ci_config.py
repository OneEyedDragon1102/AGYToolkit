"""Validation tests for the GitHub Actions CI workflow configuration."""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


class TestCIWorkflowConfiguration(unittest.TestCase):
    def test_ci_workflow_exists(self):
        """Verify .github/workflows/ci.yml is present in the repository."""
        self.assertTrue(CI_WORKFLOW_PATH.exists(), f"Workflow not found at {CI_WORKFLOW_PATH}")

    def test_ci_workflow_structure(self):
        """Verify workflow triggers, OS matrix, and governance gate commands."""
        content = CI_WORKFLOW_PATH.read_text(encoding="utf-8")

        # 1. Triggers
        self.assertIn("push:", content)
        self.assertIn("pull_request:", content)
        self.assertIn("main", content)

        # 2. Multi-OS Matrix
        self.assertIn("ubuntu-latest", content)
        self.assertIn("windows-latest", content)
        self.assertIn("macos-latest", content)
        self.assertIn("3.12", content)

        # 3. Governance and Testing Gates
        self.assertIn("--cov-fail-under=50", content)
        self.assertIn("agy-toolkit doctor", content)
        self.assertIn("Anti-Bloat Code Hygiene Verification", content)
        self.assertIn("doctor-and-scaffold:", content)
        self.assertIn("package-and-smoke:", content)
        self.assertIn("git-discipline:", content)

    def test_pr_review_workflow_structure(self):
        """Verify .github/workflows/pr-review.yml exists and has proper permissions and bot script."""
        pr_path = REPO_ROOT / ".github" / "workflows" / "pr-review.yml"
        self.assertTrue(pr_path.exists())
        content = pr_path.read_text(encoding="utf-8")
        self.assertIn("pull-requests: write", content)
        self.assertIn("agy-toolkit pr-review", content)
        self.assertIn("actions/github-script", content)
        self.assertIn("<!-- AGYToolkit-PR-Review-Bot -->", content)


if __name__ == "__main__":
    unittest.main()
