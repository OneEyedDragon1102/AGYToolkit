"""AGYToolkit Automated GitOps Lifecycle & Release Engine.

Enforces release quality gates, parses Conventional Commits, updates CHANGELOG.md,
synchronizes SemVer across package metadata, and creates atomic git tags.
"""

import datetime
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> "SemVer":
        clean = version_str.strip().lstrip("v")
        prerelease = None
        if "-" in clean:
            clean, prerelease = clean.split("-", 1)
        parts = clean.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid SemVer string: '{version_str}'")
        try:
            return cls(int(parts[0]), int(parts[1]), int(parts[2]), prerelease)
        except ValueError as ex:
            raise ValueError(f"Invalid SemVer integer parts in: '{version_str}'") from ex

    def bump(self, bump_type: str) -> "SemVer":
        bt = bump_type.lower()
        if bt == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        elif bt == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        elif bt == "major":
            return SemVer(self.major + 1, 0, 0)
        else:
            raise ValueError(
                f"Invalid bump type: '{bump_type}'. Expected 'patch', 'minor', or 'major'."
            )

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        return s


@dataclass
class ConventionalCommit:
    sha: str
    type: str
    scope: Optional[str]
    description: str
    breaking: bool = False
    raw_message: str = ""

    def format_bullet(self) -> str:
        scope_part = f"({self.scope})" if self.scope else ""
        breaking_flag = " [BREAKING]" if self.breaking else ""
        return f"- **{self.type}{scope_part}**: {self.description}{breaking_flag} (`{self.sha}`)"


