---
name: workspace-doctor
description: Diagnoses workspace dependencies, validates build tool installations (Node, Java, Maven, Python), and verifies AGY compliance.
---

# Workspace Doctor Skill

## Overview
This skill performs end-to-end diagnostic health checks on the current development environment and project workspace. It verifies that required language runtimes, build systems, git hooks, and AGYToolkit governance files are correctly configured and operational.

## Operational Protocol

1. **Runtime & Toolchain Verification**:
   - Check Node.js: `node -v` (version 20+ recommended) and `npm -v`.
   - Check Java: `java -version` (Java 21/23 recommended) and `mvn -version`.
   - Check Python: `python --version` (Python 3.12 recommended) and virtual environment presence (`.venv`).
   - Check Git: `git --version` and working tree status.

2. **Governance & Filesystem Verification**:
   - Verify presence of `.agents/hooks.json` and verify that referenced hook scripts exist and are executable.
   - Verify presence of `.agents/skills/` and catalog installed skills.
   - Verify presence of `.agents/agents/` and catalog installed specialist subagents.
   - Verify presence of `.agents/memory/` and enforce byte limits on active-session and decisions files.
   - Verify `GEMINI.md` and `AGENTS.md` are present in workspace root.

3. **Remediation Recommendations**:
   - If a prerequisite runtime is missing, output exact installation instructions.
   - If hooks or rules are outdated or misconfigured, recommend running `agy-toolkit doctor --fix` or `agy-toolkit init`.

## Quality Gate & Verification Checklist
- [ ] Comprehensive diagnostic output across runtimes, git, and AGY assets.
- [ ] Actionable remediation steps for any missing dependencies.
- [ ] Formatted as concise technical markdown with zero emojis.
