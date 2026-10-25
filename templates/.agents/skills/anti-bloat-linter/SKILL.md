---
name: anti-bloat-linter
description: Scans modified files for AI-generated clutter, conversational comments, emojis, and files exceeding line thresholds.
---

# Anti-Bloat Linter Skill

## Overview
This skill operationalizes AGYToolkit's Anti-Bloat Sentinel standards. It acts as an automated quality gate scanning working trees and staged files for emojis, narrative chatter, monolithic code dumps, and speculative boilerplate.

## Operational Protocol

1. **Emoji Detection**:
   - Scan changed source files for Unicode ranges `\U00010000-\U0010ffff`, `\u2600-\u26ff`, and `\u2700-\u27bf`.
   - Any emoji found in code files, log strings, or comments triggers an immediate failure.

2. **File Size Boundaries**:
   - Inspect line count of each changed file.
   - Any file exceeding 600 lines is flagged for mandatory modularization.

3. **Conversational Comment Audit**:
   - Scan for phrases characteristic of verbose AI chatter (e.g., "Now we do this", "Let's make sure that", "Here we handle", "First, we import").
   - Strip conversational narratives; enforce concise technical docstrings explaining *why*, not *what*.

4. **Monolithic Dump Defense**:
   - Detect wholesale file rewrites when incremental diffs would suffice.
   - Reject unprompted additions of speculative abstractions or premature helper utilities.

## Quality Gate & Verification Checklist
- [ ] 0 emojis across all staged source code files and comments.
- [ ] 0 files exceeding 600 lines in the commit set.
- [ ] All comments conform to professional, technical API documentation standards.
- [ ] Clean report output with zero emojis.
