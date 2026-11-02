"""AGYToolkit Global Linker - Mounts skills and agents into ~/.gemini/config/ for machine-wide AGY discovery."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
TEMPLATES_SKILLS = TEMPLATES_DIR / ".agents" / "skills"
TEMPLATES_AGENTS = TEMPLATES_DIR / ".agents" / "agents"


def get_global_config_dir() -> Path:
    """Resolve global Antigravity configuration directory."""
    return Path.home() / ".gemini" / "config"


def link_global(
    mode: str = "copy",
    dry_run: bool = False,
    config_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Mount the 28 SDLC skills and 15 specialist agents into the global AGY configuration directory."""
    base_dir = config_dir or get_global_config_dir()
    skills_dest = base_dir / "skills"
    agents_dest = base_dir / "agents"

    stats = {
        "config_dir": str(base_dir),
        "mode": mode,
        "dry_run": dry_run,
        "skills_linked": 0,
        "agents_linked": 0,
        "errors": [],
    }

    if not dry_run:
        skills_dest.mkdir(parents=True, exist_ok=True)
        agents_dest.mkdir(parents=True, exist_ok=True)

    # 1. Mount Skills
    if TEMPLATES_SKILLS.exists():
        for skill_path in sorted(TEMPLATES_SKILLS.iterdir()):
            if not skill_path.is_dir():
                continue
            skill_name = skill_path.name
            target_skill_dir = skills_dest / skill_name

            if dry_run:
                stats["skills_linked"] += 1
                continue

            try:
                if mode == "symlink":
                    try:
                        if target_skill_dir.exists() or target_skill_dir.is_symlink():
                            if target_skill_dir.is_symlink() or target_skill_dir.is_file():
                                target_skill_dir.unlink()
                            else:
                                shutil.rmtree(target_skill_dir)
                        os.symlink(skill_path, target_skill_dir, target_is_directory=True)
                    except (OSError, NotImplementedError):
                        # Fallback to copy if symlink privileges are unavailable (common on Windows)
                        if target_skill_dir.exists():
                            shutil.rmtree(target_skill_dir)
                        shutil.copytree(skill_path, target_skill_dir)
                else:
                    if target_skill_dir.exists():
                        shutil.rmtree(target_skill_dir)
                    shutil.copytree(skill_path, target_skill_dir)
                stats["skills_linked"] += 1
            except Exception as e:
                stats["errors"].append(f"Failed to link skill {skill_name}: {e}")

    # 2. Mount Agents
    if TEMPLATES_AGENTS.exists():
        for agent_file in sorted(TEMPLATES_AGENTS.glob("*.md")):
            target_file = agents_dest / agent_file.name

            if dry_run:
                stats["agents_linked"] += 1
                continue

            try:
                if mode == "symlink":
                    try:
                        if target_file.exists() or target_file.is_symlink():
                            target_file.unlink()
                        os.symlink(agent_file, target_file)
                    except (OSError, NotImplementedError):
                        shutil.copy2(agent_file, target_file)
                else:
                    shutil.copy2(agent_file, target_file)
                stats["agents_linked"] += 1
            except Exception as e:
                stats["errors"].append(f"Failed to link agent {agent_file.name}: {e}")

    return stats
