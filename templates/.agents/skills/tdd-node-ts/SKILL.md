---
name: tdd-node-ts
description: Implements Red-Green-Refactor test-driven development for Node.js and TypeScript services using Vitest, Jest, and Supertest.
---

# TDD Node & TypeScript Skill

## Overview
This skill executes Test-Driven Development (TDD) for TypeScript and Node.js applications. It enforces strict type safety, asynchronous error handling, mock isolation, and comprehensive coverage across services, MCP tools, and API routes.

## Operational Protocol

1. **Phase 1: Red (Failing Test First)**:
   - Create test file adjacent to target module or in `tests/` (e.g., `service.test.ts`).
   - Define test cases covering: valid payload handling, invalid schemas, boundary values, and rejected promises.
   - Run runner (`npm test -- service.test.ts` or `npx vitest run service.test.ts`) and confirm failure.

2. **Phase 2: Green (Minimal Implementation)**:
   - Implement target functions or classes in `src/`.
   - Ensure strict typing (`noImplicitAny`, explicit return types).
   - Validate inputs using Zod or TypeBox schemas.
   - Run test runner and confirm all tests pass.

3. **Phase 3: Refactor**:
   - Clean up helper abstractions, extract shared types, and ensure all async handles (timers, connections) are cleanly closed.
   - Re-run test runner to verify green state.

4. **Edge Case Matrix**:
   - Explicitly test: Network timeouts, partial JSON responses, missing environment variables, concurrency race conditions.

## Quality Gate & Verification Checklist
- [ ] Failing test written and verified before implementation.
- [ ] TypeScript compilation (`tsc --noEmit`) passes with zero errors.
- [ ] All async tests include clean assertions and proper `await` calls (no dangling promises).
- [ ] Test coverage exceeds 80% line and branch thresholds.
- [ ] Zero emojis in test suites.
