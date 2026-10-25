---
name: release-packager
description: Prepares release artifacts, computes semantic version bumps, updates changelogs, and builds distribution packages.
---

# Release Packager Skill

## Overview
This skill automates the preparation of production release candidates and distributable packages. It enforces Semantic Versioning (SemVer), synthesizes Conventional Commit histories into changelogs, and validates binary/library packaging.

## Operational Protocol

1. **Semantic Version Calculation**:
   - Inspect git log since previous release tag.
   - Increment PATCH (`x.y.Z`) for backward-compatible bug fixes (`fix:`).
   - Increment MINOR (`x.Y.z`) for backward-compatible features (`feat:`).
   - Increment MAJOR (`X.y.z`) for breaking changes (`BREAKING CHANGE:`).

2. **Changelog Generation**:
   - Synthesize commit log into grouped release notes:
     - Features
     - Bug Fixes
     - Performance Improvements
     - Breaking Changes & Migration Steps
   - Append to `CHANGELOG.md` with version header and release date.

3. **Packaging Build & Verification**:
   - Maven: `mvn clean package -DskipTests=false`
   - NPM: `npm pack --dry-run` or `npm run build`
   - Python: `python -m build`
   - Verify distribution bundle contains expected binaries, manifests, and excludes source scratch files.

4. **Tagging Protocol**:
   - Propose annotated git tag (`vX.Y.Z`) with release summary.

## Quality Gate & Verification Checklist
- [ ] Version bump strictly conforms to SemVer rules.
- [ ] Automated tests pass before package compilation.
- [ ] CHANGELOG.md updated with all customer-impacting changes.
- [ ] Zero emojis in changelog or release notes.
