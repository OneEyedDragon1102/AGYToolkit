"""Unit tests for the AGYToolkit Agent Registry (Markdown Hybrid Specs)."""

import unittest
from agy_toolkit.agents import (
    load_agent,
    list_agents,
    validate_agent_spec,
    parse_frontmatter,
    REQUIRED_FIELDS,
)


class TestAgentRegistry(unittest.TestCase):
    def test_core_agents_exist(self):
        core_agents = [
            "orchestrator",
            "planner-architect",
            "spring-boot-engineer",
            "node-ts-engineer",
            "python-automation-lead",
        ]
        available_names = [a["name"] for a in list_agents()]
        for name in core_agents:
            self.assertIn(name, available_names)

    def test_load_orchestrator_markdown(self):
        agent = load_agent("orchestrator")
        self.assertEqual(agent["name"], "orchestrator")
        self.assertEqual(agent["role"], "Master Project Conductor")
        self.assertFalse(agent["enableWriteTools"])
        self.assertTrue(agent["enableSubagentTools"])
        self.assertEqual(agent["recommendedWorkspace"], "inherit")
        self.assertIn("Handoff Contract", agent["systemPrompt"])
        self.assertIn("Definition of Done", agent["systemPrompt"])

    def test_load_spring_boot_engineer_markdown(self):
        agent = load_agent("spring-boot-engineer")
        self.assertEqual(agent["name"], "spring-boot-engineer")
        self.assertTrue(agent["enableWriteTools"])
        self.assertFalse(agent["enableSubagentTools"])
        self.assertEqual(agent["recommendedWorkspace"], "branch")
        self.assertIn("hexagonal architecture", agent["systemPrompt"])
        self.assertIn("Definition of Done", agent["systemPrompt"])

    def test_parse_frontmatter(self):
        content = """---
name: sample-agent
role: Sample Role
enableWriteTools: true
enableSubagentTools: false
---
# Sample Body
Body line 1
"""
        meta, body = parse_frontmatter(content)
        self.assertEqual(meta["name"], "sample-agent")
        self.assertEqual(meta["role"], "Sample Role")
        self.assertTrue(meta["enableWriteTools"])
        self.assertFalse(meta["enableSubagentTools"])
        self.assertIn("# Sample Body", body)

    def test_anti_bloat_validation(self):
        emoji_char = chr(0x1F680)
        invalid_spec = {
            "name": "bloated-agent",
            "role": "Bloated Engineer",
            "description": "An agent with emojis",
            "systemPrompt": f"Hello world {emoji_char}",
            "enableWriteTools": True,
            "enableSubagentTools": False,
            "enableMCPTools": False,
            "recommendedWorkspace": "branch",
        }
        errors = validate_agent_spec(invalid_spec)
        self.assertTrue(any("Anti-Bloat violation" in e for e in errors))

    def test_missing_fields_validation(self):
        incomplete_spec = {"name": "incomplete"}
        errors = validate_agent_spec(incomplete_spec)
        self.assertTrue(len(errors) >= len(REQUIRED_FIELDS) - 1)


if __name__ == "__main__":
    unittest.main()
