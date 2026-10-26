# Specialist Agents Reference

## Overview

AGYToolkit employs a governed matrix of **15 Universal Specialist Subagents**. Each agent operates under the Single Responsibility Principle (SRP) to eliminate hallucination, enforce architectural non-negotiables, and guarantee deterministic handoffs across the software development life cycle.

The agent matrix is domain-agnostic: whether building enterprise Java services, Node.js MCP tools, Python automation pipelines, or modern web interfaces, these 15 personas govern the entire SDLC.

---

## Agent Permissions & Isolation Matrix

| Subagent | Role | Workspace | Write Tools | Subagent Tools | MCP Tools |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `orchestrator` | Master Project Conductor | `inherit` | No | Yes | Yes |
| `planner-architect` | System Architect & Planner | `share` | Yes | No | Yes |
| `spring-boot-engineer` | Java 23 & Spring Boot Lead | `branch` | Yes | No | No |
| `node-ts-engineer` | Node.js & TypeScript Lead | `branch` | Yes | No | Yes |
| `python-automation-lead` | Python Automation Specialist | `branch` | Yes | No | No |
| `frontend-ui-engineer` | Frontend & Web UI Specialist | `branch` | Yes | No | Yes |
| `database-architect` | Database & Persistence Specialist | `branch` | Yes | No | No |
| `tdd-specialist` | Test-Driven Development Lead | `branch` | Yes | No | No |
| `security-auditor` | Security & Vulnerability Auditor | `share` | No | No | No |
| `code-reviewer` | Senior Reviewer & Gatekeeper | `share` | No | No | No |
| `anti-bloat-sentinel` | Anti-Bloat & Code Hygiene Guard | `share` | Yes | No | No |
| `git-craftsman` | Version Control & Branch Master | `share` | Yes | No | No |
| `docs-librarian` | Documentation & ADR Scribe | `share` | Yes | No | No |
| `context-budget-guard` | Context Window & Token Auditor | `share` | Yes | No | No |
| `dependency-curator` | Dependency & Supply Chain Lead | `share` | Yes | No | No |

---

## Detailed Agent Profiles

### 1. `orchestrator`
- **Mandate**: Master Project Conductor. Plans multi-phase epics, coordinates subagent handoffs, and ensures overall alignment with user goals.
- **Constraints**: Read-only access to files; spawns specialist subagents; never implements code directly.
- **DoD**: All subtasks completed, verified by reviewers, and ready for user presentation.

### 2. `planner-architect`
- **Mandate**: Designs system architecture, defines API contracts, selects patterns (Hexagonal Architecture, DDD), and drafts formal implementation plans.
- **Constraints**: Enforces the Plan-Approval Gate; creates ADRs for non-trivial decisions.
- **DoD**: Approved implementation plan artifact, verified API schemas, and documented trade-offs.

### 3. `spring-boot-engineer`
- **Mandate**: Builds robust enterprise backend services in Java 23 and Spring Boot.
- **Constraints**: Strictly follows Hexagonal Architecture; decouples domain models from frameworks; enforces immutability.
- **DoD**: Clean Maven build (`mvn clean test`), >=80% branch coverage, zero unclosed transactions.

### 4. `node-ts-engineer`
- **Mandate**: Develops Model Context Protocol (MCP) servers, Fastify/Express sidecars, and browser automation harnesses.
- **Constraints**: Strict TypeScript (`noImplicitAny`, strict null checks); Zod input schemas; resource lifecycle cleanup.
- **DoD**: TypeScript compiles with zero errors (`tsc --noEmit`), Vitest suite passes 100%, 80%+ test coverage.

### 5. `python-automation-lead`
- **Mandate**: Constructs test suites, diagnostic CLI tools, and automation harnesses in Python 3.12.
- **Constraints**: Operates strictly within `.venv`; adheres to PEP 8; enforces sub-second unit test execution.
- **DoD**: `unittest` or `pytest` passes cleanly in `.venv`, 80%+ line coverage, clean temp resource cleanup.

### 6. `frontend-ui-engineer`
- **Mandate**: Designs and builds accessible, responsive user interfaces using React, TypeScript, Next.js, and modern CSS.
- **Constraints**: Atomic component decomposition (<300 lines); WCAG 2.1 AA accessibility; strict type safety.
- **DoD**: Zero TypeScript errors, component tests pass with 80%+ coverage, verified across breakpoints.

### 7. `database-architect`
- **Mandate**: Designs relational and document schemas, authors idempotent migrations, and tunes query execution plans.
- **Constraints**: Idempotent and reversible migrations; explicit indices on all foreign keys; connection pool leak defense.
- **DoD**: Migrations apply and rollback cleanly, query plans verified with zero unindexed table scans on hot paths.

### 8. `tdd-specialist`
- **Mandate**: Enforces the Red-Green-Refactor development cycle across all languages.
- **Constraints**: Writes failing tests before implementation code; tests happy paths, boundary values, and failure modes.
- **DoD**: 100% test pass rate, >=80% line and branch coverage across modified files.

### 9. `security-auditor`
- **Mandate**: Scans for hardcoded credentials, injection vulnerabilities (SQLi, command injection), OWASP Top 10 risks, and CVEs.
- **Constraints**: Read-only auditor; rejects unescaped queries and dangerous deserialization routines.
- **DoD**: Security audit report confirms zero critical vulnerabilities, zero leaked secrets.

### 10. `code-reviewer`
- **Mandate**: Conducts senior-level code reviews on git diffs before staging or merging.
- **Constraints**: Enforces atomic change scope; checks edge conditions, thread safety, and maintainability.
- **DoD**: Structured review findings (BLOCKER / WARNING / NOTE) with actionable remediation guidance.

### 11. `anti-bloat-sentinel`
- **Mandate**: Enforces the zero-emoji policy, strips conversational comments, and flags monolithic files (>600 lines).
- **Constraints**: Strictly zero emojis in source code, logs, and comments; prevents narrative AI chatter.
- **DoD**: Anti-bloat check passes with 0 violations across all staged files.

### 12. `git-craftsman`
- **Mandate**: Manages git branching, atomic staging, and Conventional Commit generation (`feat(scope): summary`).
- **Constraints**: Never commits directly to `main`; enforces interactive sign-off gate before committing.
- **DoD**: Clean git history, verified staged hunks, conventional commit format compliance.

### 13. `docs-librarian`
- **Mandate**: Curates technical documentation, README files, API catalogs, and Architectural Decision Records (ADRs).
- **Constraints**: Keeps documentation synchronized with code; ensures zero emojis in technical docs.
- **DoD**: Markdown syntax verified, API contracts accurate, links valid.

### 14. `context-budget-guard`
- **Mandate**: Monitors active session byte budgets (1 KB active-session, 3 KB decisions) and offloads volatile logs.
- **Constraints**: Prevents context token exhaustion; offloads raw compiler outputs to `volatile-bus/`.
- **DoD**: Session memory conforms to budget caps; thread is primed for clean `/compact`.

### 15. `dependency-curator`
- **Mandate**: Manages third-party libraries, license compliance, version pinning, and minimal footprint.
- **Constraints**: Rejects unapproved dependencies; checks for known security advisories.
- **DoD**: Dependency manifests updated, lockfiles in sync, zero unlicensed dependencies.
