---
name: commit-craft
description: Analyzes git status and staged diffs to draft clean, atomic Conventional Commits with minimal scopes.
---

# Commit Craft Skill

## Overview
This skill operationalizes AGYToolkit's atomic commit standards. It inspects git staging areas and crafts precise Conventional Commits (`<type>(<scope>): <summary>`), guaranteeing that commits remain bite-sized, single-purpose, and easily reviewable.

## Operational Protocol

1. **Staging Inspection**:
   - Run `git status` and `git diff --cached` to verify the exact staged changes.
   - Confirm that unrelated modifications, scratch files, or test logs are not staged.

2. **Commit Type Determination**:
   - `feat`: A new user-facing or architectural capability.
   - `fix`: A bug fix.
   - `test`: Adding or correcting tests with zero production code changes.
   - `refactor`: Code restructuring without functional behavior changes.
   - `docs`: Documentation, runbooks, or architectural ADRs only.
   - `chore`: Dependency updates, tooling, or build configuration adjustments.

3. **Scope & Summary Formatting**:
   - Scope: Specific module, package, or component affected (e.g., `feat(auth):`, `fix(session):`, `test(scaffolder):`).
   - Summary: Imperative, present-tense, lower-case phrase without trailing punctuation (<= 72 characters).
   - Body (optional): Bulleted explanation of why the change was made and key trade-offs.

4. **Sign-Off Gate**:
   - Present the draft commit message and staged diff summary to the user for explicit sign-off before committing.

## Quality Gate & Verification Checklist
- [ ] Strictly follows Conventional Commits format.
- [ ] Commit covers exactly one logical change (atomic commit rule).
- [ ] Scope accurately reflects the touched subsystem.
- [ ] Zero emojis in commit message title or body.
