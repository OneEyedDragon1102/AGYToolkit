---
name: telemetry-logger
description: Structures execution logs, cross-agent handoffs, and performance benchmarks into standard audit streams.
---

# Telemetry Logger Skill

## Overview
This skill establishes standardized telemetry and event logging across multi-agent workflows. It ensures that subagent transitions, test execution timings, and tool invocations produce deterministic, machine-parsable audit trails.

## Operational Protocol

1. **Log Record Structure**:
   - Each telemetry entry must include:
     - ISO-8601 UTC timestamp.
     - Event Type: `AGENT_HANDOFF`, `TOOL_EXECUTION`, `TEST_RUN`, `GATE_CHECK`.
     - Initiator & Target Agent/Tool.
     - Duration in milliseconds.
     - Status: `SUCCESS`, `FAILURE`, `ABORTED`.
     - Summary payload (concise, technical).

2. **Handoff Tracking**:
   - When `orchestrator` transfers context to a specialist (e.g., `spring-boot-engineer`), log the target branch, ticket/task ID, and input contract hash.

3. **Performance Metrics**:
   - Record test suite execution duration and memory footprint.
   - Flag test runs exceeding SLA thresholds (e.g., unit test suite > 10 seconds).

4. **Storage Destination**:
   - Append records to `.agents/memory/volatile-bus/telemetry.jsonl` or print standardized single-line JSON log strings.

## Quality Gate & Verification Checklist
- [ ] Telemetry records strictly format-compliant (valid JSON or JSON Lines).
- [ ] No raw passwords, API keys, or personal tokens recorded in telemetry logs.
- [ ] Timestamps formatted in UTC.
- [ ] Zero emojis in telemetry output streams.
