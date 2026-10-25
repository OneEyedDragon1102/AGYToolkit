"""AGYToolkit Persistent Memory Engine - Tiered memory management for AGY agents."""

import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

MEMORY_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".agents" / "memory"
ACTIVE_SESSION_PATH = MEMORY_DIR / "active-session.md"
DECISIONS_PATH = MEMORY_DIR / "decisions.md"
VOLATILE_BUS_DIR = MEMORY_DIR / "volatile-bus"
SESSIONS_DIR = MEMORY_DIR / "sessions"

ACTIVE_SESSION_BYTE_CAP = 1024  # 1 KB (~250 tokens)
DECISIONS_BYTE_CAP = 3072       # 3 KB (~750 tokens)


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
