"""AGYToolkit Doctor - Diagnostic health and governance audit engine."""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CheckResult:
    category: str
    name: str
    status: str  # PASS, WARN, FAIL
    details: str
    remediation: Optional[str] = None


@dataclass
class DoctorReport:
    target_dir: str
    results: List[CheckResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == "WARN")

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def is_healthy(self) -> bool:
        return self.failure_count == 0

    def to_dict(self) -> Dict:
        return {
            "target_dir": self.target_dir,
            "passed": self.passed_count,
            "warnings": self.warning_count,
            "failures": self.failure_count,
            "is_healthy": self.is_healthy,
            "checks": [
                {
                    "category": r.category,
                    "name": r.name,
                    "status": r.status,
                    "details": r.details,
                    "remediation": r.remediation,
                }
                for r in self.results
            ],
        }


def _run_cmd(args: List[str]) -> Optional[str]:
    """Execute a command and return stdout/stderr if successful."""
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        out = (proc.stdout + " " + proc.stderr).strip()
        return out if proc.returncode == 0 else None
    except Exception:
        return None


def audit_toolchain() -> List[CheckResult]:
    """Audit local host developer tools and runtimes."""
    results = []

    # 1. Python check
    py_ver = sys.version.split()[0]
    in_venv = sys.prefix != sys.base_prefix
    if sys.version_info >= (3, 10):
        venv_str = " (active venv)" if in_venv else " (global env)"
        results.append(
            CheckResult(
                category="Toolchain",
                name="Python Runtime",
                status="PASS",
                details=f"Python {py_ver}{venv_str}",
            )
        )
    else:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Python Runtime",
                status="FAIL",
                details=f"Python {py_ver} is below required >= 3.10",
                remediation="Install Python 3.12 or 3.10+.",
            )
        )

    # 2. Node.js check
    node_out = _run_cmd(["node", "-v"])
    if node_out:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Node.js",
                status="PASS",
                details=node_out,
            )
        )
    else:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Node.js",
                status="WARN",
                details="Node.js not detected in PATH",
                remediation="Install Node.js 20+ for TypeScript & MCP sidecars.",
            )
        )

    # 3. Java check
    java_out = _run_cmd(["java", "-version"])
    if java_out:
        first_line = java_out.splitlines()[0] if java_out else "Installed"
        results.append(
            CheckResult(
                category="Toolchain",
                name="Java Development Kit",
                status="PASS",
                details=first_line,
            )
        )
    else:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Java Development Kit",
                status="WARN",
                details="Java runtime not detected in PATH",
                remediation="Install JDK 21 or 23 for Spring Boot microservices.",
            )
        )

    # 4. Maven check
    mvn_out = _run_cmd(["mvn", "-v"])
    if mvn_out:
        first_line = mvn_out.splitlines()[0] if mvn_out else "Installed"
        results.append(
            CheckResult(
                category="Toolchain",
                name="Apache Maven",
                status="PASS",
                details=first_line,
            )
        )
    else:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Apache Maven",
                status="WARN",
                details="Maven not detected in PATH",
                remediation="Install Maven 3.9+ for Java builds.",
            )
        )

    # 5. Git check
    git_out = _run_cmd(["git", "--version"])
    if git_out:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Git Version Control",
                status="PASS",
                details=git_out,
            )
        )
    else:
        results.append(
            CheckResult(
                category="Toolchain",
                name="Git Version Control",
                status="FAIL",
                details="Git not detected in PATH",
                remediation="Install Git 2.40+.",
            )
        )

    return results


