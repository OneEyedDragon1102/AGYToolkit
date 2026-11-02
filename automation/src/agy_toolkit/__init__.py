"""AGYToolkit - Python toolkit and utilities for Google Antigravity (AGY)."""

from agy_toolkit.bus import (
    BusEvent,
    publish_event,
    read_event,
    list_events,
    consume_events,
    clear_bus,
)
from agy_toolkit.doctor import run_doctor, DoctorReport
from agy_toolkit.linker import link_global
from agy_toolkit.mcp_server import McpServer
from agy_toolkit.memory import (
    check_memory_budgets,
    flush_active_session,
    record_decision,
)

__version__ = "0.1.0"

__all__ = [
    "BusEvent",
    "publish_event",
    "read_event",
    "list_events",
    "consume_events",
    "clear_bus",
    "run_doctor",
    "DoctorReport",
    "link_global",
    "McpServer",
    "check_memory_budgets",
    "flush_active_session",
    "record_decision",
]
