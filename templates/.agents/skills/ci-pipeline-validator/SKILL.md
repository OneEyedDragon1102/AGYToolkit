---
name: ci-pipeline-validator
description: Validates CI/CD workflow configurations (GitHub Actions, GitLab CI), ensures deterministic steps, and audits caching.
---

# CI Pipeline Validator Skill

## Overview
This skill audits continuous integration and deployment pipelines (such as `.github/workflows/`). It ensures that automated CI jobs execute deterministically, leverage dependency caching, run isolated quality gates, and prevent pipeline failures before pull requests are opened.

## Operational Protocol

1. **Workflow File Inspection**:
   - Locate and parse workflow definitions (`.github/workflows/*.yml` or `.gitlab-ci.yml`).
   - Validate YAML syntax and action version pinning (pin specific commit SHA or minor release).

2. **Quality Gate Alignment**:
   - Verify pipeline runs:
     - Branch enforcement check.
     - Anti-bloat check.
     - Linter & formatting checks.
     - Isolated test suite execution.
     - Coverage report validation (80%+ threshold).

3. **Performance & Caching Optimization**:
   - Verify dependency caching: `actions/cache` or setup action caching for Maven (`~/.m2`), npm (`~/.npm`), or pip (`~/.cache/pip`).
   - Eliminate unnecessary duplicate compilation steps.

4. **Security & Permission Hardening**:
   - Audit `permissions:` block. Enforce minimum viable token permissions (`contents: read`, `pull-requests: write` only when necessary).
   - Ensure secrets are referenced through repository secrets, never exposed in workflow steps.

## Quality Gate & Verification Checklist
- [ ] Workflow YAML is syntactically valid and lint-clean.
- [ ] Pipeline mirrors local verification steps (test, coverage, anti-bloat).
- [ ] Minimum viable permissions configured for `GITHUB_TOKEN`.
- [ ] Zero emojis in workflow file comments.
