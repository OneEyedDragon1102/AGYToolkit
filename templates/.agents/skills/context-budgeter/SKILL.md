---
name: context-budgeter
description: Manages context window token usage, monitors byte budgets for session files, and offloads volatile data to prevent token exhaustion.
---

# Context Budgeter Skill

## Overview
This skill actively monitors and enforces token and byte budgets across conversation sessions. By offloading volatile data and maintaining compact session representations, it prevents token depletion and ensures seamless `/compact` operations without context loss.

## Operational Protocol

1. **Memory File Budget Enforcement**:
   - `active-session.md`: Hard limit of 1024 bytes (1 KB). Contains only the current active task, touchpoints, and operational mode.
   - `decisions.md`: Hard limit of 3072 bytes (3 KB). Contains concise architectural decisions and ADR links.

2. **Volatile Data Offloading**:
   - Large compiler outputs, stack traces, and JSON payloads exceeding 20 lines must be saved to `.agents/memory/volatile-bus/<timestamp>-<topic>.log`.
   - In-thread context should only reference the offloaded file path.

3. **Subagent Delegation Offloading**:
   - When a research or exploration task requires reading >5 files, delegate to an isolated subagent (`Workspace: 'branch'` or `'share'`).
   - The subagent must return only a synthesized markdown summary, keeping parent context clean.

4. **Compaction Preparation**:
   - Before recommending `/compact`, ensure all volatile changes are committed or summarized in `.agents/memory/decisions.md`.
   - Verify working tree status.

## Quality Gate & Verification Checklist
- [ ] Active session file remains <= 1024 bytes.
- [ ] Decisions file remains <= 3072 bytes.
- [ ] Raw logs > 20 lines written to volatile bus rather than pasted into conversation.
- [ ] Zero emojis in log dumps or memory tracking files.
