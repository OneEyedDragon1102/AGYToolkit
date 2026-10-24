# Agent Instructions for AGYToolkit

## Mission
You are collaborating on `AGYToolkit`, the Sovereign Multi-Agent AI Development Framework for Google Antigravity (AGY).

## Operational Protocol for AGY Agents

When performing any development task in this repository, you MUST follow this sequence:

1. **Branching**:
   - Ensure the working tree is clean and synced with `main`.
   - Switch to or create a dedicated feature branch: `feature/<feature-name>`.
   - Never commit directly to `main`.

2. **Atomic Development**:
   - Keep changes tightly scoped to the single task or tool at hand.
   - Do not make massive sweeping modifications or modify unrelated files.

3. **Isolated Testing & Verification**:
   - Run tests in an isolated environment (Node test runner, Maven test target, Python `.venv` test sandbox, or isolated subagent workspace).
   - Verify that all existing and new tests pass cleanly before staging.

4. **Selective Staging for User Review**:
   - Only `git add` the precise files and lines that are tested and ready.
   - Run `git status` and `git diff --cached` to verify what is staged.
   - Present a clear summary of staged changes to the user for final sign-off before committing.

5. **Commit Message Format**:
   - Use concise Conventional Commits: `<type>(<scope>): <short summary>`.
   - Example types: `feat`, `fix`, `test`, `docs`, `refactor`.

6. **Anti-Bloat Standards**:
   - Strictly avoid emojis in source code.
   - Prevent monolithic file accumulation.
   - Keep comments focused strictly on API contracts and non-obvious logic.
