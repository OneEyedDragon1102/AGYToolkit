"""AGYToolkit Swarm Choreographer - Finite State Machine & Multi-Agent Pipeline Engine.

Coordinates multi-step workflows across the 15 Universal Specialist Subagents
over the volatile IPC event bus with declarative DAG pipelines and automated context handoffs.
"""

import datetime
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.bus import publish_event
from agy_toolkit.memory import ensure_memory_dirs


@dataclass
class PipelineStep:
    """Declarative definition of a single step within a choreography pipeline."""
    name: str
    role: str
    topic: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 600


@dataclass
class StepState:
    """Runtime execution state of a pipeline step."""
    name: str
    role: str
    topic: str
    status: str = "PENDING"  # PENDING, DISPATCHED, CLAIMED, COMPLETED, FAILED, SKIPPED
    event_id: Optional[str] = None
    claimer: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    dispatched_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepState":
        """Reconstruct step state from dictionary."""
        return cls(**data)


@dataclass
class PipelineRun:
    """Complete runtime state of an executing or finished multi-agent choreography pipeline."""
    run_id: str
    pipeline_name: str
    status: str  # RUNNING, COMPLETED, FAILED, CANCELLED
    created_at: str
    updated_at: str
    context: Dict[str, Any]
    steps: Dict[str, StepState]

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline run to dictionary."""
        return {
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "context": self.context,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineRun":
        """Reconstruct pipeline run from dictionary."""
        steps = {k: StepState.from_dict(v) for k, v in data.get("steps", {}).items()}
        return cls(
            run_id=data["run_id"],
            pipeline_name=data["pipeline_name"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            context=data.get("context", {}),
            steps=steps,
        )


STANDARD_PIPELINES: Dict[str, Dict[str, Any]] = {
    "feature-sdlc": {
        "description": "Full-lifecycle autonomous SDLC pipeline from architectural planning to git staging.",
        "steps": [
            PipelineStep(
                name="plan",
                role="planner-architect",
                topic="swarm:plan",
                description="Draft implementation specification, task decomposition, and ADRs.",
            ),
            PipelineStep(
                name="tdd",
                role="tdd-specialist",
                topic="swarm:tdd",
                description="Write comprehensive red-green-refactor unit and boundary test suite.",
                depends_on=["plan"],
            ),
            PipelineStep(
                name="implement",
                role="stack-engineer",
                topic="swarm:code",
                description="Implement minimal, clean source code satisfying all tests.",
                depends_on=["tdd"],
            ),
            PipelineStep(
                name="review",
                role="code-reviewer",
                topic="swarm:review",
                description="Rigorous code review auditing security, anti-bloat, and architectural cohesion.",
                depends_on=["implement"],
            ),
            PipelineStep(
                name="stage",
                role="git-craftsman",
                topic="swarm:stage",
                description="Verify clean git diff and prepare atomic Conventional Commit.",
                depends_on=["review"],
            ),
        ],
    },
    "code-review": {
        "description": "Autonomous multi-agent review audit checking security, quality, and anti-bloat.",
        "steps": [
            PipelineStep(
                name="security-audit",
                role="security-auditor",
                topic="swarm:security",
                description="Audit diff for credentials leaks, OWASP vulnerabilities, and permission escapes.",
            ),
            PipelineStep(
                name="quality-review",
                role="code-reviewer",
                topic="swarm:review",
                description="Review diff for cohesion, performance bottlenecks, and race conditions.",
            ),
            PipelineStep(
                name="anti-bloat-check",
                role="anti-bloat-sentinel",
                topic="swarm:anti-bloat",
                description="Enforce zero emojis in code, <600 lines per file, and zero conversational comments.",
            ),
        ],
    },
    "quickfix": {
        "description": "Accelerated TDD fix and verification pipeline for defects and hotfixes.",
        "steps": [
            PipelineStep(
                name="reproduce-test",
                role="tdd-specialist",
                topic="swarm:tdd",
                description="Write reproduction test asserting the bug or edge case.",
            ),
            PipelineStep(
                name="patch",
                role="stack-engineer",
                topic="swarm:code",
                description="Apply minimal targeted fix to make reproduction test pass.",
                depends_on=["reproduce-test"],
            ),
            PipelineStep(
                name="verify-review",
                role="code-reviewer",
                topic="swarm:review",
                description="Verify fix meets quality standards and introduces no regressions.",
                depends_on=["patch"],
            ),
        ],
    },
}


def resolve_role_for_stack(generic_role: str, stack: Optional[str]) -> str:
    """Map generic role (e.g. stack-engineer) to exact specialized subagent."""
    if generic_role != "stack-engineer" or not stack:
        return generic_role

    normalized = stack.lower().strip()
    if "spring" in normalized or "java" in normalized:
        return "spring-boot-engineer"
    elif "node" in normalized or "ts" in normalized or "typescript" in normalized:
        return "node-ts-engineer"
    elif "python" in normalized or "py" in normalized:
        return "python-automation-lead"
    return generic_role


def get_pipeline_definition(name: str) -> Optional[Dict[str, Any]]:
    """Retrieve blueprint configuration for a named standard pipeline."""
    return STANDARD_PIPELINES.get(name)


def list_available_pipelines() -> List[Dict[str, Any]]:
    """Enumerate all built-in pipeline templates and their step topologies."""
    result = []
    for name, data in STANDARD_PIPELINES.items():
        steps_info = [
            {
                "name": s.name,
                "role": s.role,
                "topic": s.topic,
                "depends_on": s.depends_on,
            }
            for s in data["steps"]
        ]
        result.append({
            "name": name,
            "description": data["description"],
            "steps_count": len(data["steps"]),
            "steps": steps_info,
        })
    return result


def _get_runs_dir(memory_dir: Optional[Path] = None, create: bool = False) -> Path:
    """Resolve and ensure volatile-bus/runs directory."""
    base_dir = ensure_memory_dirs(memory_dir)
    runs_dir = base_dir / "volatile-bus" / "runs"
    if create:
        try:
            runs_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return runs_dir


def _save_pipeline_run(run: PipelineRun, memory_dir: Optional[Path] = None) -> Path:
    """Persist pipeline run state to JSON file with atomic write semantics."""
    runs_dir = _get_runs_dir(memory_dir, create=True)

    target_file = runs_dir / f"{run.run_id}.json"
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(runs_dir), prefix="run_", suffix=".tmp")
    with open(tmp_fd, "w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, indent=2)
    os.replace(tmp_path, str(target_file))
    return target_file


def load_pipeline_run(run_id: str, memory_dir: Optional[Path] = None) -> Optional[PipelineRun]:
    """Load an existing pipeline run by its unique identifier."""
    runs_dir = _get_runs_dir(memory_dir, create=False)
    if not runs_dir.exists():
        return None

    target_file = runs_dir / f"{run_id}.json"
    if not target_file.exists():
        return None

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PipelineRun.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def list_pipeline_runs(memory_dir: Optional[Path] = None) -> List[PipelineRun]:
    """Retrieve all pipeline runs recorded in the runs directory."""
    runs_dir = _get_runs_dir(memory_dir, create=False)
    if not runs_dir.exists():
        return []

    runs: List[PipelineRun] = []

    for file_path in sorted(runs_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            runs.append(PipelineRun.from_dict(data))
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    runs.sort(key=lambda r: r.created_at, reverse=True)
    return runs


def _dispatch_ready_steps(run: PipelineRun, memory_dir: Optional[Path] = None) -> int:
    """Identify pending steps whose dependencies have completed and publish their events."""
    pipeline_def = get_pipeline_definition(run.pipeline_name)
    if not pipeline_def:
        return 0

    steps_dict: Dict[str, PipelineStep] = {s.name: s for s in pipeline_def["steps"]}
    dispatched_count = 0
    stack = run.context.get("stack")

    for step_name, state in run.steps.items():
        if state.status != "PENDING":
            continue

        step_def = steps_dict.get(step_name)
        if not step_def:
            continue

        # Check if all upstream dependencies have completed
        dependencies_met = all(
            run.steps.get(dep) and run.steps[dep].status == "COMPLETED"
            for dep in step_def.depends_on
        )

        if dependencies_met:
            resolved_role = resolve_role_for_stack(step_def.role, stack)
            upstream_results = {
                dep: run.steps[dep].result
                for dep in step_def.depends_on
                if run.steps.get(dep) and run.steps[dep].result is not None
            }

            payload = {
                "run_id": run.run_id,
                "pipeline": run.pipeline_name,
                "step": step_name,
                "role": resolved_role,
                "description": step_def.description,
                "context": run.context,
                "upstream_results": upstream_results,
            }

            evt = publish_event(
                topic=step_def.topic,
                sender="choreographer",
                recipient=resolved_role,
                payload=payload,
                memory_dir=memory_dir,
            )

            state.status = "DISPATCHED"
            state.role = resolved_role
            state.event_id = evt.id
            state.dispatched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            dispatched_count += 1

    return dispatched_count


def create_pipeline_run(
    pipeline_name: str,
    context: Optional[Dict[str, Any]] = None,
    memory_dir: Optional[Path] = None,
) -> PipelineRun:
    """Instantiate, register, and launch a new choreography pipeline run."""
    pipeline_def = get_pipeline_definition(pipeline_name)
    if not pipeline_def:
        raise ValueError(f"Unknown pipeline: '{pipeline_name}'. Available: {list(STANDARD_PIPELINES.keys())}")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    run_id = f"run_{now_utc.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    now_iso = now_utc.isoformat()

    ctx = dict(context or {})
    stack = ctx.get("stack")

    steps: Dict[str, StepState] = {}
    for s in pipeline_def["steps"]:
        role = resolve_role_for_stack(s.role, stack)
        steps[s.name] = StepState(name=s.name, role=role, topic=s.topic)

    run = PipelineRun(
        run_id=run_id,
        pipeline_name=pipeline_name,
        status="RUNNING",
        created_at=now_iso,
        updated_at=now_iso,
        context=ctx,
        steps=steps,
    )

    # Dispatch initially available steps
    _dispatch_ready_steps(run, memory_dir=memory_dir)
    _save_pipeline_run(run, memory_dir=memory_dir)
    return run


def advance_step(
    run_id: str,
    step_name: str,
    status: str,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    claimer: Optional[str] = None,
    memory_dir: Optional[Path] = None,
) -> PipelineRun:
    """Transition a step's lifecycle state and trigger downstream step unlocks."""
    run = load_pipeline_run(run_id, memory_dir=memory_dir)
    if not run:
        raise ValueError(f"Pipeline run '{run_id}' not found.")

    if step_name not in run.steps:
        raise ValueError(f"Step '{step_name}' not defined in pipeline '{run.pipeline_name}'.")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    step = run.steps[step_name]
    step.status = status
    run.updated_at = now_iso

    if claimer is not None:
        step.claimer = claimer

    if result is not None:
        step.result = result

    if error is not None:
        step.error = error

    if status in ("COMPLETED", "FAILED"):
        step.completed_at = now_iso

    if status == "COMPLETED":
        # Dispatch newly unlocked steps
        _dispatch_ready_steps(run, memory_dir=memory_dir)

        # Check if entire pipeline has completed
        all_completed = all(s.status == "COMPLETED" for s in run.steps.values())
        if all_completed:
            run.status = "COMPLETED"

    elif status == "FAILED":
        run.status = "FAILED"

    _save_pipeline_run(run, memory_dir=memory_dir)
    return run


def cancel_pipeline_run(
    run_id: str,
    reason: str = "User cancelled",
    memory_dir: Optional[Path] = None,
) -> Optional[PipelineRun]:
    """Halt an active pipeline run and skip remaining unfinished steps."""
    run = load_pipeline_run(run_id, memory_dir=memory_dir)
    if not run:
        return None

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run.status = "CANCELLED"
    run.updated_at = now_iso
    run.context["cancel_reason"] = reason

    for step in run.steps.values():
        if step.status in ("PENDING", "DISPATCHED"):
            step.status = "SKIPPED"
            step.completed_at = now_iso

    _save_pipeline_run(run, memory_dir=memory_dir)
    return run
