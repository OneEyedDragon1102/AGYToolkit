"""CLI handlers and parser configuration for AGYToolkit Multi-Agent Swarm Pipelines."""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from agy_toolkit.multi_repo import (
    format_multi_status_card,
    get_multi_run,
    launch_multi_run,
    load_workspace_manifest,
)
from agy_toolkit.choreographer import (
    advance_step,
    cancel_pipeline_run,
    create_pipeline_run,
    list_available_pipelines,
    list_pipeline_runs,
    load_pipeline_run,
)


def format_run_status(run) -> str:
    """Render human-readable formatted status card for a pipeline run."""
    lines = [
        "=" * 65,
        f" [AGYToolkit Swarm] Pipeline Run: {run.pipeline_name}",
        f" Run ID   : {run.run_id}",
        f" Status   : [{run.status}]",
        f" Created  : {run.created_at}",
        f" Updated  : {run.updated_at}",
        "-" * 65,
        " Steps Topology & Progress:",
    ]

    for name, step in run.steps.items():
        status_badge = f"[{step.status}]"
        role_info = f"({step.role})"
        event_info = f"Event: {step.event_id}" if step.event_id else ""
        claimer_info = f"Claimer: {step.claimer}" if step.claimer else ""
        detail = " | ".join(part for part in [event_info, claimer_info] if part)
        detail_str = f" - {detail}" if detail else ""
        lines.append(f"  * {status_badge:<13} {name:<16} {role_info:<26}{detail_str}")
        if step.error:
            lines.append(f"      Error: {step.error}")

    lines.append("=" * 65)
    return "\n".join(lines)


