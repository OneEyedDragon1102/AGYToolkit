"""AGYToolkit Stack Scaffolder - Generates turnkey production codebases."""

import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

STACKS_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "templates" / "stacks"
)

STACK_CATALOG: Dict[str, Dict[str, Any]] = {
    "spring-boot-hexagonal": {
        "name": "spring-boot-hexagonal",
        "aliases": ["spring-boot", "java-hexagonal", "spring"],
        "language": "Java 23",
        "framework": "Spring Boot 3.3+",
        "architecture": "Hexagonal (Ports & Adapters)",
        "description": "Enterprise Java service with domain models, inbound REST ports, JPA adapters, and Testcontainers.",
    },
    "node-clean-ts": {
        "name": "node-clean-ts",
        "aliases": ["node-ts", "clean-ts", "typescript", "fastify"],
        "language": "TypeScript (ESM / NodeNext)",
        "framework": "Fastify",
        "architecture": "Clean Architecture / Layered",
        "description": "High-performance TypeScript microservice with Fastify, Zod validation, Vitest, and Dockerfile.",
    },
    "python-fastapi": {
        "name": "python-fastapi",
        "aliases": ["fastapi", "python", "py-fastapi"],
        "language": "Python 3.12+",
        "framework": "FastAPI",
        "architecture": "Modular API & Service Layer",
        "description": "Modern async Python service with FastAPI, Pydantic v2, pytest suite, and ruff linting.",
    },
}


def sanitize_package_name(project_name: str, stack_type: str = "generic") -> str:
    """Sanitize project name into an idiomatic package identifier."""
    lowered = project_name.lower().strip()
    if stack_type == "java":
        # Java packages: lowercase alphanumeric characters only
        sanitized = re.sub(r"[^a-z0-9]", "", lowered)
        return sanitized or "app"
    elif stack_type == "python":
        # Python modules: lowercase alphanumeric and single underscores
        sanitized = re.sub(r"[^a-z0-9_]", "_", lowered)
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        if sanitized and sanitized[0].isdigit():
            sanitized = f"pkg_{sanitized}"
        return sanitized or "app"
    else:
        # Node / general: lowercase kebab-case
        sanitized = re.sub(r"[^a-z0-9-]", "-", lowered)
        sanitized = re.sub(r"-+", "-", sanitized).strip("-")
        return sanitized or "app"


def resolve_template_name(requested_name: str) -> str:
    """Resolve user-requested template name or alias to canonical catalog name."""
    req = requested_name.strip().lower()
    if req in STACK_CATALOG:
        return req
    for canonical, meta in STACK_CATALOG.items():
        if req in meta.get("aliases", []):
            return canonical
    raise ValueError(
        f"Unknown template: '{requested_name}'. "
        f"Available templates: {', '.join(sorted(STACK_CATALOG.keys()))}"
    )


def list_available_templates(stacks_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return list of available stack templates with metadata."""
    base_dir = stacks_dir or STACKS_TEMPLATES_DIR
    templates = []
    for canonical, meta in STACK_CATALOG.items():
        tmpl_path = base_dir / canonical
        exists = tmpl_path.is_dir()
        entry = dict(meta)
        entry["exists"] = exists
        entry["path"] = str(tmpl_path)
        templates.append(entry)
    return templates


def scaffold_stack_template(
    target_dir: Path,
    project_name: str,
    template_name: str,
    stacks_dir: Optional[Path] = None,
) -> List[Path]:
    """Render and copy stack template into target directory."""
    base_dir = stacks_dir or STACKS_TEMPLATES_DIR
    canonical_name = resolve_template_name(template_name)
    src_template_dir = base_dir / canonical_name

    if not src_template_dir.exists() or not src_template_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {src_template_dir}")

    # Determine stack type for package name sanitization
    if "spring" in canonical_name or "java" in canonical_name:
        package_name = sanitize_package_name(project_name, "java")
    elif "python" in canonical_name or "fastapi" in canonical_name:
        package_name = sanitize_package_name(project_name, "python")
    else:
        package_name = sanitize_package_name(project_name, "node")

    today_str = datetime.date.today().isoformat()
    year_str = str(datetime.date.today().year)

    replacements = {
        "{{PROJECT_NAME}}": project_name,
        "{{PACKAGE_NAME}}": package_name,
        "{{DATE}}": today_str,
        "{{YEAR}}": year_str,
    }

    created_files: List[Path] = []
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    for root, _, files in os.walk(src_template_dir):
        root_path = Path(root)
        rel_dir = root_path.relative_to(src_template_dir)

        # Substitute package name in directory path
        rel_dir_str = str(rel_dir)
        for key, val in replacements.items():
            rel_dir_str = rel_dir_str.replace(key, val)

        dest_dir = target_dir / rel_dir_str if rel_dir_str != "." else target_dir

        for filename in files:
            src_file = root_path / filename

            # Substitute placeholder in filename if present
            dest_filename = filename
            for key, val in replacements.items():
                dest_filename = dest_filename.replace(key, val)

            dest_file = dest_dir / dest_filename
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                content = src_file.read_text(encoding="utf-8")
                for key, val in replacements.items():
                    content = content.replace(key, val)
                dest_file.write_text(content, encoding="utf-8")
            except UnicodeDecodeError:
                dest_file.write_bytes(src_file.read_bytes())

            created_files.append(dest_file)

    return created_files
