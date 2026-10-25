---
name: branch-manager
description: Governs git branching workflows, branch synchronization, branch naming conventions, and branch isolation rules.
---

# Branch Manager Skill

## Overview
This skill governs repository branching strategies. In accordance with AGYToolkit policy, direct development on `main` is strictly prohibited. All development occurs in dedicated feature, fix, or spike branches branched from clean, up-to-date baselines.

## Operational Protocol

1. **Baseline Synchronization**:
   - Verify working tree is clean (`git status`).
   - Switch to `main` and pull latest changes (`git checkout main && git pull origin main`).

2. **Branch Creation Conventions**:
   - New capabilities: `feature/<feature-name>` (e.g., `feature/user-auth-jwt`).
   - Defect fixes: `fix/<bug-description>` (e.g., `fix/token-refresh-leak`).
   - Exploratory spikes: `spike/<topic>` (e.g., `spike/fastify-sse-benchmarks`).
   - Execute branch creation: `git checkout -b <branch-name>`.

3. **Branch Hygiene & Conflict Prevention**:
   - Keep feature branches short-lived (merge within 24-48 hours).
   - Rebase or merge from `main` frequently to resolve integration drifts early.

4. **Post-Merge Cleanup**:
   - Once a pull request is merged upstream, delete local branch (`git branch -d <branch-name>`).

## Quality Gate & Verification Checklist
- [ ] Direct commits to `main` blocked by pre-commit or pre-tool hooks.
- [ ] Branch names strictly conform to `<type>/<kebab-case-name>`.
- [ ] Working tree verified clean before switching branches.
- [ ] Zero emojis in branch names.
