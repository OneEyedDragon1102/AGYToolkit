# Getting Started with AGYToolkit

## Overview

AGYToolkit is the sovereign multi-agent software development lifecycle (SDLC) framework and operating system for Google Antigravity (AGY). It provides deterministic governance, test-driven development (TDD) guardrails, a 15-agent specialist matrix, 28 progressive skills, and lifecycle hooks that keep autonomous agent teams aligned, verifiable, and free of AI clutter.

---

## Prerequisites

- **Operating System**: Windows 11 / 10, macOS, or Linux.
- **Python**: Version 3.12 (minimum 3.10) with `venv` support.
- **Node.js**: Version 20.x or later (for MCP servers and TypeScript projects).
- **Java**: JDK 21 or 23 with Apache Maven 3.9+ (for Spring Boot projects).
- **Git**: Version 2.40+ installed and configured.
- **Google Antigravity (AGY)**: Antigravity IDE or AGY CLI (`agy`).

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/OneEyedDragon1102/AGYToolkit.git
cd AGYToolkit
```

### 2. Configure Python Virtual Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install AGYToolkit in Editable Mode
```bash
pip install -e .
```

Verify installation:
```bash
agy-toolkit --list-tools
agy-toolkit --list-agents
agy-toolkit --list-skills
```

---

## Provisioning a New or Existing Project

To govern any project with AGYToolkit, use the `init` command. This scaffolds the complete `.agents/` runtime, memory architecture, lifecycle hooks, and project rules directly into the target project root without polluting it with unused domain code.

### Command Syntax
```bash
agy-toolkit init [target-path] [--name <project-name>] [--stack <stack>] [--mode <mode>]
```

### Parameters
- `target-path`: Destination directory (defaults to current directory `.`).
- `--name`: Name of the project (defaults to the folder name).
- `--stack`: Primary technology stack:
  - `spring-boot`: Java 23, Spring Boot 3.4+, Maven, Hexagonal Architecture.
  - `node-ts`: Node.js, TypeScript, Vitest, Fastify/Express, MCP.
  - `python`: Python 3.12, `.venv`, `unittest`, PEP 8.
- `--mode`: Development mode:
  - `feature`: Full SDLC governance (Plan -> TDD -> Implement -> Review -> Staging).
  - `spike`: Rapid exploration on an isolated branch with relaxed plan gates.
  - `quickfix`: Targeted bug fixing and direct test verification.

### Example
```bash
agy-toolkit init ../my-service --name order-service --stack spring-boot --mode feature
```

---

## Updating an Existing Downstream Project

As AGYToolkit releases improvements to its 28 skills, 15 agent prompts, or lifecycle hook scripts, existing projects can pull these updates non-destructively:

### Command Syntax
```bash
agy-toolkit update [target-path] [--dry-run] [--force-rules] [--json]
```

### Parameters
- `target-path`: Target project directory (defaults to current directory `.`).
- `--dry-run`: Preview planned updates without writing to disk.
- `--force-rules`: Force overwrite `GEMINI.md` and `AGENTS.md` rules with latest blueprints (by default, custom rules are strictly preserved).
- `--json`: Output structured JSON update report.

### Example
```bash
# Non-destructively update skills, agents, and hooks in an existing repo
agy-toolkit update ../order-service

