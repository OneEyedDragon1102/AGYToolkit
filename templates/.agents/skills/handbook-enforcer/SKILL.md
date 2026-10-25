---
name: handbook-enforcer
description: Validates and enforces engineering standards, repository guidelines, and coding handbook rules defined in GEMINI.md and AGENTS.md.
---

# Handbook Enforcer Skill

## Overview
This skill actively audits workspace operations against project-specific engineering rules defined in `GEMINI.md` and `AGENTS.md`. It acts as an automated guard verifying that all contributors and subagents comply with operational standards.

## Operational Protocol

1. **Rule Discovery & Loading**:
   - Locate and parse `GEMINI.md` and `AGENTS.md` in the workspace root.
   - Extract technical constraints: required language versions, forbidden libraries, architectural style (e.g., Hexagonal Architecture, Clean Architecture).

2. **Compliance Verification**:
   - Verify branch naming: Must follow `feature/<name>`, `bugfix/<name>`, or `spike/<name>`.
   - Verify file size boundaries: Flag any source file exceeding 600 lines for modularization.
   - Verify comment hygiene: Reject conversational chatter (e.g., "Now we do this", "Let us check that"). Enforce technical documentation only.
   - Verify emoji ban: Ensure 0 emojis in code, comments, logs, and commit messages.

3. **Violation Remediation**:
   - When violations occur, output precise line references and provide refactoring instructions before allowing the workflow to advance.

## Quality Gate & Verification Checklist
- [ ] Confirms `GEMINI.md` and `AGENTS.md` exist and are respected.
- [ ] Direct commits to `main` strictly prohibited.
- [ ] Monolithic files (>600 lines) blocked from staging.
- [ ] Zero emojis detected in source code.
