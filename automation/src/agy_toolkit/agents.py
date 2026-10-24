"""AGYToolkit Agent Registry - Loader and validator for specialist subagents.

Supports both Markdown (.md) specifications with YAML frontmatter
and legacy JSON (.json) agent definitions.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

AGENTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agents"

REQUIRED_FIELDS = [
    "name",
    "role",
    "description",
    "systemPrompt",
    "enableWriteTools",
    "enableSubagentTools",
    "enableMCPTools",
    "recommendedWorkspace",
]

VALID_WORKSPACES = {"inherit", "branch", "share"}
EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]")


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """Parse YAML frontmatter and body from Markdown content."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    metadata = {}
    body_start_idx = -1

    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start_idx = idx + 1
            break
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            # Handle booleans
            if val.lower() == "true":
                metadata[key] = True
            elif val.lower() == "false":
                metadata[key] = False
            else:
                metadata[key] = val

    body = "\n".join(lines[body_start_idx:]).strip() if body_start_idx != -1 else ""
    return metadata, body


def validate_agent_spec(spec: Dict) -> List[str]:
    """Validate an agent specification dictionary against AGY requirements."""
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in spec:
            errors.append(f"Missing required field: '{field}'")

    if "name" in spec:
        name = spec["name"]
        if not re.match(r"^[a-z0-9-]+$", str(name)):
            errors.append(f"Invalid name '{name}': must be lowercase hyphenated")

    if "recommendedWorkspace" in spec:
        ws = spec["recommendedWorkspace"]
        if ws not in VALID_WORKSPACES:
            errors.append(f"Invalid recommendedWorkspace '{ws}': must be one of {VALID_WORKSPACES}")

    if "systemPrompt" in spec:
        prompt = spec["systemPrompt"]
        if EMOJI_PATTERN.search(prompt):
            errors.append("Anti-Bloat violation: System prompt contains emojis")

    return errors


def load_agent(agent_name: str, agents_dir: Optional[Path] = None) -> Dict:
    """Load and validate an agent definition by name (.md or .json)."""
    target_dir = agents_dir or AGENTS_DIR

    md_path = target_dir / f"{agent_name}.md"
    json_path = target_dir / f"{agent_name}.json"

    if md_path.exists():
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        metadata, body = parse_frontmatter(content)
        spec = dict(metadata)
        spec["systemPrompt"] = body
    elif json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    else:
        raise FileNotFoundError(f"Agent definition not found for '{agent_name}' in {target_dir}")

    errors = validate_agent_spec(spec)
    if errors:
        raise ValueError(f"Invalid agent specification for '{agent_name}': {', '.join(errors)}")

    return spec


def list_agents(agents_dir: Optional[Path] = None) -> List[Dict]:
    """List all available specialist agents in the agents directory."""
    target_dir = agents_dir or AGENTS_DIR
    if not target_dir.exists():
        return []

    agents = []
    # Discover .md first, then .json
    seen_names = set()

    for file_path in sorted(target_dir.glob("*.md")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = parse_frontmatter(content)
            spec = dict(metadata)
            spec["systemPrompt"] = body
            if not validate_agent_spec(spec) and spec["name"] not in seen_names:
                agents.append(spec)
                seen_names.add(spec["name"])
        except Exception:
            continue

    for file_path in sorted(target_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
            if not validate_agent_spec(spec) and spec["name"] not in seen_names:
                agents.append(spec)
                seen_names.add(spec["name"])
        except Exception:
            continue

    return agents
