"""AGYToolkit Project Scaffolder - Provisions downstream workspaces with AGY governance."""

import datetime
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.scaffolder_stacks import scaffold_stack_template

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"


def scaffold_project(
    target_path: Path,
    project_name: str,
    stack: str = "node-ts",
    mode: str = "feature",
    templates_dir: Optional[Path] = None,
    template: Optional[str] = None,
) -> Dict[str, Any]:
    """Scaffold AGYToolkit governance and optionally stack code into a downstream directory."""
    tmpl_dir = templates_dir or TEMPLATES_DIR
    target_dir = Path(target_path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.date.today().isoformat()

    # 1. Copy .agents directory (hooks, agents, skills, memory structure)
    src_agents = tmpl_dir / ".agents"
    dst_agents = target_dir / ".agents"
    if dst_agents.exists():
        shutil.rmtree(dst_agents)
    shutil.copytree(src_agents, dst_agents)

    # 2. Render active-session.md from template
    active_tmpl = dst_agents / "memory" / "active-session.template.md"
    if active_tmpl.exists():
        content = active_tmpl.read_text(encoding="utf-8")
        content = content.replace("{{GOAL}}", f"Initialize {project_name}")
        content = content.replace("{{BRANCH}}", "main")
        content = content.replace("{{MODE}}", mode.upper())
        (dst_agents / "memory" / "active-session.md").write_text(content, encoding="utf-8")
        active_tmpl.unlink()

    # 3. Render decisions.md from template
    decisions_tmpl = dst_agents / "memory" / "decisions.template.md"
    if decisions_tmpl.exists():
        content = decisions_tmpl.read_text(encoding="utf-8")
        content = content.replace("{{DATE}}", today_str)
        (dst_agents / "memory" / "decisions.md").write_text(content, encoding="utf-8")
        decisions_tmpl.unlink()

    # 4. Render GEMINI.md
    gemini_tmpl = tmpl_dir / "rules" / "GEMINI.md.template"
    if gemini_tmpl.exists():
        content = gemini_tmpl.read_text(encoding="utf-8")
        content = content.replace("{{PROJECT_NAME}}", project_name)
        content = content.replace("{{STACK}}", stack)
        (target_dir / "GEMINI.md").write_text(content, encoding="utf-8")

    # 5. Render AGENTS.md
    agents_tmpl = tmpl_dir / "rules" / "AGENTS.md.template"
    if agents_tmpl.exists():
        content = agents_tmpl.read_text(encoding="utf-8")
        content = content.replace("{{PROJECT_NAME}}", project_name)
        (target_dir / "AGENTS.md").write_text(content, encoding="utf-8")

    # 6. Ensure .gitignore excludes active-session.md and volatile-bus
    gitignore_path = target_dir / ".gitignore"
    existing_ignore = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    ignore_entries = [
        "\n# AGYToolkit Local Session Memory (Gitignored)",
        ".agents/memory/active-session.md",
        ".agents/memory/volatile-bus/*",
        "!.agents/memory/volatile-bus/.gitignore",
    ]
    to_append = []
    for entry in ignore_entries:
        if entry.strip() and entry.strip() not in existing_ignore:
            to_append.append(entry)

    if to_append:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(to_append) + "\n")

    # 7. Optionally scaffold tech stack template boilerplate
    template_files: List[str] = []
    if template:
        stacks_dir = tmpl_dir / "stacks"
        created = scaffold_stack_template(
            target_dir=target_dir,
            project_name=project_name,
            template_name=template,
            stacks_dir=stacks_dir,
        )
        template_files = [str(p) for p in created]

    return {
        "target_dir": str(target_dir),
        "project_name": project_name,
        "stack": stack,
        "mode": mode,
        "template": template,
        "template_files_count": len(template_files),
        "agents_installed": len(list((dst_agents / "agents").glob("*.md"))),
        "hooks_installed": len(list((dst_agents / "hooks").glob("*.*"))),
        "skills_installed": len(list((dst_agents / "skills").glob("*/SKILL.md"))),
        "memory_initialized": (dst_agents / "memory" / "active-session.md").exists(),
    }
