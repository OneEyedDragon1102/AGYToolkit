"""AGYToolkit Persistent Memory Engine - Tiered memory management for AGY agents."""

import datetime
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

MEMORY_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".agents" / "memory"
ACTIVE_SESSION_PATH = MEMORY_DIR / "active-session.md"
DECISIONS_PATH = MEMORY_DIR / "decisions.md"
VOLATILE_BUS_DIR = MEMORY_DIR / "volatile-bus"
SESSIONS_DIR = MEMORY_DIR / "sessions"

ACTIVE_SESSION_BYTE_CAP = 1024  # 1 KB (~250 tokens)
DECISIONS_BYTE_CAP = 3072       # 3 KB (~750 tokens)

ACTIVE_SESSION_CAP = ACTIVE_SESSION_BYTE_CAP
DECISIONS_CAP = DECISIONS_BYTE_CAP


@dataclass
class CompactReport:
    active_session_compacted: bool = False
    active_session_bytes_before: int = 0
    active_session_bytes_after: int = 0
    decisions_compacted: bool = False
    decisions_bytes_before: int = 0
    decisions_bytes_after: int = 0
    archived_session_path: Optional[str] = None
    archived_adr_path: Optional[str] = None
    decisions_evicted_count: int = 0
    advice: List[str] = field(default_factory=list)
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def ensure_memory_dirs(memory_dir: Optional[Path] = None) -> Path:
    target_dir = memory_dir or MEMORY_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "volatile-bus").mkdir(parents=True, exist_ok=True)
    (target_dir / "sessions").mkdir(parents=True, exist_ok=True)
    return target_dir


