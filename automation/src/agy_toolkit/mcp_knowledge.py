"""AGYToolkit MCP Knowledge Tools - Native Model Context Protocol tools for FTS5 search."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from agy_toolkit.knowledge import index_workspace, search_knowledge

KNOWLEDGE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "agy_memory_search",
        "description": "Execute sub-millisecond FTS5 BM25 search across historical architectural decisions (ADRs), sprint sessions, and documentation.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords or phrase (e.g. 'hexagonal architecture', 'lease timeout', 'jwt').",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g. ARCH, BUS, CI, SEC, SESSION).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of ranked results to return (default: 5).",
                    "default": 5,
                },
            },
        },
    },
    {
        "name": "agy_memory_reindex",
        "description": "Rebuild or incrementally sync the SQLite FTS5 permanent knowledge index across decisions, sessions, and documentation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Force re-indexing all documents regardless of modification time.",
                    "default": False,
                },
            },
        },
    },
]


def handle_knowledge_tool(
    workspace_root: Path, tool_name: str, arguments: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Execute knowledge MCP tool call."""
    if tool_name == "agy_memory_search":
        query = arguments.get("query", "")
        category = arguments.get("category")
        limit = int(arguments.get("limit", 5))

        results = search_knowledge(
            workspace_root=workspace_root,
            query=query,
            category=category,
            limit=limit,
        )

        formatted_lines = [
            f"# Knowledge Search Results for '{query}'",
            f"Hits: {len(results)}",
            "",
        ]
        for idx, r in enumerate(results, 1):
            date_str = f" ({r.date})" if r.date else ""
            formatted_lines.append(f"### {idx}. [{r.category}] {r.title}{date_str}")
            formatted_lines.append(f"- **Source**: `{r.source_file}`")
            formatted_lines.append(f"- **Snippet**: {r.snippet}")
            formatted_lines.append("")

        return {
            "content": [{"type": "text", "text": "\n".join(formatted_lines).strip()}],
            "data": [r.to_dict() for r in results],
        }

    elif tool_name == "agy_memory_reindex":
        force = bool(arguments.get("force", False))
        report = index_workspace(workspace_root=workspace_root, force=force)

        text = (
            f"Knowledge Index Rebuilt:\n"
            f"- Files indexed: {report.indexed_files}\n"
            f"- Files skipped: {report.skipped_files}\n"
            f"- Total documents: {report.total_documents}\n"
            f"- Elapsed: {report.elapsed_ms} ms"
        )
        return {
            "content": [{"type": "text", "text": text}],
            "data": report.to_dict(),
        }

    return None