def audit_governance(target_path: Path) -> List[CheckResult]:
    """Audit AGYToolkit governance integrity inside target project directory."""
    results = []
    target = Path(target_path).resolve()

    if not target.exists():
        return [
            CheckResult(
                category="Workspace",
                name="Directory Exists",
                status="FAIL",
                details=f"Target path does not exist: {target}",
                remediation="Provide a valid directory path.",
            )
        ]

    # 1. Check rules
    gemini_file = target / "GEMINI.md"
    if gemini_file.exists():
        results.append(
            CheckResult(
                category="Governance",
                name="Project Rules (GEMINI.md)",
                status="PASS",
                details=f"Found ({gemini_file.stat().st_size} bytes)",
            )
        )
    else:
        results.append(
            CheckResult(
                category="Governance",
                name="Project Rules (GEMINI.md)",
                status="WARN",
                details="Missing GEMINI.md in workspace root",
                remediation="Run 'agy-toolkit init' to scaffold rules.",
            )
        )

    agents_file = target / "AGENTS.md"
    if agents_file.exists():
        results.append(
            CheckResult(
                category="Governance",
                name="Agent Instructions (AGENTS.md)",
                status="PASS",
                details=f"Found ({agents_file.stat().st_size} bytes)",
            )
        )
    else:
        results.append(
            CheckResult(
                category="Governance",
                name="Agent Instructions (AGENTS.md)",
                status="WARN",
                details="Missing AGENTS.md in workspace root",
                remediation="Run 'agy-toolkit init' to scaffold agent rules.",
            )
        )

    # 2. Check hooks.json
    hooks_json = target / ".agents" / "hooks.json"
    if hooks_json.exists():
        try:
            with open(hooks_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = list(data.get("hooks", {}).keys())
            results.append(
                CheckResult(
                    category="Governance",
                    name="Lifecycle Hooks Config (hooks.json)",
                    status="PASS",
                    details=f"Valid JSON with events: {', '.join(events)}",
                )
            )
        except Exception as e:
            results.append(
                CheckResult(
                    category="Governance",
                    name="Lifecycle Hooks Config (hooks.json)",
                    status="FAIL",
                    details=f"Invalid JSON: {e}",
                    remediation="Re-scaffold or fix .agents/hooks.json.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Governance",
                name="Lifecycle Hooks Config (hooks.json)",
                status="WARN",
                details="Missing .agents/hooks.json",
                remediation="Run 'agy-toolkit init' to configure lifecycle hooks.",
            )
        )

    # 3. Check hook scripts
    hooks_dir = target / ".agents" / "hooks"
    expected_hooks = [
        "anti-bloat-check.ps1",
        "enforce-branch-rule.ps1",
        "plan-approval-gate.ps1",
        "flush-active-memory.ps1",
    ]
    if hooks_dir.exists():
        found_hooks = [h for h in expected_hooks if (hooks_dir / h).exists()]
        if len(found_hooks) == len(expected_hooks):
            results.append(
                CheckResult(
                    category="Governance",
                    name="Lifecycle Hook Scripts",
                    status="PASS",
                    details=f"All {len(expected_hooks)} core scripts present",
                )
            )
        else:
            missing = set(expected_hooks) - set(found_hooks)
            results.append(
                CheckResult(
                    category="Governance",
                    name="Lifecycle Hook Scripts",
                    status="FAIL",
                    details=f"Missing scripts: {', '.join(missing)}",
                    remediation="Re-run 'agy-toolkit init' to restore hook scripts.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Governance",
                name="Lifecycle Hook Scripts",
                status="WARN",
                details="Directory .agents/hooks/ missing",
                remediation="Run 'agy-toolkit init' to scaffold hook scripts.",
            )
        )

    # 4. Check specialist agents
    agents_dir = target / ".agents" / "agents"
    if agents_dir.exists():
        agent_count = len(list(agents_dir.glob("*.md")))
        if agent_count >= 15:
            results.append(
                CheckResult(
                    category="Agents",
                    name="Specialist Agents Matrix",
                    status="PASS",
                    details=f"{agent_count} specialist agents registered in .agents/agents/",
                )
            )
        else:
            results.append(
                CheckResult(
                    category="Agents",
                    name="Specialist Agents Matrix",
                    status="WARN",
                    details=f"Only {agent_count}/15 specialist agents found",
                    remediation="Run 'agy-toolkit init' to install complete agent matrix.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Agents",
                name="Specialist Agents Matrix",
                status="WARN",
                details="Directory .agents/agents/ missing",
                remediation="Run 'agy-toolkit init' to scaffold specialist agents.",
            )
        )

    # 5. Check progressive skills
    skills_dir = target / ".agents" / "skills"
    if skills_dir.exists():
        skill_count = len(list(skills_dir.glob("*/SKILL.md")))
        if skill_count >= 28:
            results.append(
                CheckResult(
                    category="Skills",
                    name="Progressive Skills Catalog",
                    status="PASS",
                    details=f"{skill_count} progressive skills installed in .agents/skills/",
                )
            )
        else:
            results.append(
                CheckResult(
                    category="Skills",
                    name="Progressive Skills Catalog",
                    status="WARN",
                    details=f"Found {skill_count}/28 progressive skills",
                    remediation="Run 'agy-toolkit init' to install all 28 skills.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Skills",
                name="Progressive Skills Catalog",
                status="WARN",
                details="Directory .agents/skills/ missing",
                remediation="Run 'agy-toolkit init' to scaffold progressive skills.",
            )
        )

    # 6. Check memory system & budgets
    active_sess = target / ".agents" / "memory" / "active-session.md"
    if active_sess.exists():
        size = active_sess.stat().st_size
        if size <= 1024:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Active Session Budget",
                    status="PASS",
                    details=f"{size} bytes (within 1024 byte budget)",
                )
            )
        else:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Active Session Budget",
                    status="FAIL",
                    details=f"{size} bytes exceeds 1024 byte limit by {size - 1024} bytes",
                    remediation="Trim active-session.md or trigger memory flush.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Memory",
                name="Active Session Budget",
                status="WARN",
                details="Missing .agents/memory/active-session.md",
                remediation="Run 'agy-toolkit init' to initialize session memory.",
            )
        )

    decisions = target / ".agents" / "memory" / "decisions.md"
    if decisions.exists():
        size = decisions.stat().st_size
        if size <= 3072:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Decisions Log Budget",
                    status="PASS",
                    details=f"{size} bytes (within 3072 byte budget)",
                )
            )
        else:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Decisions Log Budget",
                    status="FAIL",
                    details=f"{size} bytes exceeds 3072 byte limit by {size - 3072} bytes",
                    remediation="Offload older decisions to docs/adr/ and summarize decisions.md.",
                )
            )
    else:
        results.append(
            CheckResult(
                category="Memory",
                name="Decisions Log Budget",
                status="WARN",
                details="Missing .agents/memory/decisions.md",
                remediation="Run 'agy-toolkit init' to initialize decisions register.",
            )
        )

    # 7. Check gitignore exclusions
    gitignore = target / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        has_sess = ".agents/memory/active-session.md" in content
        has_bus = ".agents/memory/volatile-bus/*" in content
        if has_sess and has_bus:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Gitignore Memory Exclusions",
                    status="PASS",
                    details="active-session.md and volatile-bus/ are gitignored",
                )
            )
        else:
            results.append(
                CheckResult(
                    category="Memory",
                    name="Gitignore Memory Exclusions",
                    status="FAIL",
                    details="Memory files are not excluded in .gitignore",
                    remediation="Add .agents/memory/active-session.md and .agents/memory/volatile-bus/* to .gitignore.",
                )
            )

    return results


