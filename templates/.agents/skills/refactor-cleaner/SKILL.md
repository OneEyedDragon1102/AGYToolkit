---
name: refactor-cleaner
description: Conducts structural refactoring, dead-code removal, modularization of monolithic files, and anti-bloat sanitation.
---

# Refactor Cleaner Skill

## Overview
This skill guides the safe, incremental refactoring of existing codebases. It enforces structural code hygiene, splits monolithic files (>600 lines), removes obsolete dead code, and strips speculative comments without altering external behavioral contracts.

## Operational Protocol

1. **Safety Harness Verification**:
   - Verify that automated unit and integration tests exist and pass cleanly before starting any refactoring.
   - If tests are missing, author baseline characterization tests first.

2. **Monolithic File Decomposition**:
   - Identify files approaching or exceeding 600 lines.
   - Extract coherent domain sub-modules, helper functions, and distinct data transfer objects into separate, dedicated files.
   - Maintain single responsibility per module.

3. **Dead Code Elimination**:
   - Scan for unreferenced private methods, unused variables, dead branches, and commented-out legacy code blocks.
   - Remove unused imports and dependencies.

4. **Code Hygiene & Anti-Bloat**:
   - Strip narrative agent comments (e.g., "Now we handle this case..."). Keep only technical docstrings and explanations of non-obvious algorithms.
   - Scan for and eliminate all emojis from source code files and commit history.

5. **Post-Refactor Verification**:
   - Run complete test suite and linters to verify zero functional regressions.

## Quality Gate & Verification Checklist
- [ ] Existing automated test suite passes 100% before and after refactoring.
- [ ] No file in the refactored scope exceeds 600 lines.
- [ ] Zero dead code blocks or commented-out code retained.
- [ ] Zero emojis remain in code or comments.
