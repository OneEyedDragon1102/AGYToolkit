---
name: adr-architect
description: Documents architecture decision records (ADRs) and system designs with structured trade-off analysis and Mermaid diagrams. Use when documenting significant architectural choices.
---

# ADR Architect Skill

## Overview
This skill provides standard operating procedures for recording Architectural Decision Records (ADRs) and structural system designs. Every significant technical choice, library selection, or data flow pattern must be recorded in an immutable, version-controlled ADR.

## Operational Protocol

1. **Context & Problem Statement**:
   - Clearly define the business context, technical requirements, and underlying constraints.
   - Outline the problem without prematurely dictating the solution.

2. **Decision Drivers**:
   - List key architectural drivers (e.g., performance, latency, developer velocity, data integrity, security).

3. **Considered Options & Trade-Off Analysis**:
   - Compare at least two viable alternatives.
   - Construct a trade-off matrix analyzing pros, cons, and operational risks.

4. **Decision Outcome**:
   - State the chosen option unambiguously.
   - Detail the justification and rationale behind the decision.

5. **Consequences & Mitigations**:
   - Positive impacts (benefits realized).
   - Negative impacts (technical debt, trade-offs accepted, migration overhead).
   - Planned mitigations for negative impacts.

6. **Structural Visualization**:
   - Generate Mermaid diagrams (flowcharts, sequence diagrams, or class diagrams) illustrating data flows or component boundaries.

## Quality Gate & Verification Checklist
- [ ] Stored in `docs/adr/` or project decision log with sequential numbering (e.g., `ADR-001-<slug>.md`).
- [ ] No marketing fluff or speculative assumptions; strictly technical analysis.
- [ ] Trade-off matrix includes concrete performance and operational characteristics.
- [ ] Validated Mermaid syntax rendering cleanly without errors.
- [ ] Zero emojis in file content.
