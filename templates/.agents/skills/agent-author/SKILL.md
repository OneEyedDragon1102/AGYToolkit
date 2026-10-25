---
name: agent-author
description: Authors project-specific specialist subagents on demand inside target workspaces using AGY hybrid Markdown specifications.
---

# Agent Author Skill

## Overview
This meta-skill guides the dynamic generation of domain-specific specialist subagents within target workspaces. When a project requires specialized personas with distinct tool permissions, workspace isolation modes, or architectural mandates (e.g., ADB device control, quant trading execution), this skill authors a hybrid Markdown agent specification in `.agents/agents/<agent-name>.md`.

## Operational Protocol

1. **Agent Role & Boundary Definition**:
   - Delineate the exact responsibilities of the subagent following the Single Responsibility Principle.
   - Determine tool permissions:
     - `enableWriteTools`: True for coding agents, False for auditing/reviewing agents.
     - `enableSubagentTools`: False by default (only `orchestrator` should spawn subagents).
     - `enableMCPTools`: True if the agent requires browser automation, external docs, or database access.
   - Select workspace isolation mode: `inherit` for conductors, `branch` for feature developers, `share` for read-only reviewers.

2. **Hybrid Markdown Anatomy**:
   - YAML Frontmatter:
     - `name`: Kebab-case identifier matching the filename.
     - `role`: 2-4 word professional job title.
     - `description`: 1-2 sentence description of role and responsibilities.
     - `recommendedWorkspace`: `inherit`, `branch`, or `share`.
     - `enableWriteTools`: boolean.
     - `enableSubagentTools`: boolean.
     - `enableMCPTools`: boolean.
   - Body Sections:
     - `# <Role Title>`
     - `## Operational Mandate`: Deep system prompt defining domain authority.
     - `## Strict Architectural Non-Negotiables`: Invariants and rules.
     - `## Handoff Contract`: Inputs consumed, workspace execution mode, output delivered.
     - `## Definition of Done (DoD)`: Concrete delivery checklist.

3. **Anti-Bloat Standards**:
   - Zero emojis anywhere in the agent definition.
   - Prohibit conversational or open-ended instructions.
   - Keep total specification under 100 lines.

## Quality Gate & Verification Checklist
- [ ] Spec created in `.agents/agents/<agent-name>.md`.
- [ ] Valid YAML frontmatter with all required keys.
- [ ] Handoff Contract and Definition of Done present.
- [ ] Zero emojis in agent specification.
