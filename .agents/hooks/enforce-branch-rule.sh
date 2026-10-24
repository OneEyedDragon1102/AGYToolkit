#!/usr/bin/env bash
# Enforces that no git commits are made directly on 'main' branch

input_json=$(cat)

if [ -z "$input_json" ]; then
    echo '{"decision": "allow"}'
    exit 0
fi

tool_name=$(echo "$input_json" | grep -o '"name": *"[^"]*"' | head -1 | cut -d'"' -f4)
cmd_line=$(echo "$input_json" | grep -o '"CommandLine": *"[^"]*"' | head -1 | cut -d'"' -f4)

if [ "$tool_name" = "run_command" ]; then
    if echo "$cmd_line" | grep -Eq "git\s+commit|git\s+push\s+.*main"; then
        current_branch=$(git branch --show-current 2>/dev/null)
        if [ "$current_branch" = "main" ]; then
            echo '{"decision": "deny", "reason": "Branch Rule Violation: Direct commits or pushes to main are strictly forbidden. Switch to a feature branch."}'
            exit 0
        fi
    fi
fi

echo '{"decision": "allow"}'