def handle_swarm(args):
    """Handle all subcommands under 'agy-toolkit swarm'."""
    action = args.swarm_action
    target_dir = Path(getattr(args, "path", ".") or ".").resolve() / ".agents" / "memory"

    if action == "pipelines":
        pipelines = list_available_pipelines()
        print("=" * 70)
        print(" [AGYToolkit Swarm] Standard Multi-Agent Blueprint Catalog")
        print("=" * 70)
        for p in pipelines:
            print(f"\n* {p['name']} ({p['steps_count']} steps):")
            print(f"   Desc: {p['description']}")
            step_flow = " -> ".join(s["name"] for s in p["steps"])
            print(f"   Flow: {step_flow}")
        print("\n" + "=" * 70)

    elif action == "run":
        pipeline_name = args.pipeline
        context: Dict[str, Any] = {}

        if getattr(args, "context", None):
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                context = {"raw_context": args.context}

        if getattr(args, "stack", None):
            context["stack"] = args.stack

        try:
            run = create_pipeline_run(
                pipeline_name=pipeline_name,
                context=context,
                memory_dir=target_dir,
            )
        except ValueError as ex:
            print(f"[AGYToolkit Swarm] Error: {str(ex)}")
            sys.exit(1)

        print(f"[AGYToolkit Swarm] Launched pipeline '{run.pipeline_name}' (Run ID: {run.run_id})")
        print(f" Status: [{run.status}]")
        dispatched = [s for s in run.steps.values() if s.status == "DISPATCHED"]
        if dispatched:
            print(" Initial Dispatched Step(s):")
            for s in dispatched:
                print(f"  * {s.name} -> {s.role} (Topic: {s.topic} | Event: {s.event_id})")

    elif action == "status":
        run_id = args.run_id
        run = load_pipeline_run(run_id, memory_dir=target_dir)
        if not run:
            print(f"[AGYToolkit Swarm] Pipeline run '{run_id}' not found.")
            sys.exit(1)

        if getattr(args, "json", False):
            print(json.dumps(run.to_dict(), indent=2))
        else:
            print(format_run_status(run))

    elif action == "list":
        runs = list_pipeline_runs(memory_dir=target_dir)
        if getattr(args, "json", False):
            print(json.dumps([r.to_dict() for r in runs], indent=2))
        else:
            print("=" * 70)
            print(f" [AGYToolkit Swarm] Active & Historical Pipeline Runs ({len(runs)} Total)")
            print("=" * 70)
            if not runs:
                print("  No swarm pipeline runs recorded.")
            for r in runs:
                completed = sum(1 for s in r.steps.values() if s.status == "COMPLETED")
                total = len(r.steps)
                print(f"  * [{r.status:<9}] {r.run_id} ({r.pipeline_name}) - Steps: {completed}/{total} - {r.created_at[:19]}")
            print("=" * 70)

    elif action == "advance":
        run_id = args.run_id
        step_name = args.step
        status = args.status.upper()
        raw_result = getattr(args, "result", None)
        error = getattr(args, "error", None)
        claimer = getattr(args, "claimer", None)

        result_val: Any = None
        if raw_result is not None:
            try:
                result_val = json.loads(raw_result)
            except json.JSONDecodeError:
                result_val = raw_result

        try:
            run = advance_step(
                run_id=run_id,
                step_name=step_name,
                status=status,
                result=result_val,
                error=error,
                claimer=claimer,
                memory_dir=target_dir,
            )
        except ValueError as ex:
            print(f"[AGYToolkit Swarm] Error: {str(ex)}")
            sys.exit(1)

        print(f"[AGYToolkit Swarm] Step '{step_name}' advanced to [{status}].")
        print(f" Overall Run Status: [{run.status}]")
        dispatched = [s for s in run.steps.values() if s.status == "DISPATCHED"]
        if dispatched:
            print(" Currently Dispatched Step(s):")
            for s in dispatched:
                print(f"  * {s.name} -> {s.role} (Topic: {s.topic} | Event: {s.event_id})")

    elif action == "cancel":
        run_id = args.run_id
        reason = getattr(args, "reason", "Operator cancelled") or "Operator cancelled"
        run = cancel_pipeline_run(run_id, reason=reason, memory_dir=target_dir)
        if not run:
            print(f"[AGYToolkit Swarm] Pipeline run '{run_id}' not found.")
            sys.exit(1)
        print(f"[AGYToolkit Swarm] Run '{run_id}' cancelled. Reason: {reason}")

    elif action == "worker":
        from agy_toolkit.worker import SwarmWorker

        workspace_root = Path(getattr(args, "path", ".") or ".").resolve()
        mem_dir = workspace_root / ".agents" / "memory"
        poll_interval = float(getattr(args, "poll_interval", 1.0) or 1.0)
        timeout_seconds = int(getattr(args, "timeout", 300) or 300)
        run_once = getattr(args, "run_once", False)
        max_cycles = getattr(args, "max_cycles", None)
        if max_cycles is not None:
            max_cycles = int(max_cycles)

        worker = SwarmWorker(
            memory_dir=mem_dir,
            workspace_root=workspace_root,
            poll_interval=poll_interval,
            timeout_seconds=timeout_seconds,
        )

        if run_once:
            print(f"[AGYToolkit Swarm Worker] Running single worker cycle (Worker ID: {worker.worker_id})...")
            res = worker.run_once()
            if res:
                print(f"[AGYToolkit Swarm Worker] Processed step '{res.step_name}' in run '{res.run_id}': [{res.status}] in {res.duration_ms}ms")
                if res.error:
                    print(f" Error: {res.error}")
            else:
                print("[AGYToolkit Swarm Worker] No dispatched steps found to claim.")
        else:
            print("=" * 70)
            print(f" [AGYToolkit Swarm Worker] Supervisor Daemon Active (ID: {worker.worker_id})")
            print(f" Workspace    : {workspace_root}")
            print(f" Poll Interval: {poll_interval}s | Timeout: {timeout_seconds}s")
            print(" Press Ctrl+C to stop daemon.")
            print("=" * 70)
            try:
                worker.run_loop(max_cycles=max_cycles)
            except KeyboardInterrupt:
                print("\n[AGYToolkit Swarm Worker] Supervisor daemon stopped.")

    elif action == "multi-run":
        ws_dir = Path(getattr(args, "path", ".") or ".").resolve()
        try:
            manifest = load_workspace_manifest(ws_dir)
        except Exception as ex:
            print(f"[AGYToolkit Multi-Repo Swarm] Error loading manifest: {str(ex)}")
            sys.exit(1)

        blueprint_name = args.blueprint
        context = {}
        if getattr(args, "context", None):
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                context = {"raw_context": args.context}

        try:
            run = launch_multi_run(manifest, blueprint_name, context=context)
            print(f"[AGYToolkit Multi-Repo Swarm] Launched run '{run.run_id}' for pipeline '{blueprint_name}'")
            print(format_multi_status_card(run, manifest))
        except Exception as ex:
            print(f"[AGYToolkit Multi-Repo Swarm] Error: {str(ex)}")
            sys.exit(1)

    elif action == "multi-status":
        ws_dir = Path(getattr(args, "path", ".") or ".").resolve()
        try:
            manifest = load_workspace_manifest(ws_dir)
        except Exception as ex:
            print(f"[AGYToolkit Multi-Repo Swarm] Error loading manifest: {str(ex)}")
            sys.exit(1)

        run = get_multi_run(manifest, args.run_id)
        if not run:
            print(f"[AGYToolkit Multi-Repo Swarm] Multi-repo run '{args.run_id}' not found.")
            sys.exit(1)

        if getattr(args, "json", False):
            print(json.dumps(run.to_dict(), indent=2))
        else:
            print(format_multi_status_card(run, manifest))


