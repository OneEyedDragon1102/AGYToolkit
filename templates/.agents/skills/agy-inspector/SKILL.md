---
name: agy-inspector
description: Inspects, catalogs, and verifies all AGY tools, skills, rules, hooks, and MCP servers configured in the workspace or environment. Use when checking tool readiness or running diagnostic audits.
---

# AGY Inspector Skill

## Overview
This skill guides the agent in diagnosing and verifying all active AGY capabilities, registered tools, MCP servers, and workspace configurations. It provides a complete situational awareness audit of the agentic operating environment.

## Operational Protocol

1. **Verify Core Agent Capabilities**:
   - Check file system access (`read_file`, `write_file`, `edit_file`).
   - Check shell command execution (`run_command`).
   - Check background task manager (`manage_task`).
   - Check timer and cron scheduling (`schedule`).
   - Check multi-agent registration (`define_subagent`, `invoke_subagent`).

2. **Inspect Customizations**:
   - Check `.agents/skills/` for workspace-level skills.
   - Check `GEMINI.md` and `AGENTS.md` for project rules.
   - Check `hooks.json` for active lifecycle hooks.

3. **Check MCP Server Status**:
   - Check available MCP servers (`context7`, `puppeteer`, `sequential-thinking`).
   - Verify tool schemas and lazily loaded tools.

4. **Audit Report Synthesis**:
   - Output a structured readiness report summarizing working directories, active branch, installed skills, and hook status.

## Quality Gate & Verification Checklist
- [ ] Core tools confirmed available and functional.
- [ ] Active workspace paths and permissions verified.
- [ ] Custom hooks and rules loaded.
- [ ] Clean markdown output with zero emojis.
