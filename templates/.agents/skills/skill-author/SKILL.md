---
name: skill-author
description: Authors project-specific domain skills on demand inside target workspaces following AGY progressive disclosure standards.
---

# Skill Author Skill

## Overview
This meta-skill guides the dynamic generation of domain-specific skills within target workspaces. When a project requires specialized operational playbooks (such as ADB device tapping, trading backtesting, or email triage), this skill authors a structured, progressive `SKILL.md` file in `.agents/skills/<skill-name>/` to give agents immediate, high-signal domain competence without polluting the global framework.

## Operational Protocol

1. **Domain Requirement Ingestion**:
   - Identify the specific domain capability, repetitive runbook, or external library integration needed by the workspace.
   - Determine the trigger criteria: What user prompt or operational phase invokes this skill?

2. **Skill Anatomy Specification**:
   - Location: `.agents/skills/<skill-name>/SKILL.md`
   - YAML Frontmatter:
     - `name`: Kebab-case identifier matching the directory name.
     - `description`: 1-3 sentences stating what the skill does and exact triggers for when to use it.
   - Document Structure:
     - `# <Skill Name>`
     - `## Overview`: Concise statement of domain purpose.
     - `## Strict Architectural Non-Negotiables`: Invariants and constraints for this domain.
     - `## Operational Protocol`: Step-by-step procedures, CLI commands, or API calls.
     - `## Quality Gate & Verification Checklist`: Checklist validating task completion.

3. **Anti-Bloat Standards**:
   - Strictly 0 emojis in source code, documentation, or instructions.
   - Keep instructions concise, factual, and actionable. Avoid conversational filler.
   - Ensure file size remains under 200 lines to preserve token efficiency.

4. **Workspace Registration**:
   - Write the skill to `.agents/skills/<skill-name>/SKILL.md`.
   - Verify that AGY recognizes the new skill via `agy-inspector` or CLI audit.

## Quality Gate & Verification Checklist
- [ ] Skill created in `.agents/skills/<skill-name>/SKILL.md`.
- [ ] Valid YAML frontmatter with `name` and `description`.
- [ ] Contains Overview, Protocol, and Verification Checklist.
- [ ] Zero emojis in file content.