CONVENTIONAL_REGEX = re.compile(
    r"^(?P<type>[a-zA-Z0-9_-]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)

CATEGORY_MAP: Dict[str, str] = {
    "feat": "Features",
    "feature": "Features",
    "fix": "Bug Fixes",
    "bugfix": "Bug Fixes",
    "perf": "Performance Improvements",
    "refactor": "Refactoring & Architecture",
    "docs": "Documentation",
    "test": "Testing & Quality Assurance",
    "tests": "Testing & Quality Assurance",
    "chore": "Maintenance & Dependencies",
    "ci": "CI/CD & Automation",
    "build": "Maintenance & Dependencies",
}


def _run_git_cmd(repo_path: Path, args: List[str]) -> Tuple[int, str, str]:
    """Execute git command within repository path."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as ex:
        return 1, "", str(ex)


def check_working_tree_clean(repo_path: Path) -> Tuple[bool, str]:
    """Verify that git working tree has no uncommitted tracked changes."""
    code, stdout, stderr = _run_git_cmd(repo_path, ["status", "--porcelain"])
    if code != 0:
        return False, f"Git status error: {stderr}"

    dirty_lines = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Allow untracked files if needed, but flag tracked modifications or staged items
        status_code = line[:2]
        if status_code != "??" and not line.endswith("decisions.md"):
            dirty_lines.append(line)

    if dirty_lines:
        return False, f"Uncommitted changes detected in working tree:\n" + "\n".join(
            f"  {l}" for l in dirty_lines
        )
    return True, "Working tree clean"


def check_release_branch(
    repo_path: Path, allowed_branches: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """Verify current branch is an authorized release branch."""
    allowed = allowed_branches or ["main", "master"]
    code, stdout, stderr = _run_git_cmd(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        return False, f"Unable to determine current branch: {stderr}"

    current = stdout.strip()
    if current not in allowed:
        return (
            False,
            f"Release must be executed from {allowed}. Current branch is '{current}'.",
        )
    return True, f"Branch '{current}' authorized for release"


def run_release_test_gate(repo_path: Path) -> Tuple[bool, str]:
    """Execute full test suite verification gate before cutting release."""
    env = os.environ.copy()
    src_dir = str(repo_path / "automation" / "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_dir

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "automation/tests"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            return False, f"Test gate failed:\n{proc.stderr}\n{proc.stdout}"
        return True, "Test gate passed cleanly"
    except Exception as ex:
        return False, f"Failed to execute test gate: {str(ex)}"


def get_latest_git_tag(repo_path: Path) -> Optional[str]:
    """Find most recent annotated or lightweight git tag."""
    code, stdout, _ = _run_git_cmd(repo_path, ["describe", "--tags", "--abbrev=0"])
    if code == 0 and stdout:
        return stdout.strip()
    return None


def get_git_commits_since(
    repo_path: Path, tag: Optional[str] = None
) -> List[Tuple[str, str]]:
    """Retrieve git commits (sha, subject) since previous tag or root."""
    args = ["log", "--pretty=format:%h|||%s"]
    if tag:
        args.append(f"{tag}..HEAD")
    code, stdout, _ = _run_git_cmd(repo_path, args)
    if code != 0 or not stdout:
        return []

    commits = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or "|||" not in line:
            continue
        sha, subject = line.split("|||", 1)
        commits.append((sha.strip(), subject.strip()))
    return commits


def parse_conventional_commit(sha: str, message: str) -> Optional[ConventionalCommit]:
    """Parse single commit subject line against Conventional Commits standard."""
    m = CONVENTIONAL_REGEX.match(message)
    if not m:
        return None
    type_str = m.group("type").lower()
    scope = m.group("scope")
    breaking = bool(m.group("breaking"))
    desc = m.group("desc").strip()
    return ConventionalCommit(
        sha=sha,
        type=type_str,
        scope=scope,
        description=desc,
        breaking=breaking,
        raw_message=message,
    )


def categorize_commits(
    commits: List[Tuple[str, str]],
) -> Tuple[Dict[str, List[ConventionalCommit]], List[Tuple[str, str]]]:
    """Group commits into conventional categories and uncategorized list."""
    categories: Dict[str, List[ConventionalCommit]] = {
        "Features": [],
        "Bug Fixes": [],
        "Performance Improvements": [],
        "Refactoring & Architecture": [],
        "Documentation": [],
        "Testing & Quality Assurance": [],
        "Maintenance & Dependencies": [],
    }
    uncategorized: List[Tuple[str, str]] = []

    for sha, msg in commits:
        parsed = parse_conventional_commit(sha, msg)
        if parsed:
            cat_name = CATEGORY_MAP.get(parsed.type, "Maintenance & Dependencies")
            categories.setdefault(cat_name, []).append(parsed)
        else:
            uncategorized.append((sha, msg))

    return categories, uncategorized


def generate_changelog_entry(
    version: str,
    date_str: str,
    categories: Dict[str, List[ConventionalCommit]],
    uncategorized: List[Tuple[str, str]],
) -> str:
    """Generate markdown changelog entry for a release."""
    lines = [f"## [v{version}] - {date_str}", ""]
    has_content = False

    for cat_name, items in categories.items():
        if items:
            has_content = True
            lines.append(f"### {cat_name}")
            for item in items:
                lines.append(item.format_bullet())
            lines.append("")

    if uncategorized:
        has_content = True
        lines.append("### Other Changes")
        for sha, msg in uncategorized:
            lines.append(f"- {msg} (`{sha}`)")
        lines.append("")

    if not has_content:
        lines.append("- Maintenance release and dependency updates.")
        lines.append("")

    return "\n".join(lines)


def get_current_project_version(repo_path: Path) -> str:
    """Read current version from pyproject.toml."""
    pyproject_file = repo_path / "pyproject.toml"
    if not pyproject_file.exists():
        raise FileNotFoundError(f"pyproject.toml not found in {repo_path}")

    text = pyproject_file.read_text(encoding="utf-8")
    m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        raise ValueError("Could not parse 'version' field from pyproject.toml")
    return m.group(1).strip()


def sync_version_metadata(repo_path: Path, new_version: str) -> List[Path]:
    """Update version across pyproject.toml, __init__.py, and mcp_server.py."""
    updated_files = []

    # 1. pyproject.toml
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        text = pyproject_file.read_text(encoding="utf-8")
        updated = re.sub(
            r'(version\s*=\s*["\'])([^"\']+)(["\'])',
            rf"\g<1>{new_version}\g<3>",
            text,
            count=1,
        )
        pyproject_file.write_text(updated, encoding="utf-8")
        updated_files.append(pyproject_file)

    # 2. automation/src/agy_toolkit/__init__.py
    init_file = repo_path / "automation" / "src" / "agy_toolkit" / "__init__.py"
    if init_file.exists():
        text = init_file.read_text(encoding="utf-8")
        updated = re.sub(
            r'(__version__\s*=\s*["\'])([^"\']+)(["\'])',
            rf"\g<1>{new_version}\g<3>",
            text,
            count=1,
        )
        init_file.write_text(updated, encoding="utf-8")
        updated_files.append(init_file)

    # 3. automation/src/agy_toolkit/mcp_server.py
    mcp_file = repo_path / "automation" / "src" / "agy_toolkit" / "mcp_server.py"
    if mcp_file.exists():
        text = mcp_file.read_text(encoding="utf-8")
        updated = re.sub(
            r'(SERVER_VERSION\s*=\s*["\'])([^"\']+)(["\'])',
            rf"\g<1>{new_version}\g<3>",
            text,
            count=1,
        )
        mcp_file.write_text(updated, encoding="utf-8")
        updated_files.append(mcp_file)

    return updated_files


def prepend_changelog(repo_path: Path, new_entry: str) -> Path:
    """Prepend release notes into CHANGELOG.md, preserving header and past entries."""
    changelog_file = repo_path / "CHANGELOG.md"
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

    existing_content = ""
    if changelog_file.exists():
        raw = changelog_file.read_text(encoding="utf-8")
        # Strip existing top header if present
        if raw.startswith("# Changelog"):
            parts = raw.split("\n\n", 2)
            if len(parts) >= 3:
                existing_content = parts[2]
            else:
                existing_content = raw
        else:
            existing_content = raw

    full_content = header + new_entry.strip() + "\n\n" + existing_content.strip() + "\n"
    changelog_file.write_text(full_content, encoding="utf-8")
    return changelog_file


@dataclass
class ReleasePlan:
    current_version: str
    next_version: str
    bump_type: str
    previous_tag: Optional[str]
    commits_count: int
    categories: Dict[str, List[ConventionalCommit]]
    uncategorized: List[Tuple[str, str]]
    changelog_snippet: str
    files_to_update: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_version": self.current_version,
            "next_version": self.next_version,
            "bump_type": self.bump_type,
            "previous_tag": self.previous_tag,
            "commits_count": self.commits_count,
            "files_to_update": self.files_to_update,
            "changelog_snippet": self.changelog_snippet,
        }


def plan_release(repo_path: Path, bump_type: str) -> ReleasePlan:
    """Construct release plan, calculate next SemVer, and draft changelog."""
    curr_ver_str = get_current_project_version(repo_path)
    semver = SemVer.parse(curr_ver_str)
    next_semver = semver.bump(bump_type)
    next_ver_str = str(next_semver)

    prev_tag = get_latest_git_tag(repo_path)
    commits = get_git_commits_since(repo_path, prev_tag)
    categories, uncategorized = categorize_commits(commits)

    today = datetime.date.today().isoformat()
    changelog_snippet = generate_changelog_entry(
        next_ver_str, today, categories, uncategorized
    )

    files_to_update = [
        "pyproject.toml",
        "automation/src/agy_toolkit/__init__.py",
        "automation/src/agy_toolkit/mcp_server.py",
        "CHANGELOG.md",
    ]

    return ReleasePlan(
        current_version=curr_ver_str,
        next_version=next_ver_str,
        bump_type=bump_type,
        previous_tag=prev_tag,
        commits_count=len(commits),
        categories=categories,
        uncategorized=uncategorized,
        changelog_snippet=changelog_snippet,
        files_to_update=files_to_update,
    )


def execute_release(
    repo_path: Path,
    bump_type: str,
    dry_run: bool = False,
    skip_tests: bool = False,
    allow_branch: bool = False,
) -> Dict[str, Any]:
    """Execute complete release workflow: gate verification, version bump, changelog, and git tag."""
    root = Path(repo_path).resolve()

    # Gate 1: Branch verification
    if not allow_branch:
        is_branch_ok, branch_msg = check_release_branch(root)
        if not is_branch_ok:
            raise PermissionError(branch_msg)

    # Gate 2: Clean working tree
    is_clean, clean_msg = check_working_tree_clean(root)
    if not is_clean:
        raise RuntimeError(clean_msg)

    # Gate 3: Test verification
    if not skip_tests:
        tests_passed, test_msg = run_release_test_gate(root)
        if not tests_passed:
            raise RuntimeError(test_msg)

    # Calculate release plan
    plan = plan_release(root, bump_type)

    if dry_run:
        return {
            "status": "DRY_RUN",
            "plan": plan.to_dict(),
            "message": f"Simulated release v{plan.next_version} ({plan.bump_type}). No files or git state modified.",
        }

    # 1. Update version metadata files
    updated_files = sync_version_metadata(root, plan.next_version)

    # 2. Prepend changelog
    changelog_file = prepend_changelog(root, plan.changelog_snippet)
    updated_files.append(changelog_file)

    # 3. Stage and commit release files
    rel_files = [str(f.relative_to(root)) for f in updated_files]
    add_code, _, add_err = _run_git_cmd(root, ["add"] + rel_files)
    if add_code != 0:
        raise RuntimeError(f"Git staging failed: {add_err}")

    commit_msg = f"chore(release): bump version to v{plan.next_version}"
    commit_code, _, commit_err = _run_git_cmd(root, ["commit", "-m", commit_msg])
    if commit_code != 0:
        raise RuntimeError(f"Git commit failed: {commit_err}")

    # 4. Create annotated git tag
    tag_name = f"v{plan.next_version}"
    tag_msg = f"Release {tag_name}"
    tag_code, _, tag_err = _run_git_cmd(root, ["tag", "-a", tag_name, "-m", tag_msg])
    if tag_code != 0:
        raise RuntimeError(f"Git tagging failed: {tag_err}")

    return {
        "status": "SUCCESS",
        "tag": tag_name,
        "version": plan.next_version,
        "bump_type": plan.bump_type,
        "updated_files": rel_files,
        "commits_count": plan.commits_count,
        "changelog_entry": plan.changelog_snippet,
    }
