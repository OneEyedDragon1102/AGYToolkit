# Google Antigravity (AGY) Core Tools Reference

This guide provides a comprehensive overview of the built-in core tools available in AGY.

---

## 1. File Manipulation

### `read_file`
- **Purpose**: Reads file content with token efficiency (max 800 lines or 45KB per call).
- **Parameters**: `Path` (required), `StartLine`, `EndLine`, `ByteOffset`.
- **Best Practice**: Use `StartLine` and `EndLine` to read only the necessary code snippets.

### `write_file`
- **Purpose**: Writes new files or appends to existing files. Automatically creates parent directories.
- **Parameters**: `Path` (required), `Content` (required), `Overwrite` (bool), `Append` (bool), `ArtifactMetadata` (for brain artifacts).

### `edit_file`
- **Purpose**: Applies targeted, exact-string replacements to existing files.
- **Parameters**: `Path`, `Target` (exact existing string with whitespace), `Replacement`.

---

## 2. Command Execution & Background Tasks

### `run_command`
- **Purpose**: Executes shell commands in PowerShell (Windows) or Bash (POSIX).
- **Key Parameters**:
  - `CommandLine`: Exact command string.
  - `WaitMsBeforeAsync`: Milliseconds before putting into background (500–10000ms).
  - `IsDaemon`: Set to `true` for long-running processes (e.g. dev servers, file watchers).
  - `toolSummary`: 2–5 word description.

### `manage_task`
- **Purpose**: Controls background processes.
- **Actions**:
  - `list`: Show running background tasks and TaskIds.
  - `status`: Retrieve task execution status and recent logs.
  - `send_input`: Stream standard input to an interactive running task.
  - `kill`: Terminate a background task.

---

## 3. Reactive Scheduling & Cron

### `schedule`
- **Purpose**: Triggers one-shot timers or recurring cron schedules that wake up the agent reactively.
- **Parameters**:
  - `DurationSeconds`: Wait duration for one-shot timer.
  - `CronExpression`: 5-field cron expression for recurring jobs.
  - `Prompt`: High-priority notification sent upon triggering.
  - `TimerCondition`: Early cancellation condition (`never`, `any`, or sender ID).

---

## 4. Multi-Agent Orchestration

### `define_subagent`
- **Purpose**: Dynamically defines a new subagent type at runtime.
- **Parameters**: `Name`, `Description`, `SystemPrompt`, `EnableWriteTools`, `EnableSubagentTools`, `EnableMCPTools`.

### `invoke_subagent`
- **Purpose**: Launches a subagent instance running in the background.
- **Parameters**:
  - `TypeName`: Agent type (`self`, `research`, `image-generator`, or user-defined).
  - `Role`: 2–5 word job title.
  - `Prompt`: Actionable task prompt.
  - `Workspace`: `inherit` (shared), `branch` (isolated git branch), `share` (git worktree).

### `send_message` & `manage_subagents`
- **Purpose**: Inter-agent messaging and swarm lifecycle management (`list`, `kill`, `kill_all`).

---

## 5. User Interaction & Research

### `ask_question`
- **Purpose**: Prompts the user with structured multiple-choice questions for requirement clarifications or design decisions.

### `search_web`
- **Purpose**: Live internet searches with domain prioritizing and citation synthesis.
