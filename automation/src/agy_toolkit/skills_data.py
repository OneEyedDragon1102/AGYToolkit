"""AGYToolkit Skills Catalog Metadata.

Defines the 28 progressive SDLC skills organized across 5 engineering tracks.
"""

SKILL_TRACKS = {
    "Track A: Planning & Architecture": [
        ("adr-architect", "Documents architecture decision records with trade-off matrices"),
        ("plan-approval-gate", "Enforces plan-approval gate before code modifications"),
        ("task-decomposer", "Decomposes complex user epics into atomic tasks"),
        ("context-budgeter", "Manages token budgets and offloads volatile data"),
        ("telemetry-logger", "Structures execution logs and cross-agent handoffs"),
        ("handbook-enforcer", "Enforces repository guidelines and coding rules"),
    ],
    "Track B: TDD & Implementation": [
        ("tdd-spring-boot", "Red-Green-Refactor TDD for Java 23 / Spring Boot"),
        ("tdd-node-ts", "Red-Green-Refactor TDD for Node.js / TypeScript"),
        ("tdd-python", "Isolated Python 3.12 TDD in virtual environments"),
        ("spring-service-generator", "Generates Hexagonal Architecture Spring Boot services"),
        ("node-mcp-builder", "Builds MCP servers and tools using TypeScript SDK"),
        ("ui-component-builder", "Builds accessible, responsive UI components"),
        ("refactor-cleaner", "Structural refactoring and modularization (<600 lines)"),
    ],
    "Track C: Review & Quality Gates": [
        ("code-reviewer", "Production-grade code review on git diffs"),
        ("anti-bloat-linter", "Scans for emojis, chatter, and monolithic files"),
        ("security-scanner", "Audits for credentials, OWASP vulnerabilities, and CVEs"),
        ("coverage-verifier", "Enforces mandatory 80%+ test coverage threshold"),
        ("concurrency-auditor", "Audits multi-threaded code and race conditions"),
        ("api-contract-checker", "Validates API schemas and DTO compatibility"),
    ],
    "Track D: Git, Staging & CI/CD": [
        ("commit-craft", "Drafts atomic Conventional Commits"),
        ("branch-manager", "Governs feature branch workflows and isolation"),
        ("selective-stager", "Granular staging and sign-off verification"),
        ("release-packager", "SemVer calculation, changelog generation, and packaging"),
        ("ci-pipeline-validator", "Validates CI/CD workflow configurations"),
    ],
    "Track E: Meta-Framework & Extensibility": [
        ("agy-inspector", "Audits AGY tools, skills, rules, and MCP servers"),
        ("skill-author", "Authors project-specific domain skills on demand"),
        ("agent-author", "Authors project-specific specialist subagents on demand"),
        ("workspace-doctor", "Diagnoses workspace dependencies and build toolchains"),
    ],
}
