---
name: node-mcp-builder
description: Builds Model Context Protocol (MCP) servers and tools using TypeScript and the official @modelcontextprotocol/sdk.
---

# Node MCP Builder Skill

## Overview
This skill guides the construction of Model Context Protocol (MCP) servers for exposing internal APIs, automation harnesses, and filesystem utilities to AI agents. It standardizes transport layers (STDIO and SSE), JSON Schema tool definitions, and robust error responses.

## Operational Protocol

1. **Protocol Transport Setup**:
   - Initialize the `Server` instance from `@modelcontextprotocol/sdk/server/index.js`.
   - Configure transport: `StdioServerTransport` for local subprocess communication or Express/Fastify SSE for remote endpoints.

2. **Tool Definition & Parameter Schemas**:
   - Register tools via `server.setRequestHandler(ListToolsRequestSchema, ...)`.
   - Provide explicit parameter schemas using JSON Schema or Zod with detailed field descriptions.
   - Design parameters to accept strongly-typed, minimal inputs.

3. **Tool Call Execution & Error Handling**:
   - Implement `CallToolRequestSchema` handler with exhaustive `switch/case` on tool names.
   - Enclose tool execution in `try...catch` blocks. Return structured MCP tool error objects (`isError: true`, content text describing the precise failure) rather than throwing unhandled exceptions.

4. **Resource Management**:
   - Ensure external client handles (HTTP clients, database pools, browser contexts) are gracefully terminated on process SIGINT/SIGTERM.

## Quality Gate & Verification Checklist
- [ ] Tool parameters fully validated with JSON Schema or Zod.
- [ ] Errors returned gracefully via MCP error responses without crashing the server process.
- [ ] STDIO transport emits zero non-MCP logs to stdout (use stderr for internal debugging).
- [ ] TypeScript compilation passes cleanly under strict mode.
- [ ] Zero emojis in code or tool descriptions.
