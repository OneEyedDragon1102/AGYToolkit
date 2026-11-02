"""AGYToolkit Event Bus - Inter-process communication and message bus for AGY multi-agent swarms."""

import datetime
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.memory import ensure_memory_dirs, MEMORY_DIR


@dataclass
class BusEvent:
    """Standardized event envelope for inter-agent communication."""
    id: str
    timestamp: str
    topic: str
    sender: str
    recipient: str
    payload: Any
    ttl_seconds: int = 3600
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusEvent":
        """Reconstruct event from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            topic=data["topic"],
            sender=data["sender"],
            recipient=data.get("recipient", "*"),
            payload=data.get("payload"),
            ttl_seconds=data.get("ttl_seconds", 3600),
            metadata=data.get("metadata"),
        )

    def is_expired(self, current_time: Optional[datetime.datetime] = None) -> bool:
        """Check whether the event has exceeded its time-to-live threshold."""
        if self.ttl_seconds <= 0:
            return False
        now = current_time or datetime.datetime.now(datetime.timezone.utc)
        try:
            event_time = datetime.datetime.fromisoformat(self.timestamp)
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=datetime.timezone.utc)
            delta = (now - event_time).total_seconds()
            return delta > self.ttl_seconds
        except (ValueError, TypeError):
            return False


def _get_volatile_bus_dir(memory_dir: Optional[Path] = None) -> Path:
    """Resolve and ensure volatile-bus directory."""
    base_dir = ensure_memory_dirs(memory_dir)
    bus_dir = base_dir / "volatile-bus"
    bus_dir.mkdir(parents=True, exist_ok=True)
    return bus_dir


def publish_event(
    topic: str,
    sender: str,
    payload: Any,
    recipient: str = "*",
    ttl_seconds: int = 3600,
    metadata: Optional[Dict[str, Any]] = None,
    memory_dir: Optional[Path] = None,
) -> BusEvent:
    """Publish a structured event envelope to the volatile bus with atomic persistence."""
    bus_dir = _get_volatile_bus_dir(memory_dir)
    event_id = f"evt_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    event = BusEvent(
        id=event_id,
        timestamp=now_iso,
        topic=topic,
        sender=sender,
        recipient=recipient,
        payload=payload,
        ttl_seconds=ttl_seconds,
        metadata=metadata or {},
    )

    target_file = bus_dir / f"{event_id}.json"

    # Atomic write pattern using tempfile
    with tempfile.NamedTemporaryFile("w", dir=str(bus_dir), delete=False, encoding="utf-8") as tf:
        json.dump(event.to_dict(), tf, indent=2)
        temp_name = tf.name

    os.replace(temp_name, str(target_file))
    return event


def read_event(
    event_id: str,
    consume: bool = False,
    memory_dir: Optional[Path] = None,
) -> Optional[BusEvent]:
    """Read a specific event by its identifier, optionally deleting it upon consumption."""
    bus_dir = _get_volatile_bus_dir(memory_dir)
    target_file = bus_dir / f"{event_id}.json"

    if not target_file.exists():
        return None

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        event = BusEvent.from_dict(data)

        if consume:
            try:
                target_file.unlink()
            except OSError:
                pass

        return event
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def list_events(
    topic: Optional[str] = None,
    recipient: Optional[str] = None,
    sender: Optional[str] = None,
    include_expired: bool = False,
    memory_dir: Optional[Path] = None,
) -> List[BusEvent]:
    """List and filter events currently stored in the volatile bus."""
    bus_dir = _get_volatile_bus_dir(memory_dir)
    events: List[BusEvent] = []

    for file_path in sorted(bus_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            event = BusEvent.from_dict(data)

            if not include_expired and event.is_expired():
                continue

            if topic and event.topic != topic:
                continue

            if recipient and event.recipient not in ("*", recipient):
                continue

            if sender and event.sender != sender:
                continue

            events.append(event)
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return events


def consume_events(
    topic: Optional[str] = None,
    recipient: Optional[str] = None,
    sender: Optional[str] = None,
    memory_dir: Optional[Path] = None,
) -> List[BusEvent]:
    """Read and remove all events matching the specified criteria."""
    events = list_events(
        topic=topic,
        recipient=recipient,
        sender=sender,
        include_expired=False,
        memory_dir=memory_dir,
    )
    bus_dir = _get_volatile_bus_dir(memory_dir)

    for event in events:
        file_path = bus_dir / f"{event.id}.json"
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass

    return events


def prune_expired_events(memory_dir: Optional[Path] = None) -> int:
    """Remove all expired event payloads from the volatile bus."""
    bus_dir = _get_volatile_bus_dir(memory_dir)
    pruned_count = 0

    for file_path in bus_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            event = BusEvent.from_dict(data)
            if event.is_expired():
                file_path.unlink()
                pruned_count += 1
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return pruned_count


def clear_bus(memory_dir: Optional[Path] = None) -> int:
    """Wipe all event JSON files from the volatile bus while preserving gitignore files."""
    bus_dir = _get_volatile_bus_dir(memory_dir)
    cleared_count = 0

    for file_path in bus_dir.glob("*.json"):
        try:
            file_path.unlink()
            cleared_count += 1
        except OSError:
            continue

    return cleared_count
