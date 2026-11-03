# AGYToolkit CI/CD Governance & PR Review Bot

`AGYToolkit` enforces automated, zero-cost CI/CD quality gates on GitHub Actions to ensure that all code merged into the repository is verified across operating systems, free of AI bloat, and strictly governed.

---

## 1. 5-Job Concurrent CI Pipeline (`ci.yml`)

The primary CI pipeline runs automatically on all pushes and pull requests across a cross-platform matrix:

| Job | Platform | Purpose |
| :--- | :--- | :--- |
| **`test-matrix`** | Ubuntu, Windows, macOS x Python 3.10, 3.12 | Runs all unit and concurrency tests with coverage enforcement. |
| **`doctor-and-scaffold`** | Ubuntu | Validates `agy-toolkit doctor --strict` and tests project scaffolding. |
| **`anti-bloat-sentinel`** | Ubuntu | Scans codebase for emojis and ensures no file exceeds 600 lines. |
| **`package-and-smoke`** | Ubuntu | Builds sdist and wheel packages and runs CLI smoke tests. |
| **`git-discipline`** | Ubuntu | Enforces branch discipline (no direct commits to `main`). |

---

## 2. Autonomous PR Review Bot (`pr-review.yml`)

The **PR Review Bot** runs automatically on every Pull Request (`opened`, `synchronize`, `reopened`), evaluates the changes, and posts/updates a sticky Markdown diagnostic card directly on the PR thread.

### Key Capabilities
1. **Sticky Single Comment**: Uses the hidden HTML tag `<!-- AGYToolkit-PR-Review-Bot -->` to update its existing comment on subsequent pushes instead of creating comment clutter.
2. **Multi-Gate Aggregation**:
   - **Environment Health**: Checks host toolchains, rules, and hook script parity.
   - **Anti-Bloat Diff Audit**: Inspects git diff for emojis in code or monolithic file dumps (>600 lines).
   - **Memory Budget**: Verifies `active-session.md` (1 KB cap) and `decisions.md` (3 KB cap).
   - **Test Results**: Confirms full test suite pass status.
3. **Zero Cost**: Built entirely with standard GitHub Actions runners and the built-in free `GITHUB_TOKEN`.

---

## 3. Local PR Review CLI

You can run the PR review engine locally before pushing:

```bash
# Preview the PR review report card in terminal
agy-toolkit pr-review --base origin/main

# Output report card to a file
agy-toolkit pr-review --base origin/main --output pr_report.md

# Enforce strict exit code (non-zero on any failure)
agy-toolkit pr-review --base origin/main --strict
```
