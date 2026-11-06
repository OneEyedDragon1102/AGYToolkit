"""AGYToolkit Project Updater - Synchronizes downstream workspaces with latest framework assets."""

from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"


@dataclass
class UpdateReport:
    """Structured report produced by the project update engine."""

    target_path: str
    success: bool
    skills_updated: int = 0
    agents_updated: int = 0
    hooks_updated: int = 0
    rules_preserved: bool = True
    memory_preserved: bool = True
    dry_run: bool = False
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "target_path": self.target_path,
            "success": self.success,
            "skills_updated": self.skills_updated,
            "agents_updated": self.agents_updated,
            "hooks_updated": self.hooks_updated,
            "rules_preserved": self.rules_preserved,
            "memory_preserved": self.memory_preserved,
            "dry_run": self.dry_run,
            "errors": self.errors,
        }


def update_project(
    target_path: Path,
    dry_run: bool = False,
    force_rules: bool = False,
    templates_dir: Optional[Path] = None,
) -> UpdateReport:
    """Non-destructively update an existing downstream AGYToolkit installation."""
    target_dir = Path(target_path).resolve()
    tmpl_dir = templates_dir or TEMPLATES_DIR

    report = UpdateReport(
        target_path=str(target_dir),
        success=False,
        dry_run=dry_run,
    )

    # 1. Validation
    if not target_dir.exists() or not target_dir.is_dir():
        report.errors.append(f"Target path does not exist or is not a directory: {target_dir}")
        return report

    agents_dir = target_dir / ".agents"
    gemini_file = target_dir / "GEMINI.md"
    if not agents_dir.exists() and not gemini_file.exists():
        report.errors.append(
            f"Target directory is not initialized with AGYToolkit: {target_dir}. "
            "Run 'agy-toolkit init' first."
        )
        return report

    # 2. Sync Skills
    src_skills = tmpl_dir / ".agents" / "skills"
    dst_skills = agents_dir / "skills"
    if src_skills.exists():
        if not dry_run:
            dst_skills.mkdir(parents=True, exist_ok=True)
        for skill_dir in sorted(src_skills.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not dry_run:
                target_skill = dst_skills / skill_dir.name
                if target_skill.exists():
                    shutil.rmtree(target_skill)
                shutil.copytree(skill_dir, target_skill)
            report.skills_updated += 1

    # 3. Sync Specialist Agents
    src_agents = tmpl_dir / ".agents" / "agents"
    dst_agents = agents_dir / "agents"
    if src_agents.exists():
        if not dry_run:
            dst_agents.mkdir(parents=True, exist_ok=True)
        for agent_file in sorted(src_agents.iterdir()):
            if not agent_file.is_file() or not agent_file.name.endswith(".md"):
                continue
            if not dry_run:
                shutil.copy2(agent_file, dst_agents / agent_file.name)
            report.agents_updated += 1

    # 4. Sync Hooks
    src_hooks_json = tmpl_dir / ".agents" / "hooks.json"
    if src_hooks_json.exists() and not dry_run:
        shutil.copy2(src_hooks_json, agents_dir / "hooks.json")

    src_hooks = tmpl_dir / ".agents" / "hooks"
    dst_hooks = agents_dir / "hooks"
    if src_hooks.exists():
        if not dry_run:
            dst_hooks.mkdir(parents=True, exist_ok=True)
        for hook_file in sorted(src_hooks.iterdir()):
            if not hook_file.is_file():
                continue
            if not dry_run:
                shutil.copy2(hook_file, dst_hooks / hook_file.name)
            report.hooks_updated += 1

    # 5. Strict Memory Pass-Through
    # Memory files (.agents/memory/active-session.md, decisions.md, volatile-bus)
    # are completely untouched to avoid overwriting ongoing context.
    report.memory_preserved = True

    # 6. Rules Handling
    if force_rules:
        project_name = target_dir.name
        gemini_tmpl = tmpl_dir / "rules" / "GEMINI.md.template"
        if gemini_tmpl.exists() and not dry_run:
            content = gemini_tmpl.read_text(encoding="utf-8")
            content = content.replace("{{PROJECT_NAME}}", project_name)
            content = content.replace("{{STACK}}", "generic")
            (target_dir / "GEMINI.md").write_text(content, encoding="utf-8")

        agents_tmpl = tmpl_dir / "rules" / "AGENTS.md.template"
        if agents_tmpl.exists() and not dry_run:
            content = agents_tmpl.read_text(encoding="utf-8")
            content = content.replace("{{PROJECT_NAME}}", project_name)
            (target_dir / "AGENTS.md").write_text(content, encoding="utf-8")

        report.rules_preserved = False
    else:
        report.rules_preserved = True

    # 7. Gitignore Hygiene
    gitignore_path = target_dir / ".gitignore"
    if gitignore_path.exists():
        existing_ignore = gitignore_path.read_text(encoding="utf-8")
        ignore_entries = [
            ".agents/memory/active-session.md",
            ".agents/memory/volatile-bus/*",
            "!.agents/memory/volatile-bus/.gitignore",
        ]
        to_append = []
        for entry in ignore_entries:
            if entry not in existing_ignore:
                to_append.append(entry)

        if to_append and not dry_run:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# AGYToolkit Local Session Memory (Gitignored)\n")
                for entry in to_append:
                    f.write(f"{entry}\n")

    report.success = True
    return report


def format_update_report(report: UpdateReport) -> str:
    """Format UpdateReport as human-readable text."""
    mode_str = " [DRY RUN]" if report.dry_run else ""
    lines = [
        "=" * 70,
        f" [AGYToolkit Project Update]{mode_str}",
        f" Target: {report.target_path}",
        "=" * 70,
        "",
    ]

    if not report.success:
        lines.append(" Status: FAILED")
        for err in report.errors:
            lines.append(f"   [ERROR] {err}")
        lines.append("=" * 70)
        return "\n".join(lines)

    lines.extend([
        f" Skills Refreshed   : {report.skills_updated} SDLC skills",
        f" Agents Refreshed   : {report.agents_updated} specialist subagents",
        f" Hooks Refreshed    : {report.hooks_updated} lifecycle scripts",
        f" Project Rules      : {'Preserved (kept custom)' if report.rules_preserved else 'Refreshed from template'}",
        f" Session Memory     : Preserved (zero context loss)",
        "",
        "=" * 70,
        " Update Summary: Successfully synchronized downstream repository.",
        "=" * 70,
    ])
    return "\n".join(lines)
