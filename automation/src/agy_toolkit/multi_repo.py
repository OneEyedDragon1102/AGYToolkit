"""AGYToolkit Multi-Repository & Worktree Swarm Orchestrator.

Enables coordinating autonomous agent swarms across multiple repositories,
services, and git worktrees under a unified workspace manifest.
"""

import datetime
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.bus import publish_event


@dataclass
class WorkspaceMember:
    name: str
    path: str
    stack: str
    role: str
    resolved_path: Path
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "stack": self.stack,
            "role": self.role,
            "is_valid": self.is_valid,
            "resolved_path": str(self.resolved_path),
        }


@dataclass
class WorkspaceManifest:
    name: str
    version: str
    workspace_root: Path
    shared_bus: str
    members: List[WorkspaceMember] = field(default_factory=list)

    def get_member(self, name: str) -> Optional[WorkspaceMember]:
        for m in self.members:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "workspace_root": str(self.workspace_root),
            "shared_bus": self.shared_bus,
            "members": [m.to_dict() for m in self.members],
        }


@dataclass
class MultiRepoStep:
    step_id: str
    target_repo: str
    agent: str
    action: str
    status: str = "PENDING"
    depends_on: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiRepoRun:
    run_id: str
    manifest_name: str
    pipeline: str
    status: str
    steps: Dict[str, MultiRepoStep]
    context: Dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "manifest_name": self.manifest_name,
            "pipeline": self.pipeline,
            "status": self.status,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


MULTI_REPO_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "fullstack-feature": {
        "name": "fullstack-feature",
        "description": "Cross-repository feature implementation spanning backend, frontend, and tests.",
        "steps": [
            {
                "id": "be-api-spec",
                "target_repo": "backend",
                "agent": "planner-architect",
                "action": "Specify domain model and API contract",
                "depends_on": [],
            },
            {
                "id": "be-implementation",
                "target_repo": "backend",
                "agent": "spring-boot-engineer",
                "action": "Implement domain entity, use cases, and REST controller",
                "depends_on": ["be-api-spec"],
            },
            {
                "id": "fe-client-sync",
                "target_repo": "frontend",
                "agent": "node-ts-engineer",
                "action": "Implement frontend service client and UI components",
                "depends_on": ["be-implementation"],
            },
            {
                "id": "cross-test",
                "target_repo": "backend",
                "agent": "tdd-specialist",
                "action": "Execute integration verification across service boundaries",
                "depends_on": ["fe-client-sync"],
            },
            {
                "id": "multi-review",
                "target_repo": "frontend",
                "agent": "code-reviewer",
                "action": "Review multi-repository diffs and verify anti-bloat compliance",
                "depends_on": ["cross-test"],
            },
        ],
    },
    "cross-review": {
        "name": "cross-review",
        "description": "Concurrent multi-repository code review and security audit.",
        "steps": [
            {
                "id": "backend-review",
                "target_repo": "backend",
                "agent": "code-reviewer",
                "action": "Review backend changes",
                "depends_on": [],
            },
            {
                "id": "frontend-review",
                "target_repo": "frontend",
                "agent": "code-reviewer",
                "action": "Review frontend changes",
                "depends_on": [],
            },
            {
                "id": "security-audit",
                "target_repo": "backend",
                "agent": "security-auditor",
                "action": "Verify cross-boundary auth and input validation",
                "depends_on": ["backend-review", "frontend-review"],
            },
        ],
    },
}


