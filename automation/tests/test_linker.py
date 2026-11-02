"""Unit tests for agy_toolkit.linker global mounting engine."""

import tempfile
import unittest
from pathlib import Path

from agy_toolkit.linker import link_global, get_global_config_dir


class TestGlobalLinker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_global_config_dir(self):
        """Verify default global config path resolves under user home."""
        path = get_global_config_dir()
        self.assertTrue(str(path).endswith(".gemini\\config") or str(path).endswith(".gemini/config"))

    def test_link_global_dry_run(self):
        """Verify dry run calculates counts without writing to disk."""
        stats = link_global(mode="copy", dry_run=True, config_dir=self.config_dir)
        self.assertTrue(stats["dry_run"])
        self.assertEqual(stats["skills_linked"], 28)
        self.assertEqual(stats["agents_linked"], 15)
        # Verify nothing written
        self.assertFalse((self.config_dir / "skills").exists())

    def test_link_global_copy_mode(self):
        """Verify copy mode mounts all skills and agents."""
        stats = link_global(mode="copy", dry_run=False, config_dir=self.config_dir)
        self.assertEqual(stats["skills_linked"], 28)
        self.assertEqual(stats["agents_linked"], 15)
        self.assertEqual(len(stats["errors"]), 0)

        skills = list((self.config_dir / "skills").glob("*/SKILL.md"))
        agents = list((self.config_dir / "agents").glob("*.md"))
        self.assertEqual(len(skills), 28)
        self.assertEqual(len(agents), 15)

    def test_link_global_symlink_mode(self):
        """Verify symlink mode succeeds or safely falls back to copy on Windows."""
        stats = link_global(mode="symlink", dry_run=False, config_dir=self.config_dir)
        self.assertEqual(stats["skills_linked"], 28)
        self.assertEqual(stats["agents_linked"], 15)
        self.assertEqual(len(stats["errors"]), 0)


if __name__ == "__main__":
    unittest.main()