# Preview updates in dry-run mode
agy-toolkit update ../order-service --dry-run
```

---

## Structure Injected into Target Workspaces

When `agy-toolkit init` runs, it creates the following structure:

```text
my-service/
├── .agents/
│   ├── agents/                   # 15 Universal Specialist Subagents
│   ├── hooks/                    # Lifecycle hook scripts (PS1 and Bash)
│   ├── hooks.json                # PreToolUse, PostToolUse, SessionStart event triggers
│   ├── skills/                   # 28 Progressive SDLC Skills
│   └── memory/                   # Dual-tier memory system
│       ├── active-session.md     # (Gitignored) Local working memory (<= 1 KB)
│       ├── decisions.md          # (Committed) Permanent architectural decisions (<= 3 KB)
│       ├── volatile-bus/         # (Gitignored) Ephemeral logs and subagent dumps
│       └── sessions/             # (Committed) Archived session summaries
├── GEMINI.md                     # Project-specific rules and coding standards
├── AGENTS.md                     # Role descriptions and operational protocols
└── .gitignore                    # Auto-configured to ignore local memory
```

---

## Operational Workflow in AGY

1. **Open Target Workspace in AGY**:
   - Launch the Antigravity IDE or run `agy` in your target directory.
2. **SessionStart Hook**:
   - Automatically loads `active-session.md` and displays the active operational mode, target branch, and active goals.
3. **Plan-Approval Gate**:
   - Before writing code, the agent generates an implementation plan artifact.
   - You review the plan and click **Proceed** to authorize execution.
4. **Isolated Branch Execution**:
   - Feature development runs on `feature/<name>` branches. Direct commits to `main` are blocked by hooks.
5. **Quality Gates & Review**:
   - TDD execution verifies tests before code.
   - `anti-bloat-check` blocks emojis, narrative comments, and monolithic files (>600 lines).
   - `code-reviewer` reviews staged diffs.
6. **Compaction Defense & Auto-Compaction**:
   - On `PostToolUse`, `auto-compact-memory.ps1` evaluates budget thresholds. When approaching limits (>85%), active sessions are archived to `sessions/` and oldest decisions are evicted to `docs/adr/decisions-history.md`.
   - Running `/compact` retains all decisions and working state cleanly because volatile data has been offloaded to `.agents/memory/volatile-bus/`.

---

## Governance & Diagnostic CLI Commands

AGYToolkit provides essential CLI tools for environment audits, machine-wide installation, and memory management:

### 1. Health & Diagnostic Audit (`doctor`)
Runs a deep diagnostic check of installed toolchains (Python, Node.js, JDK, Maven, Git), governance rules, hook scripts, and memory limits:
```bash
agy-toolkit doctor

# Output in JSON format
agy-toolkit doctor --json

# Fail with non-zero exit code on any warning or failure (for CI/CD pipelines)
agy-toolkit doctor --strict
```

### 2. Global Machine-Wide Installation (`link-global`)
Mounts all 28 skills and 15 agents into `~/.gemini/config/` so any project opened in Antigravity can discover them:
```bash
agy-toolkit link-global

# Preview mounts without writing
agy-toolkit link-global --dry-run
```

### 3. Memory & Event Bus Management (`memory` & `bus`)
Inspect memory budgets, flush active session context, auto-compact memory, and pass structured inter-agent messages:
```bash
# Check memory budget metrics
agy-toolkit memory status

# Auto-compact working session and archive oldest decisions (85% threshold)
agy-toolkit memory auto-compact

# Preview auto-compaction and projections without writing
agy-toolkit memory auto-compact --dry-run

# Output auto-compaction report in JSON format
agy-toolkit memory auto-compact --json

# Flush working memory and archive state to sessions/
agy-toolkit memory flush

# Record an architectural decision
agy-toolkit memory record --category ARCH --decision "Use Hexagonal Architecture."

# Publish an event to the volatile bus
agy-toolkit bus send --topic review --sender code-reviewer --recipient orchestrator --payload '{"status": "PASS"}'

# List active events on the volatile bus
agy-toolkit bus list

# Stream events in real-time until timeout or completion
agy-toolkit bus watch --topic review --timeout 30
```

### 4. Autonomous Swarm Pipeline Choreography (`swarm`)
Orchestrate multi-step DAG workflows across specialist subagents over the volatile event bus:
```bash
# List available blueprint workflows
agy-toolkit swarm pipelines

# Launch a new pipeline run with stack specialization
agy-toolkit swarm run feature-sdlc --stack spring-boot --context '{"issue": 101}'

# Query the real-time execution status card of a pipeline run
agy-toolkit swarm status <run_id>

# Query status in machine-readable JSON format
agy-toolkit swarm status <run_id> --json

# List all active and historical pipeline runs
agy-toolkit swarm list

# Advance a step and trigger downstream dependency unlocks
agy-toolkit swarm advance <run_id> --step plan --status COMPLETED --result '{"spec": "approved"}' --claimer architect

# Cancel an active run
agy-toolkit swarm cancel <run_id> --reason "User requested stop"

# Start autonomous background swarm worker daemon
agy-toolkit swarm worker

# Execute a single atomic worker claim-and-advance sweep
agy-toolkit swarm worker --run-once
```

### 5. Native Antigravity MCP Server (`mcp`)
Run the standard I/O JSON-RPC Model Context Protocol (MCP) server or export static schemas:
```bash
# Start native Antigravity MCP server over stdio (16 native tools)
agy-toolkit mcp

# Export static tool schemas for auto-discovery
agy-toolkit mcp --export-schemas .agents/mcp/agy-toolkit/
```

For configuration details and tool parameter schemas, refer to the [Native Antigravity MCP Server Guide](mcp_server.md).
