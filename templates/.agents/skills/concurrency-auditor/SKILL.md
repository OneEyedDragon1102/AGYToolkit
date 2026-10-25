---
name: concurrency-auditor
description: Audits multi-threaded code, asynchronous promises, and race conditions for thread-safety, deadlocks, and connection leaks.
---

# Concurrency Auditor Skill

## Overview
This skill investigates concurrent, asynchronous, and multi-threaded logic. It ensures safe shared-state management, prevents deadlocks and race conditions, and guarantees resource handle reclamation in high-throughput engines.

## Operational Protocol

1. **Shared Mutable State Inspection**:
   - Java: Inspect state variables across `@Service`, `@Component`, and scheduled jobs. Ensure classes are stateless or utilize atomic references (`AtomicInteger`, `ConcurrentHashMap`).
   - Node / TypeScript: Inspect global singletons and event loops. Detect unbounded concurrency (`Promise.all` over unthrottled collections) and apply chunking or worker pools (e.g., `p-limit`).
   - Python: Audit `asyncio` loops, thread pools, and shared queues.

2. **Locking & Deadlock Prevention**:
   - Verify consistent lock acquisition ordering across nested synchronized blocks or mutexes.
   - Forbid indefinite blocking; require timeouts on all locks and network waits.

3. **Resource Leak Detection**:
   - Verify that all opened database connections, sockets, file descriptors, and child processes are wrapped in `try-with-resources` (Java), `try...finally` (Node/TypeScript), or context managers (Python).

4. **Thread Pool & Executor Hygiene**:
   - Verify named thread factories for diagnostic visibility.
   - Enforce explicit shutdown hooks and queue capacity caps to prevent `OutOfMemoryError`.

## Quality Gate & Verification Checklist
- [ ] Zero unmanaged shared mutable state in singleton beans.
- [ ] All network and locking operations bounded by explicit timeouts.
- [ ] No unthrottled asynchronous batch operations.
- [ ] Clean concurrency audit report with zero emojis.
