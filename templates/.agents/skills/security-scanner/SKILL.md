---
name: security-scanner
description: Audits codebases for credentials, API tokens, OWASP Top 10 vulnerabilities, insecure deserialization, and dependency CVEs.
---

# Security Scanner Skill

## Overview
This skill executes defensive security audits across source code, dependencies, and configuration manifests. It prevents accidental credential leaks, insecure deserialization, command injection, and known Common Vulnerabilities and Exposures (CVEs).

## Operational Protocol

1. **Secret & Credential Detection**:
   - Scan diffs for entropy patterns matching API keys, AWS credentials, private keys, database passwords, and JWT secrets.
   - Enforce usage of environment variables or secret management sidecars.

2. **Injection & Input Validation Audit**:
   - Inspect all external input entrypoints (HTTP routes, CLI args, file uploads).
   - Ensure parameterized queries for SQL, escaping for shell commands, and strict schema validation for JSON payloads.

3. **Dependency Vulnerability Assessment**:
   - Scan package manifests (`pom.xml`, `package.json`, `requirements.txt`).
   - Run native package audit commands (`npm audit`, `pip-audit`, `mvn dependency-check:check`) where available.

4. **Access Control & Serialization Verification**:
   - Verify proper authentication and authorization checks on protected routes.
   - Forbid dangerous deserialization routines (`pickle.loads` on untrusted data, raw Java object serialization).

## Quality Gate & Verification Checklist
- [ ] Zero plaintext secrets or private keys in the working tree or commit history.
- [ ] No unparameterized SQL queries or unescaped shell invocations.
- [ ] No high or critical CVEs present in newly introduced dependencies.
- [ ] Security report delivered with actionable remediation steps and zero emojis.