def run_doctor(target_path: Optional[Path] = None) -> DoctorReport:
    """Run full diagnostic audit of toolchain and target workspace governance."""
    target = Path(target_path or ".").resolve()
    report = DoctorReport(target_dir=str(target))

    # Toolchain checks
    report.results.extend(audit_toolchain())

    # Governance checks
    report.results.extend(audit_governance(target))

    return report


def print_doctor_report(report: DoctorReport):
    """Render doctor audit findings to stdout."""
    print("=" * 75)
    print(" [AGYToolkit Doctor] Diagnostic Environment & Governance Report")
    print(f" Target Workspace: {report.target_dir}")
    print("=" * 75)

    current_cat = None
    for r in report.results:
        if r.category != current_cat:
            current_cat = r.category
            print(f"\n[{current_cat}]")

        status_tag = f"[{r.status}]"
        print(f"  {status_tag:<8} {r.name:<34} : {r.details}")
        if r.remediation:
            print(f"           Remediation: {r.remediation}")

    print("\n" + "=" * 75)
    print(
        f" Audit Summary: {report.passed_count} Passed | "
        f"{report.warning_count} Warnings | "
        f"{report.failure_count} Failures"
    )
    if report.is_healthy:
        print(" Status: HEALTHY - Workspace is ready for governed autonomous operations.")
    else:
        print(" Status: ATTENTION REQUIRED - Resolve failure items above before starting tasks.")
    print("=" * 75)
