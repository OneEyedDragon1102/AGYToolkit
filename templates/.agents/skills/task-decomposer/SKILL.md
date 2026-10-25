---
name: task-decomposer
description: Decomposes complex user epics and feature requests into atomic, verifiable, and bite-sized development tasks suitable for single-commit execution.
---

# Task Decomposer Skill

## Overview
This skill breaks down large engineering initiatives into small, atomic tasks that adhere to the Single Responsibility Principle. Decomposed tasks prevent monolithic pull requests, minimize context window bloat, and ensure deterministic verification at each milestone.

## Operational Protocol

1. **Epic Analysis**:
   - Ingest user requirements and delineate technical boundaries (frontend, backend, persistence, infrastructure).
   - Identify implicit requirements: schema changes, error handling, backward compatibility.

2. **Atomic Slicing**:
   - Break tasks down such that each task modifies or introduces no more than 1-3 tightly coupled files.
   - Each task must have its own isolated test specification and verification gate.

3. **Dependency Graph Construction**:
   - Establish execution order: Shared types/schemas -> Persistence -> Domain logic -> API/Controllers -> UI -> Integration.
   - Flag parallelizable tasks suitable for subagent delegation.

4. **Task Specification Output**:
   - For each subtask, record:
     - Target files to touch or create.
     - Verification command (e.g., `mvn test -Dtest=...`, `npm test -- ...`).
     - Commit message template following Conventional Commits.

## Quality Gate & Verification Checklist
- [ ] No single task estimated at over 150 lines of changed code.
- [ ] Every task has a runnable test target defined.
- [ ] Dependencies between tasks are strictly acyclic.
- [ ] Output formatted as clear markdown checklist with zero emojis.
