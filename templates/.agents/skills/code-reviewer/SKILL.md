---
name: code-reviewer
description: Conducts rigorous, production-grade code reviews on git diffs focusing on correctness, security vulnerabilities, edge cases, and architectural cohesion.
---

# Code Reviewer Skill

## Overview
This skill provides a standardized framework for performing senior-level code reviews. It audits git diffs and staging candidates for logic defects, security vulnerabilities, race conditions, performance bottlenecks, and adherence to repository conventions.

## Operational Protocol

1. **Diff Ingestion & Scope Analysis**:
   - Inspect git diff (`git diff` or `git diff --cached`).
   - Validate that changes are strictly scoped to the stated task (atomic commit rule). Flag any unrelated modifications.

2. **Correctness & Edge Cases**:
   - Verify boundary conditions: null/undefined pointers, empty arrays, integer overflows, off-by-one errors.
   - Verify error handling: Are promises handled? Are checked exceptions wrapped or bubbled appropriately? Are resources closed?

3. **Security & Vulnerability Audit**:
   - Check for SQL injection, unvalidated user inputs, hardcoded secrets, unsafe deserialization, and path traversal vectors.

4. **Performance & Scalability**:
   - Detect N+1 query patterns, excessive memory allocations, unindexed lookups, or unthrottled loop iterations.

5. **Review Report Generation**:
   - Output structured review findings categorized by severity:
     - `BLOCKER`: Must be resolved before merge.
     - `WARNING`: Recommended improvement for maintainability.
     - `NOTE`: Non-blocking observation.
   - Include exact file paths and line numbers.

## Quality Gate & Verification Checklist
- [ ] Every modified file in the diff scrutinized.
- [ ] All blocker issues clearly explained with actionable remediation snippets.
- [ ] Feedback is strictly technical and constructive with zero conversational padding.
- [ ] Zero emojis in review report.
