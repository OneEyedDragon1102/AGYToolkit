---
name: coverage-verifier
description: Inspects test execution metrics and enforces the mandatory 80%+ line and branch coverage threshold before staging.
---

# Coverage Verifier Skill

## Overview
This skill measures and validates test coverage across the workspace. It enforces AGYToolkit's mandatory policy requiring 80%+ line and branch coverage for newly introduced or modified production code before staging.

## Operational Protocol

1. **Coverage Tool Invocation**:
   - Java / Spring Boot: Execute JaCoCo coverage runner (`mvn clean test jacoco:report`).
   - Node / TypeScript: Execute Vitest/Jest coverage (`npm test -- --coverage` or `npx vitest run --coverage`).
   - Python: Execute pytest-cov (`.venv/bin/python -m pytest --cov=src`).

2. **Metric Extraction & Analysis**:
   - Extract Line Coverage % and Branch Coverage % from generated reports (`jacoco.xml`, `coverage-summary.json`, `.coverage`).
   - Identify uncovered blocks, unexercised error branches, and untested exception handlers.

3. **Coverage Deficit Remediation**:
   - If coverage falls below 80%, pinpoint the specific unexercised lines.
   - Instruct the appropriate engineering agent or test specialist to author targeted edge-case unit tests.

4. **Gate Determination**:
   - Pass: Overall and changed-line coverage >= 80%.
   - Block: Coverage < 80% with explicit missing branch report.

## Quality Gate & Verification Checklist
- [ ] Both line and branch coverage meet or exceed 80%.
- [ ] No critical error-handling paths left untested.
- [ ] Coverage reports generated within isolated build directories.
- [ ] Report outputs concise technical metrics with zero emojis.
