"""Unit tests for the AGYToolkit Progressive Skills Catalog."""

import re
import unittest
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / ".agents" / "skills"

EXPECTED_28_SKILLS = [
    # Track A: Planning & Architecture (6)
    "adr-architect",
    "plan-approval-gate",
    "task-decomposer",
    "context-budgeter",
    "telemetry-logger",
    "handbook-enforcer",
    # Track B: TDD & Implementation (7)
    "tdd-spring-boot",
    "tdd-node-ts",
    "tdd-python",
    "spring-service-generator",
    "node-mcp-builder",
    "ui-component-builder",
    "refactor-cleaner",
    # Track C: Review & Quality Gates (6)
    "code-reviewer",
    "anti-bloat-linter",
    "security-scanner",
    "coverage-verifier",
    "concurrency-auditor",
    "api-contract-checker",
    # Track D: Git, Staging & CI/CD (5)
    "commit-craft",
    "branch-manager",
    "selective-stager",
    "release-packager",
    "ci-pipeline-validator",
    # Track E: Meta-Framework & Extensibility (4)
    "agy-inspector",
    "skill-author",
    "agent-author",
    "workspace-doctor",
]

EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]")


def parse_frontmatter(content: str):
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    metadata = {}
    body_start_idx = -1

    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start_idx = idx + 1
            break
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()

    body = "\n".join(lines[body_start_idx:]) if body_start_idx != -1 else ""
    return metadata, body


class TestSkillsCatalog(unittest.TestCase):
    def test_skills_directory_exists(self):
        self.assertTrue(SKILLS_DIR.exists(), f"Skills dir not found at {SKILLS_DIR}")

    def test_all_28_skills_exist(self):
        self.assertEqual(len(EXPECTED_28_SKILLS), 28)
        for skill_name in EXPECTED_28_SKILLS:
            skill_path = SKILLS_DIR / skill_name / "SKILL.md"
            self.assertTrue(skill_path.exists(), f"Missing skill file: {skill_path}")

    def test_skill_frontmatter_and_structure(self):
        for skill_name in EXPECTED_28_SKILLS:
            skill_path = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_path.read_text(encoding="utf-8")

            # Frontmatter check
            meta, body = parse_frontmatter(content)
            self.assertIn("name", meta, f"{skill_name} missing 'name' in frontmatter")
            self.assertEqual(meta["name"], skill_name, f"Frontmatter name mismatch in {skill_name}")
            self.assertIn("description", meta, f"{skill_name} missing 'description' in frontmatter")
            self.assertTrue(len(meta["description"]) > 10, f"{skill_name} description too short")

            # Structure checks
            self.assertIn("## Overview", body, f"{skill_name} missing '## Overview'")
            has_protocol = ("## Operational Protocol" in body) or ("## Quick Audit Procedure" in body)
            self.assertTrue(has_protocol, f"{skill_name} missing operational protocol section")
            self.assertIn("## Quality Gate & Verification Checklist", body, f"{skill_name} missing verification checklist")

    def test_anti_bloat_zero_emojis(self):
        for skill_name in EXPECTED_28_SKILLS:
            skill_path = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_path.read_text(encoding="utf-8")
            emojis_found = EMOJI_PATTERN.findall(content)
            self.assertEqual(
                len(emojis_found),
                0,
                f"Bloat alert: Emoji(s) detected in {skill_name}: {emojis_found}",
            )


if __name__ == "__main__":
    unittest.main()
