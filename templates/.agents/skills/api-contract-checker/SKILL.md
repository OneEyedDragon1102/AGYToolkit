---
name: api-contract-checker
description: Validates API schemas, OpenAPI specifications, DTO backward-compatibility, and serialization contracts.
---

# API Contract Checker Skill

## Overview
This skill audits HTTP APIs, WebSocket interfaces, and RPC protocols for contract fidelity. It verifies that data transfer objects (DTOs), serialization properties, and status codes conform to published specifications and avoid breaking changes.

## Operational Protocol

1. **Schema Extraction & Diffing**:
   - Extract current API specifications (OpenAPI / Swagger JSON, JSON Schema, or Protobuf definitions).
   - Compare new proposed endpoints or DTO changes against the existing contract.

2. **Breaking Change Detection**:
   - Flag forbidden breaking changes on existing endpoints:
     - Removing or renaming an existing field in a response.
     - Adding a mandatory (`required: true`) field to an existing request.
     - Altering field types (e.g., integer to string) or date formatting patterns.
     - Removing supported HTTP verbs or changing status codes.

3. **Validation & Deserialization Audit**:
   - Ensure all incoming parameters use strict validation constraints (`@Valid`, `@NotNull`, Zod schemas).
   - Verify handling of unknown properties (either explicitly ignored or rejected based on security posture).

4. **Documentation Sync**:
   - Ensure OpenAPI annotations, schema examples, and generated documentation reflect the implemented behavior.

## Quality Gate & Verification Checklist
- [ ] No unversioned breaking changes introduced to existing public API endpoints.
- [ ] Inbound payloads protected by strict validation schemas.
- [ ] All response status codes and error payloads documented.
- [ ] Output report formatted cleanly with zero emojis.
