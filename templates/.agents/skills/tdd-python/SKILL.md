---
name: tdd-python
description: Drives Python 3.12 Test-Driven Development in isolated virtual environments using unittest, pytest, and mock fixtures.
---

# TDD Python Skill

## Overview
This skill executes Test-Driven Development (TDD) for Python 3.12 applications and automation harnesses. It ensures test isolation within a dedicated virtual environment (`.venv`), deterministic assertions, mock patching, and rapid execution.

## Operational Protocol

1. **Virtual Environment Isolation**:
   - Ensure execution uses the dedicated virtual environment interpreter (`.venv/bin/python` or `.venv\Scripts\python.exe`).
   - Set `PYTHONPATH` appropriately to resolve package imports without global installation side-effects.

2. **Phase 1: Red (Failing Test)**:
   - Create test case extending `unittest.TestCase` in `tests/test_<module>.py`.
   - Use `unittest.mock.patch` for external network, filesystem, or process dependencies.
   - Run runner (`.venv/bin/python -m unittest discover tests`) and verify test failure.

3. **Phase 2: Green (Implementation)**:
   - Implement minimal logic in `src/<package>/`.
   - Adhere strictly to PEP 8, type hints (`typing.Optional`, `typing.List`, `typing.Dict`), and immutable data models (`dataclasses`).
   - Execute test runner and confirm all tests pass.

4. **Phase 3: Refactor**:
   - Modularize helper routines, eliminate duplicated setup logic in tests using `setUp()` / `tearDown()`.
   - Ensure all open file handles and temp directories are cleanly closed/deleted.

## Quality Gate & Verification Checklist
- [ ] Tests execute within isolated `.venv`.
- [ ] Test runs in sub-second duration without blocking console pipes.
- [ ] 80%+ line coverage across domain modules.
- [ ] Zero emojis in test suites, docstrings, or production code.
