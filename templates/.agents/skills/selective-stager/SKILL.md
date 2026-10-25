---
name: selective-stager
description: Manages granular git staging, ensures only verified diffs are added, and presents staged changes for user sign-off.
---

# Selective Stager Skill

## Overview
This skill operationalizes AGYToolkit's Selective Staging Gate. It prevents accidental inclusion of unverified changes, test artifacts, or scratch scripts by enforcing explicit, file-level staging and providing transparent diff summaries for user review.

## Operational Protocol

1. **Pre-Staging Verification**:
   - Verify that all affected tests pass 100% in an isolated environment.
   - Run `git status` to identify modified, added, and untracked files.

2. **Targeted Staging**:
   - Never run blanket `git add .` or `git add -A`.
   - Stage files explicitly by path (`git add path/to/file1.ts path/to/file2.ts`).
   - If a file contains both verified and in-progress changes, stage individual hunks using patch mode (`git add -p`).

3. **Staged Diff Review**:
   - Run `git diff --cached` to verify the exact staged content.
   - Run `git diff` to ensure unstaged changes are cleanly separated.

4. **Sign-Off Presentation**:
   - Present a structured summary of staged files and purpose to the user.
   - Await explicit user authorization before proceeding to commit.

## Quality Gate & Verification Checklist
- [ ] No unverified or failing code staged.
- [ ] No temporary, scratch, or credential files staged.
- [ ] Staged diff verified via `git diff --cached`.
- [ ] Structured summary presented to user with zero emojis.
