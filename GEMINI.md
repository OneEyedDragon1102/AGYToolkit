# AGYToolkit Project Rules & Guidelines

Welcome to **AGYToolkit**. This repository is the Sovereign Multi-Agent AI Development Framework and SDLC Operating System for Google Antigravity (AGY).

## Primary Tech Stack Alignment

* **Managed Project Development (Core Applications)**:
  - **Node.js / TypeScript**: MCP servers, Puppeteer automation, Fastify/Express sidecars.
  - **Java Spring Boot**: Enterprise backend services, quant trading pipelines, scheduled engines.
* **Testing & Framework Automation**:
  - **Python 3.12**: Verification test suites, diagnostic CLI, and computer vision harnesses.
  - **PowerShell 7+ / Bash**: Cross-platform lifecycle hooks and quality gate scripts.

## Mandatory Development Workflow Rules

Every contributor and agent working in this repository MUST strictly follow these rules:

1. **Atomic Commits (No Large Chunks)**:
   - Commits must be small, focused, and bite-sized. Never bundle multiple unrelated features or wholesale rewrites into a single commit.

2. **Mandatory Isolated Verification & Testing**:
   - Every change must be verified, tested, and reviewed in an isolated environment before staging.
   - Use dedicated virtual environments/sandboxes:
     - Node: isolated `npm test` or mock runner.
     - Java Spring Boot: isolated Maven builds (`mvn test`).
     - Python: dedicated `.venv` and test sandbox (`unittest`).
     - Subagents: AGY workspace isolation (`Workspace: 'branch'` or `'share'`).
   - All tests in the relevant test suites must pass cleanly with 80%+ test coverage.

3. **Feature Branching & Commit Conventions**:
   - All work must be conducted on branches named `feature/<feature-name>` branched from the latest `main`.
   - Never commit directly to `main`.
   - Commit messages must be minimal and adhere to Conventional Commits (e.g., `feat(hooks): add plan-approval gate`, `test(hooks): add branch enforcement tests`).

4. **Staging & Final User Review Gate**:
   - Only stage (`git add`) the exact diffs that have been verified, reviewed, and tested.
   - Leave unstaged anything unverified or in-progress.
   - Present staged diffs clearly to the user for final review and approval before committing.

## Anti-Bloat Sentinel Rules (Zero AI Clutter)

To ensure high-signal, enterprise-grade code quality:
1. **Zero Emojis in Code**: No emojis in source code files, logs, or comments (emojis are permitted only in markdown badges/visual UI summaries).
2. **No Monolithic Single-File Dumps**: Code must be modularized into appropriate packages, classes, and helper modules.
3. **No Conversational Comments**: Comments must be concise technical documentation only. Prohibit narrative agent chatter (e.g., "Now we do this...", "Let's make sure that...").
4. **Plan-Approval Gate**: No code changes without an explicit, approved implementation plan.
