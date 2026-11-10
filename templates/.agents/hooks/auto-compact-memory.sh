#!/usr/bin/env bash
# Auto-compaction hook for tiered agent memory on PostToolUse

input_json=$(cat)

if [ -z "$input_json" ]; then
    echo '{"decision": "allow"}'
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$AGENTS_DIR")"
MEM_DIR="$AGENTS_DIR/memory"
ACTIVE_SESSION="$MEM_DIR/active-session.md"
DECISIONS="$MEM_DIR/decisions.md"

NEEDS_COMPACT=0

if [ -f "$ACTIVE_SESSION" ]; then
    SIZE=$(wc -c < "$ACTIVE_SESSION" 2>/dev/null || stat -f%z "$ACTIVE_SESSION" 2>/dev/null || echo 0)
    if [ "$SIZE" -ge 870 ]; then
        NEEDS_COMPACT=1
    fi
fi

if [ -f "$DECISIONS" ]; then
    D_SIZE=$(wc -c < "$DECISIONS" 2>/dev/null || stat -f%z "$DECISIONS" 2>/dev/null || echo 0)
    if [ "$D_SIZE" -ge 2611 ]; then
        NEEDS_COMPACT=1
    fi
fi

if [ "$NEEDS_COMPACT" -eq 1 ]; then
    PY_CMD="python3"
    if ! command -v python3 &>/dev/null; then
        PY_CMD="python"
    fi
    if command -v "$PY_CMD" &>/dev/null; then
        PYTHONPATH="$REPO_ROOT/automation/src:$PYTHONPATH" "$PY_CMD" -m agy_toolkit memory auto-compact "$REPO_ROOT" --json >/dev/null 2>&1
        echo '{"decision": "allow", "advice": "Memory auto-compacted. Consider running /compact in AGY IDE."}'
        exit 0
    fi
fi

echo '{"decision": "allow"}'