def detect_repo_stack(repo_path: Path) -> str:
    """Detect tech stack of a repository directory."""
    if (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
        return "spring-boot"
    if (repo_path / "package.json").exists():
        return "node-ts"
    if (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists():
        return "python"
    return "generic"


def init_workspace_manifest(
    target_dir: Path, name: Optional[str] = None
) -> Path:
    """Auto-discover child repositories and write agy-workspace.json."""
    root = Path(target_dir).resolve()
    manifest_path = root / "agy-workspace.json"
    ws_name = name or root.name or "enterprise-workspace"

    members = []
    for item in sorted(root.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue

        is_repo = (
            (item / ".git").exists()
            or (item / ".agents").exists()
            or (item / "pom.xml").exists()
            or (item / "package.json").exists()
            or (item / "pyproject.toml").exists()
        )
        if is_repo:
            stack = detect_repo_stack(item)
            role = "backend" if "service" in item.name or stack == "spring-boot" else "frontend"
            rel_path = item.name
            members.append(
                {
                    "name": item.name,
                    "path": rel_path,
                    "stack": stack,
                    "role": role,
                }
            )

    # Fallback to current directory as sole member if no sub-repos found
    if not members:
        members.append(
            {
                "name": "core",
                "path": ".",
                "stack": detect_repo_stack(root),
                "role": "core-service",
            }
        )

    manifest_data = {
        "name": ws_name,
        "version": "1.0.0",
        "shared_bus": ".agents/memory/volatile-bus",
        "repositories": members,
    }

    manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def load_workspace_manifest(manifest_path_or_dir: Path) -> WorkspaceManifest:
    """Load and validate agy-workspace.json."""
    p = Path(manifest_path_or_dir).resolve()
    if p.is_dir():
        manifest_file = p / "agy-workspace.json"
    else:
        manifest_file = p

    if not manifest_file.exists():
        raise FileNotFoundError(f"Workspace manifest not found: {manifest_file}")

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    ws_root = manifest_file.parent

    members: List[WorkspaceMember] = []
    for r in data.get("repositories", []):
        rel_p = r.get("path", ".")
        resolved = (ws_root / rel_p).resolve()
        is_valid = resolved.exists() and resolved.is_dir()
        members.append(
            WorkspaceMember(
                name=r.get("name", resolved.name),
                path=rel_p,
                stack=r.get("stack", detect_repo_stack(resolved)),
                role=r.get("role", "service"),
                resolved_path=resolved,
                is_valid=is_valid,
            )
        )

    return WorkspaceManifest(
        name=data.get("name", ws_root.name),
        version=data.get("version", "1.0.0"),
        workspace_root=ws_root,
        shared_bus=data.get("shared_bus", ".agents/memory/volatile-bus"),
        members=members,
    )


def audit_workspace(manifest: WorkspaceManifest) -> Dict[str, Any]:
    """Audit member repositories in the workspace manifest."""
    results = []
    healthy_count = 0

    for m in manifest.members:
        has_agents = (m.resolved_path / ".agents").exists()
        has_gemini = (m.resolved_path / "GEMINI.md").exists()
        has_agents_rule = (m.resolved_path / "AGENTS.md").exists()
        is_healthy = m.is_valid and (has_agents or has_gemini)

        if is_healthy:
            healthy_count += 1

        results.append(
            {
                "name": m.name,
                "path": m.path,
                "stack": m.stack,
                "role": m.role,
                "is_valid": m.is_valid,
                "has_agents": has_agents,
                "has_rules": has_gemini and has_agents_rule,
                "status": "HEALTHY" if is_healthy else "NEEDS_INIT",
            }
        )

    return {
        "workspace_name": manifest.name,
        "total_repositories": len(manifest.members),
        "healthy_repositories": healthy_count,
        "overall_status": "PASS" if healthy_count == len(manifest.members) else "WARN",
        "repositories": results,
    }


def get_shared_bus_dir(manifest: WorkspaceManifest) -> Path:
    """Return resolved path to the shared volatile event bus."""
    bus_dir = manifest.workspace_root / manifest.shared_bus
    bus_dir.mkdir(parents=True, exist_ok=True)
    return bus_dir


def broadcast_workspace_event(
    manifest: WorkspaceManifest,
    topic: str,
    sender: str,
    payload: Dict[str, Any],
) -> str:
    """Publish a cross-repository event onto the shared volatile bus."""
    bus_dir = get_shared_bus_dir(manifest)
    evt = publish_event(
        topic=topic,
        sender=sender,
        payload=payload,
        memory_dir=bus_dir.parent,
    )
    return evt.id


def _get_multi_runs_dir(manifest: WorkspaceManifest) -> Path:
    runs_dir = get_shared_bus_dir(manifest) / "multi-runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir


def launch_multi_run(
    manifest: WorkspaceManifest,
    blueprint_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> MultiRepoRun:
    """Launch a cross-repository swarm pipeline run."""
    bp = MULTI_REPO_BLUEPRINTS.get(blueprint_name)
    if not bp:
        raise ValueError(
            f"Unknown blueprint: '{blueprint_name}'. Available: {list(MULTI_REPO_BLUEPRINTS.keys())}"
        )

    run_id = f"mrun-{uuid.uuid4().hex[:8]}"
    now_str = datetime.datetime.now().isoformat()

    # Map member repos by role or name
    role_map: Dict[str, str] = {}
    for m in manifest.members:
        role_map[m.role.lower()] = m.name
        role_map[m.name.lower()] = m.name

    steps: Dict[str, MultiRepoStep] = {}
    for s in bp["steps"]:
        target_role = s["target_repo"].lower()
        # Resolve target repo name or default to first member
        target_name = role_map.get(target_role, manifest.members[0].name)
        initial_status = "DISPATCHED" if not s["depends_on"] else "PENDING"
        steps[s["id"]] = MultiRepoStep(
            step_id=s["id"],
            target_repo=target_name,
            agent=s["agent"],
            action=s["action"],
            status=initial_status,
            depends_on=s["depends_on"],
        )

    run = MultiRepoRun(
        run_id=run_id,
        manifest_name=manifest.name,
        pipeline=blueprint_name,
        status="RUNNING",
        steps=steps,
        context=context or {},
        created_at=now_str,
        updated_at=now_str,
    )

    save_multi_run(manifest, run)
    return run


def save_multi_run(manifest: WorkspaceManifest, run: MultiRepoRun) -> Path:
    """Persist MultiRepoRun state to disk."""
    run.updated_at = datetime.datetime.now().isoformat()
    runs_dir = _get_multi_runs_dir(manifest)
    run_file = runs_dir / f"{run.run_id}.json"
    run_file.write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")
    return run_file


def get_multi_run(manifest: WorkspaceManifest, run_id: str) -> Optional[MultiRepoRun]:
    """Retrieve MultiRepoRun by id."""
    runs_dir = _get_multi_runs_dir(manifest)
    run_file = runs_dir / f"{run_id}.json"
    if not run_file.exists():
        return None

    data = json.loads(run_file.read_text(encoding="utf-8"))
    steps = {
        k: MultiRepoStep(**v) for k, v in data.get("steps", {}).items()
    }
    return MultiRepoRun(
        run_id=data["run_id"],
        manifest_name=data["manifest_name"],
        pipeline=data["pipeline"],
        status=data["status"],
        steps=steps,
        context=data.get("context", {}),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def advance_multi_step(
    manifest: WorkspaceManifest,
    run_id: str,
    step_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> MultiRepoRun:
    """Advance status of a multi-repo step and resolve downstream dependencies."""
    run = get_multi_run(manifest, run_id)
    if not run:
        raise ValueError(f"Multi-repo run '{run_id}' not found.")

    step = run.steps.get(step_id)
    if not step:
        raise ValueError(f"Step '{step_id}' not found in run '{run_id}'.")

    step.status = status.upper()
    step.result = result
    step.error = error

    if step.status == "FAILED":
        run.status = "FAILED"
        for other in run.steps.values():
            if other.status in ("PENDING", "DISPATCHED"):
                other.status = "SKIPPED"
    elif step.status == "COMPLETED":
        # Check downstream dependencies
        for other in run.steps.values():
            if other.status == "PENDING" and step_id in other.depends_on:
                all_met = all(
                    run.steps[dep].status == "COMPLETED" for dep in other.depends_on
                )
                if all_met:
                    other.status = "DISPATCHED"

        # Check if all steps completed
        all_completed = all(s.status == "COMPLETED" for s in run.steps.values())
        if all_completed:
            run.status = "COMPLETED"

    save_multi_run(manifest, run)
    return run


def format_multi_status_card(run: MultiRepoRun, manifest: WorkspaceManifest) -> str:
    """Render a terminal card showing cross-repository execution topology."""
    lines = [
        "=" * 70,
        f" [AGYToolkit Multi-Repo Swarm] Run: `{run.run_id}` | Status: [{run.status}]",
        f" Workspace: {manifest.name} | Pipeline: {run.pipeline}",
        "=" * 70,
        f"{'Step ID':<18} | {'Repository':<15} | {'Agent':<20} | {'Status':<10}",
        "-" * 70,
    ]
    for step in run.steps.values():
        lines.append(
            f"{step.step_id:<18} | {step.target_repo:<15} | {step.agent:<20} | {step.status:<10}"
        )
    lines.append("=" * 70)
    return "\n".join(lines)