def get_active_session(memory_dir: Optional[Path] = None) -> str:
    path = (memory_dir or MEMORY_DIR) / "active-session.md"
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def flush_active_session(
    archive: bool = True,
    memory_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Flush working session memory, optionally archiving previous state."""
    target_dir = ensure_memory_dirs(memory_dir)
    active_path = target_dir / "active-session.md"
    archive_path = None

    if active_path.exists() and archive:
        content = active_path.read_text(encoding="utf-8").strip()
        if content:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = target_dir / "sessions" / f"{timestamp}_session.md"
            archive_path.write_text(content + "\n", encoding="utf-8")

    clean_template = """# Active Session State

- **Active Goal**: None
- **Current Branch**: `main`
- **Active Agent**: `orchestrator`
- **Immediate Next Step**: Awaiting instructions

## Modified Files
- None

## Open Blockers
- None
"""
    active_path.write_text(clean_template, encoding="utf-8")
    return archive_path


def update_active_session(
    goal: str,
    branch: str,
    active_agent: str,
    modified_files: List[str],
    next_step: str,
    blockers: Optional[List[str]] = None,
    memory_dir: Optional[Path] = None,
) -> None:
    target_dir = ensure_memory_dirs(memory_dir)
    path = target_dir / "active-session.md"

    files_list = "\n".join([f"- `{f}`" for f in modified_files]) if modified_files else "- None"
    blockers_list = "\n".join([f"- {b}" for b in blockers]) if blockers else "- None"

    content = f"""# Active Session State

- **Active Goal**: {goal}
- **Current Branch**: `{branch}`
- **Active Agent**: `{active_agent}`
- **Immediate Next Step**: {next_step}

## Modified Files
{files_list}

## Open Blockers
{blockers_list}
"""
    # Enforce 1 KB byte cap
    encoded = content.encode("utf-8")
    if len(encoded) > ACTIVE_SESSION_BYTE_CAP:
        # Prune modified files list to fit within cap
        pruned_files = modified_files[-3:]
        files_list = "\n".join([f"- `{f}`" for f in pruned_files])
        content = f"""# Active Session State

- **Active Goal**: {goal}
- **Current Branch**: `{branch}`
- **Active Agent**: `{active_agent}`
- **Immediate Next Step**: {next_step}

## Modified Files (Recent)
{files_list}

## Open Blockers
{blockers_list}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")


def record_decision(
    category: str,
    decision: str,
    date_str: Optional[str] = None,
    memory_dir: Optional[Path] = None,
) -> None:
    target_dir = ensure_memory_dirs(memory_dir)
    path = target_dir / "decisions.md"
    date_prefix = date_str or datetime.date.today().isoformat()

    new_entry = f"- **{date_prefix} [{category}]**: {decision}\n"

    existing = ""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = "# Binding Architectural Decisions Register\n\n"

    # Append new entry
    updated = existing.strip() + "\n" + new_entry

    # Enforce 3 KB byte cap
    encoded = updated.encode("utf-8")
    if len(encoded) > DECISIONS_BYTE_CAP:
        # Keep header and the most recent decisions
        lines = updated.splitlines()
        header = lines[:2]
        entries = [l for l in lines[2:] if l.strip().startswith("- **")]
        while entries and len("\n".join(header + entries).encode("utf-8")) > DECISIONS_BYTE_CAP:
            entries.pop(0)  # Evict oldest decision
        updated = "\n".join(header + entries) + "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)


def write_bus_payload(payload_id: str, data: Dict, memory_dir: Optional[Path] = None) -> Path:
    target_dir = ensure_memory_dirs(memory_dir)
    file_path = target_dir / "volatile-bus" / f"{payload_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path


def read_bus_payload(payload_id: str, memory_dir: Optional[Path] = None) -> Dict:
    target_dir = ensure_memory_dirs(memory_dir)
    file_path = target_dir / "volatile-bus" / f"{payload_id}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Volatile payload not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def record_session_event(event_type: str, details: Dict, memory_dir: Optional[Path] = None) -> Path:
    target_dir = ensure_memory_dirs(memory_dir)
    today = datetime.date.today().isoformat()
    session_file = target_dir / "sessions" / f"{today}.jsonl"

    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "eventType": event_type,
        "details": details,
    }

    with open(session_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return session_file


def check_memory_budgets(memory_dir: Optional[Path] = None) -> Dict[str, Dict]:
    target_dir = memory_dir or MEMORY_DIR
    active_path = target_dir / "active-session.md"
    decisions_path = target_dir / "decisions.md"

    active_bytes = active_path.stat().st_size if active_path.exists() else 0
    decisions_bytes = decisions_path.stat().st_size if decisions_path.exists() else 0

    return {
        "active_session": {
            "bytes": active_bytes,
            "cap": ACTIVE_SESSION_BYTE_CAP,
            "within_budget": active_bytes <= ACTIVE_SESSION_BYTE_CAP,
        },
        "decisions": {
            "bytes": decisions_bytes,
            "cap": DECISIONS_BYTE_CAP,
            "within_budget": decisions_bytes <= DECISIONS_BYTE_CAP,
        },
    }


def auto_compact_memory(
    memory_dir: Optional[Path] = None,
    threshold: float = 0.85,
    workspace_root: Optional[Path] = None,
    dry_run: bool = False,
) -> CompactReport:
    """Evaluate memory budgets and auto-compact session and decisions if above threshold."""
    target_dir = ensure_memory_dirs(memory_dir)
    ws_root = workspace_root
    if ws_root is None:
        if target_dir.parent.name == ".agents":
            ws_root = target_dir.parent.parent
        else:
            ws_root = Path.cwd()

    report = CompactReport(dry_run=dry_run)

    # 1. Active Session Compaction
    active_path = target_dir / "active-session.md"
    if active_path.exists():
        content = active_path.read_text(encoding="utf-8")
        bytes_before = len(content.encode("utf-8"))
        report.active_session_bytes_before = bytes_before
        report.active_session_bytes_after = bytes_before

        session_threshold_limit = int(ACTIVE_SESSION_CAP * threshold)
        if bytes_before > session_threshold_limit:
            report.active_session_compacted = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = target_dir / "sessions" / f"{timestamp}_session.md"
            report.archived_session_path = str(archive_file)

            if not dry_run:
                archive_file.write_text(content, encoding="utf-8")

            # Prune active session to essential state
            goal = "None"
            branch = "`main`"
            agent = "`orchestrator`"
            next_step = "Awaiting instructions"
            blockers = "- None"

            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("- **Active Goal**:"):
                    goal = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("- **Current Branch**:"):
                    branch = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("- **Active Agent**:"):
                    agent = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("- **Immediate Next Step**:"):
                    next_step = stripped.split(":", 1)[1].strip()

            if "## Open Blockers" in content:
                parts = content.split("## Open Blockers", 1)
                blockers_section = parts[1].strip()
                blocker_lines = []
                for bline in blockers_section.splitlines():
                    if bline.strip().startswith("#"):
                        break
                    if bline.strip():
                        blocker_lines.append(bline)
                if blocker_lines:
                    blockers = "\n".join(blocker_lines)

            pruned_session = (
                "# Active Session State\n\n"
                f"- **Active Goal**: {goal}\n"
                f"- **Current Branch**: {branch}\n"
                f"- **Active Agent**: {agent}\n"
                f"- **Immediate Next Step**: {next_step}\n\n"
                "## Modified Files (Recent)\n"
                "- None (archived to sessions/)\n\n"
                "## Open Blockers\n"
                f"{blockers}\n"
            )
            report.active_session_bytes_after = len(pruned_session.encode("utf-8"))
            if not dry_run:
                active_path.write_text(pruned_session, encoding="utf-8")

            report.advice.append(
                "Active session archived and pruned. Run /compact in AGY IDE to summarize context."
            )

    # 2. Decisions Compaction (FIFO eviction to docs/adr/decisions-history.md)
    decisions_path = target_dir / "decisions.md"
    if decisions_path.exists():
        d_content = decisions_path.read_text(encoding="utf-8")
        d_bytes_before = len(d_content.encode("utf-8"))
        report.decisions_bytes_before = d_bytes_before
        report.decisions_bytes_after = d_bytes_before

        decisions_threshold_limit = int(DECISIONS_CAP * threshold)
        if d_bytes_before > decisions_threshold_limit:
            report.decisions_compacted = True
            adr_dir = ws_root / "docs" / "adr"
            adr_file = adr_dir / "decisions-history.md"
            report.archived_adr_path = str(adr_file)

            lines = d_content.splitlines()
            header_lines = []
            entry_chunks = []
            current_chunk = []
            in_entries = False

            for line in lines:
                if line.strip().startswith("- **"):
                    in_entries = True
                    if current_chunk:
                        entry_chunks.append("\n".join(current_chunk))
                        current_chunk = []
                if in_entries:
                    current_chunk.append(line)
                else:
                    header_lines.append(line)
            if current_chunk:
                entry_chunks.append("\n".join(current_chunk))

            header_str = "\n".join(header_lines).strip()
            if not header_str:
                header_str = "# Binding Architectural Decisions Register"

            target_bytes = int(DECISIONS_CAP * 0.60)
            evicted_chunks = []
            while entry_chunks and len(entry_chunks) > 1:
                assembled = header_str + "\n\n" + "\n".join(entry_chunks) + "\n"
                if len(assembled.encode("utf-8")) <= target_bytes:
                    break
                evicted_chunks.append(entry_chunks.pop(0))

            assembled_decisions = header_str + "\n\n" + "\n".join(entry_chunks) + "\n"
            report.decisions_evicted_count = len(evicted_chunks)
            report.decisions_bytes_after = len(assembled_decisions.encode("utf-8"))

            if evicted_chunks:
                report.advice.append(
                    f"Evicted {len(evicted_chunks)} older decisions to docs/adr/decisions-history.md. Run /compact in AGY IDE."
                )
                if not dry_run:
                    adr_dir.mkdir(parents=True, exist_ok=True)
                    if adr_file.exists():
                        existing_adr = adr_file.read_text(encoding="utf-8").rstrip()
                        new_adr = existing_adr + "\n" + "\n".join(evicted_chunks) + "\n"
                    else:
                        new_adr = (
                            "# Architectural Decisions History (Archived)\n\n"
                            "Historical decisions evicted from active working memory (.agents/memory/decisions.md).\n\n"
                            + "\n".join(evicted_chunks)
                            + "\n"
                        )
                    adr_file.write_text(new_adr, encoding="utf-8")
                    decisions_path.write_text(assembled_decisions, encoding="utf-8")

    # 3. Incremental Tier 3 Knowledge Indexing after compaction
    if not dry_run and (report.active_session_compacted or report.decisions_compacted):
        try:
            from agy_toolkit.knowledge import index_workspace
            index_workspace(ws_root)
        except Exception:
            pass

    return report


def format_compact_report(report: CompactReport) -> str:
    lines = [
        "[AGYToolkit Memory Engine] Auto-Compaction Report",
        "=" * 50,
        f"Dry Run: {report.dry_run}",
        f"Active Session Compacted: {report.active_session_compacted}",
    ]
    if report.active_session_compacted:
        lines.append(f"  - Bytes Before: {report.active_session_bytes_before} B")
        lines.append(f"  - Bytes After: {report.active_session_bytes_after} B")
        if report.archived_session_path:
            lines.append(f"  - Archive: {report.archived_session_path}")
    lines.append(f"Decisions Compacted: {report.decisions_compacted}")
    if report.decisions_compacted:
        lines.append(f"  - Evicted Entries: {report.decisions_evicted_count}")
        lines.append(f"  - Bytes Before: {report.decisions_bytes_before} B")
        lines.append(f"  - Bytes After: {report.decisions_bytes_after} B")
        if report.archived_adr_path:
            lines.append(f"  - ADR Archive: {report.archived_adr_path}")
    if report.advice:
        lines.append("\nAdvice:")
        for adv in report.advice:
            lines.append(f"  - {adv}")
    return "\n".join(lines)
