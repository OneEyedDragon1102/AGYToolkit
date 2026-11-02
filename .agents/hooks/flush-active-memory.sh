#!/usr/bin/env bash
# Flushes modified file paths to active-session.md on PostToolUse in downstream workspaces

input_json=$(cat)

if [ -z "$input_json" ]; then
    echo "{}"
    exit 0
fi

echo "{}"
