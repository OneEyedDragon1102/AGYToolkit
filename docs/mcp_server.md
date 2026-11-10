# AGYToolkit Native Antigravity MCP Server (`agy-mcp`)

The **AGYToolkit MCP Server** provides native Model Context Protocol (MCP) integration over standard input/output (`stdio`), exposing core toolkit governance, dual-tier memory budgets, dynamic memory auto-compaction, and multi-agent volatile IPC capabilities directly to Google Antigravity agents.

---

## 1. Architecture Overview

```mermaid
flowchart TD
    subgraph HostEnvironment [Antigravity Runtime]
        Agent[Antigravity Chat / Agent]
        MCPClient[MCP Client stdio]
    end

    subgraph MCPServer [agy-toolkit mcp]
        Protocol[JSON-RPC 2.0 Engine: Protocol 2024-11-05]
        Dispatcher[Tool Dispatcher]
    end

    subgraph FrameworkEngine [AGYToolkit Modules]
        Doctor[doctor.py: Diagnostic Health Auditor]
        Memory[memory.py: Budget, Decision Registry & Auto-Compactor]
        Bus[bus.py: Volatile IPC Event Bus]
        Updater[updater.py: Downstream Synchronizer]
    end

    Agent <--> MCPClient
    MCPClient <-->|stdio JSON-RPC| Protocol
    Protocol --> Dispatcher
    Dispatcher --> Doctor
    Dispatcher --> Memory
    Dispatcher --> Bus
    Dispatcher --> Updater
```

The MCP server is implemented entirely using the Python standard library with **zero external dependencies**, adhering to the official **MCP 2024-11-05** protocol specification.

---

## 2. Configuration for Antigravity

To register AGYToolkit as an active MCP server in your Antigravity environment, add the following entry to your Antigravity configuration file (e.g. `~/.gemini/antigravity.json` or `.gemini/settings.json`):

```json
{
  "mcpServers": {
    "agy-toolkit": {
      "command": "agy-toolkit",
      "args": ["mcp"]
    }
  }
}
```

If running directly from the Python repository source without global packaging:

```json
{
  "mcpServers": {
    "agy-toolkit": {
      "command": "python",
      "args": ["-m", "agy_toolkit.cli", "mcp"]
    }
  }
}
```

---

## 3. Tool Catalog Reference

The MCP server exposes eight native tools:

### `agy_doctor`
* **Description**: Runs a diagnostic health check and governance audit on the environment.
* **Arguments**:
  - `strict` *(boolean, optional, default: `false`)*: Enforce strict zero-warning mode for CI/CD gates.
* **Output**: Formatted markdown audit report detailing toolchain, hook, and memory status.

### `agy_memory_status`
* **Description**: Queries memory budget consumption and cap thresholds.
* **Arguments**: None.
* **Output**: Byte usage and pass/fail thresholds for `active-session.md` (1 KB cap) and `decisions.md` (3 KB cap).

### `agy_memory_record`
* **Description**: Appends a binding architectural decision to `decisions.md` within budget.
* **Arguments**:
  - `decision` *(string, required)*: The architectural decision statement.
  - `category` *(string, optional, default: `"ARCH"`)*: Category prefix (e.g. `ARCH`, `GOV`, `DIST`, `BUS`, `TDD`).
* **Output**: Confirmation message with recorded entry.

### `agy_memory_compact`
* **Description**: Evaluates active session and architectural decision budgets, archiving bloated snapshots and offloading oldest decisions to cold storage.
* **Arguments**:
  - `threshold` *(number, optional, default: `0.85`)*: Compaction threshold ratio (0.0 - 1.0) above which auto-compaction is triggered.
  - `dry_run` *(boolean, optional, default: `false`)*: Preview compaction actions and byte projections without modifying files on disk.
* **Output**: Formatted auto-compaction report detailing bytes before/after, archive paths, and runtime advice for AGY agents.

### `agy_bus_send`
* **Description**: Publishes a structured JSON event envelope to the volatile multi-agent IPC bus.
* **Arguments**:
  - `topic` *(string, required)*: Channel topic name (e.g. `task-handoff`, `lint-alert`).
  - `source` *(string, required)*: Sender agent identifier.
  - `payload` *(object, required)*: Structured dictionary payload for the event.
  - `recipient` *(string, optional, default: `"*"`)*: Destination agent identifier.
  - `ttl_seconds` *(integer, optional, default: `3600`)*: Event time-to-live before expiration.
* **Output**: Created event ID, topic, and expiration details.

### `agy_bus_read`
* **Description**: Reads and lists active non-expired events from the volatile IPC bus.
* **Arguments**:
  - `topic` *(string, optional)*: Filter events by topic name.
  - `limit` *(integer, optional, default: `10`)*: Maximum number of events to return.
* **Output**: JSON array of matching event envelopes.

### `agy_bus_claim`
* **Description**: Atomically claims an event from the volatile bus to prevent duplicate processing by competing agents.
* **Arguments**:
  - `event_id` *(string, required)*: The unique ID of the event envelope to claim.
  - `claimer` *(string, required)*: Identifier of the claiming agent.
* **Output**: Claimed event payload or error if already claimed.

### `agy_update`
* **Description**: Non-destructively synchronizes the workspace's skills, agents, and hooks from latest blueprints while preserving custom rules and memory.
* **Arguments**:
  - `dry_run` *(boolean, optional, default: `false`)*: Preview changes without modifying the filesystem.
  - `force_rules` *(boolean, optional, default: `false`)*: Force refresh project rules (`GEMINI.md`, `AGENTS.md`) from templates.
* **Output**: Formatted summary report of refreshed components.

---

## 4. CLI Usage & Schema Export

### Starting the Server
Start the stdio JSON-RPC loop:
```bash
agy-toolkit mcp
```

### Exporting Static Schemas
To export static JSON tool definition files into an Antigravity MCP directory:
```bash
agy-toolkit mcp --export-schemas .agents/mcp/agy-toolkit/
```
Output:
```text
[AGYToolkit MCP] Exported 8 MCP tool schemas to .../.agents/mcp/agy-toolkit
  * agy_doctor.json
  * agy_memory_status.json
  * agy_memory_record.json
  * agy_memory_compact.json
  * agy_bus_send.json
  * agy_bus_read.json
  * agy_bus_claim.json
  * agy_update.json
```
