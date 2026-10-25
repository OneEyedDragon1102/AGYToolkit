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
6. **Compaction Defense**:
   - When the context window fills, running `/compact` retains all decisions and working state cleanly because volatile data has been offloaded to `.agents/memory/volatile-bus/`.