def configure_swarm_parser(swarm_sub):
    """Register all subparser arguments for 'agy-toolkit swarm'."""
    # pipelines list
    swarm_sub.add_parser("pipelines", help="List available blueprint pipelines and step DAG flows")

    # run command
    run_parser = swarm_sub.add_parser("run", help="Launch a new multi-agent choreography pipeline run")
    run_parser.add_argument("pipeline", help="Blueprint name (e.g. feature-sdlc, code-review, quickfix)")
    run_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    run_parser.add_argument("--stack", choices=["spring-boot", "node-ts", "python"], help="Primary tech stack")
    run_parser.add_argument("--context", help="Initial context payload as JSON string")

    # status command
    status_parser = swarm_sub.add_parser("status", help="Query execution status and progress of a run")
    status_parser.add_argument("run_id", help="Pipeline Run ID")
    status_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    status_parser.add_argument("--json", action="store_true", help="Output status report as JSON")

    # list command
    list_parser = swarm_sub.add_parser("list", help="List active and historical pipeline runs")
    list_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    list_parser.add_argument("--json", action="store_true", help="Output runs as JSON array")

    # advance command
    adv_parser = swarm_sub.add_parser("advance", help="Transition step status and trigger downstream unlocks")
    adv_parser.add_argument("run_id", help="Pipeline Run ID")
    adv_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    adv_parser.add_argument("--step", required=True, help="Step name to transition")
    adv_parser.add_argument("--status", required=True, choices=["COMPLETED", "FAILED", "CLAIMED"], help="New step status")
    adv_parser.add_argument("--result", help="Result payload (JSON or text)")
    adv_parser.add_argument("--error", help="Error message if step failed")
    adv_parser.add_argument("--claimer", help="Agent identifier reporting progress")

    # cancel command
    cancel_parser = swarm_sub.add_parser("cancel", help="Cancel an active pipeline run")
    cancel_parser.add_argument("run_id", help="Pipeline Run ID")
    cancel_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    cancel_parser.add_argument("--reason", default="Operator cancelled", help="Reason for cancellation")

    # worker command
    worker_parser = swarm_sub.add_parser("worker", help="Start autonomous swarm worker daemon or run single cycle")
    worker_parser.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    worker_parser.add_argument("--run-once", action="store_true", help="Execute single claim-and-advance sweep and exit")
    worker_parser.add_argument("--poll-interval", type=float, default=1.0, help="Polling interval in seconds (default: 1.0)")
    worker_parser.add_argument("--max-cycles", type=int, help="Maximum polling cycles before exiting")
    worker_parser.add_argument("--timeout", type=int, default=300, help="Step task execution timeout in seconds (default: 300)")

    # multi-run command
    mrun_parser = swarm_sub.add_parser("multi-run", help="Launch a cross-repository swarm pipeline run")
    mrun_parser.add_argument("blueprint", help="Multi-repo blueprint (e.g. fullstack-feature, cross-review)")
    mrun_parser.add_argument("path", nargs="?", default=".", help="Workspace root or manifest directory")
    mrun_parser.add_argument("--context", help="Initial context payload as JSON string")

    # multi-status command
    mstatus_parser = swarm_sub.add_parser("multi-status", help="Query cross-repository swarm run progress card")
    mstatus_parser.add_argument("run_id", help="Multi-repo Run ID (e.g. mrun-12345678)")
    mstatus_parser.add_argument("path", nargs="?", default=".", help="Workspace root or manifest directory")
    mstatus_parser.add_argument("--json", action="store_true", help="Output multi-run report as JSON")
