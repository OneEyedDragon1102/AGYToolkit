---
name: plan-approval-gate
description: Enforces the plan-approval gate before code modifications. Structures implementation plans, definitions of done, and user sign-off protocols.
---

# Plan-Approval Gate Skill

## Overview
This skill operationalizes the mandatory plan-approval gate. In accordance with AGYToolkit governance, no code or structural files may be modified or created without an explicit, user-reviewed, and approved implementation plan artifact.

## Operational Protocol

1. **Pre-Implementation Assessment**:
   - Analyze requirements against existing architecture and code conventions.
   - Inspect existing tests, interfaces, and dependencies before proposing changes.

2. **Artifact Authoring**:
   - Create an implementation plan artifact in the brain artifact directory.
   - Set `RequestFeedback: true` in `ArtifactMetadata` so the UI presents an interactive review option.
   - Set `UserFacing: true`.

3. **Required Plan Sections**:
   - Executive Summary: Brief synopsis of the task and proposed resolution.
   - Architectural Decisions: New interfaces, state alterations, or schema migrations.
   - Step-by-Step Task Breakdown: Ordered, bite-sized units of work.
   - Verification Strategy: Exact test commands and criteria (unit, integration, lint).
   - Definition of Done: Checklist of explicit deliverables.

4. **Sign-Off Acquisition**:
   - Stop tool execution and request user approval or wait for interactive gate response.
   - Do not edit or create code files until user provides explicit confirmation.

## Quality Gate & Verification Checklist
- [ ] Implementation plan artifact created with `RequestFeedback: true`.
- [ ] Plan includes explicit file targets and verification test commands.
- [ ] Zero code files touched prior to explicit confirmation.
- [ ] Zero emojis in plan text or code listings.
