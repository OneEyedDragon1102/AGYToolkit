"""AGYToolkit Knowledge Engine - SQLite FTS5 Full-Text Search across ADRs and sessions."""

import hashlib
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeDocument:
    doc_id: str
    source_file: str
    doc_type: str
    category: str
    title: str
    content: str
    date: str


@dataclass
class KnowledgeSearchResult:
    doc_id: str
    title: str
    category: str
    snippet: str
    source_file: str
    date: str
    rank: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IndexingReport:
    indexed_files: int
    indexed_documents: int
    skipped_files: int
    total_documents: int
    elapsed_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_db_path(workspace_root: Path) -> Path:
    """Return path to knowledge SQLite database."""
    mem_dir = Path(workspace_root).resolve() / ".agents" / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    return mem_dir / "knowledge.db"


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables with FTS5 virtual index."""
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta_files (
                file_path TEXT PRIMARY KEY,
                sha256 TEXT,
                mtime REAL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source_file TEXT,
                doc_type TEXT,
                category TEXT,
                title TEXT,
                content TEXT,
                date TEXT,
                updated_at REAL
            );
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                doc_id UNINDEXED,
                title,
                category,
                content,
                source_file UNINDEXED,
                date UNINDEXED,
                tokenize = 'porter unicode61'
            );
            """
        )


def _compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_decisions_markdown(content: str, source_path: str) -> List[KnowledgeDocument]:
    """Extract individual architectural decisions from markdown text."""
    docs = []
    pattern = re.compile(
        r"^\s*-\s+\*\*(\d{4}-\d{2}-\d{2})\s+\[([A-Z0-9_\-]+)\]\*\*:\s*(.*)$",
        re.MULTILINE,
    )

    idx = 0
    for match in pattern.finditer(content):
        date_str = match.group(1).strip()
        cat = match.group(2).strip().upper()
        statement = match.group(3).strip()
        doc_id = f"{source_path}:decision:{cat}:{idx}"
        title = f"Decision [{cat}] ({date_str})"
        docs.append(
            KnowledgeDocument(
                doc_id=doc_id,
                source_file=source_path,
                doc_type="decision",
                category=cat,
                title=title,
                content=statement,
                date=date_str,
            )
        )
        idx += 1

    return docs


def parse_sessions_markdown(content: str, source_path: str) -> List[KnowledgeDocument]:
    """Extract sections from archived sprint sessions."""
    docs = []
    filename = Path(source_path).name
    date_match = re.search(r"session-(\d{4}-\d{2}-\d{2})", filename)
    date_str = date_match.group(1) if date_match else "unknown"

    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
    for idx, sec in enumerate(sections):
        lines = sec.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else title
        if not body:
            continue
        doc_id = f"{source_path}:session:{idx}"
        docs.append(
            KnowledgeDocument(
                doc_id=doc_id,
                source_file=source_path,
                doc_type="session",
                category="SESSION",
                title=f"Session: {title}",
                content=body,
                date=date_str,
            )
        )
    return docs


def parse_general_markdown(
    content: str, source_path: str, default_category: str = "DOC"
) -> List[KnowledgeDocument]:
    """Chunk generic documentation by heading."""
    docs = []
    sections = re.split(r"^##?\s+", content, flags=re.MULTILINE)
    for idx, sec in enumerate(sections):
        lines = sec.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else heading
        if len(body) < 10:
            continue
        doc_id = f"{source_path}:doc:{idx}"
        docs.append(
            KnowledgeDocument(
                doc_id=doc_id,
                source_file=source_path,
                doc_type="doc",
                category=default_category,
                title=heading,
                content=body,
                date="",
            )
        )
    return docs


def index_workspace(workspace_root: Path, force: bool = False) -> IndexingReport:
    """Scan workspace and update the SQLite knowledge index."""
    t0 = time.perf_counter()
    root = Path(workspace_root).resolve()
    db_path = get_db_path(root)
    conn = sqlite3.connect(str(db_path))
    _init_db(conn)

    files_to_index: List[Path] = []

    # 1. Decisions registers
    decisions_main = root / ".agents" / "memory" / "decisions.md"
    if decisions_main.exists():
        files_to_index.append(decisions_main)

    decisions_hist = root / "docs" / "adr" / "decisions-history.md"
    if decisions_hist.exists():
        files_to_index.append(decisions_hist)

    # 2. Archived sessions
    sessions_dir = root / ".agents" / "memory" / "sessions"
    if sessions_dir.exists():
        for p in sessions_dir.glob("*.md"):
            files_to_index.append(p)

    # 3. Project rules & documentation
    for doc_name in ["GEMINI.md", "AGENTS.md", "README.md"]:
        p = root / doc_name
        if p.exists():
            files_to_index.append(p)

    docs_dir = root / "docs"
    if docs_dir.exists():
        for p in docs_dir.glob("*.md"):
            if p != decisions_hist:
                files_to_index.append(p)

    indexed_files = 0
    skipped_files = 0
    indexed_docs = 0

    cur = conn.cursor()
    for file_path in files_to_index:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = str(file_path.relative_to(root)).replace("\\", "/")
        current_sha = _compute_sha256(content)
        current_mtime = file_path.stat().st_mtime

        if not force:
            cur.execute(
                "SELECT sha256 FROM meta_files WHERE file_path = ?", (rel_path,)
            )
            row = cur.fetchone()
            if row and row[0] == current_sha:
                skipped_files += 1
                continue

        # Parse documents according to file type
        if "decisions" in rel_path:
            parsed = parse_decisions_markdown(content, rel_path)
        elif "sessions" in rel_path:
            parsed = parse_sessions_markdown(content, rel_path)
        elif rel_path in ["GEMINI.md", "AGENTS.md"]:
            parsed = parse_general_markdown(content, rel_path, default_category="RULE")
        else:
            parsed = parse_general_markdown(content, rel_path, default_category="DOC")

        with conn:
            # Clean existing records for this file
            cur.execute("DELETE FROM documents WHERE source_file = ?", (rel_path,))
            cur.execute(
                "DELETE FROM knowledge_fts WHERE source_file = ?", (rel_path,)
            )

            now = time.time()
            for doc in parsed:
                cur.execute(
                    """
                    INSERT INTO documents (id, source_file, doc_type, category, title, content, date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc.doc_id,
                        doc.source_file,
                        doc.doc_type,
                        doc.category,
                        doc.title,
                        doc.content,
                        doc.date,
                        now,
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO knowledge_fts (doc_id, title, category, content, source_file, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc.doc_id,
                        doc.title,
                        doc.category,
                        doc.content,
                        doc.source_file,
                        doc.date,
                    ),
                )
                indexed_docs += 1

            cur.execute(
                """
                INSERT OR REPLACE INTO meta_files (file_path, sha256, mtime)
                VALUES (?, ?, ?)
                """,
                (rel_path, current_sha, current_mtime),
            )
            indexed_files += 1

    cur.execute("SELECT count(*) FROM documents")
    total_docs = cur.fetchone()[0]
    conn.close()

    elapsed = (time.perf_counter() - t0) * 1000.0
    return IndexingReport(
        indexed_files=indexed_files,
        indexed_documents=indexed_docs,
        skipped_files=skipped_files,
        total_documents=total_docs,
        elapsed_ms=round(elapsed, 2),
    )


def sanitize_fts_query(query: str) -> str:
    """Format user query into safe FTS5 query with prefix matching."""
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return ""
    # Add prefix wildcard to each token for robust substring matching
    formatted = " ".join(f'"{t}"*' for t in tokens)
    return formatted


def search_knowledge(
    workspace_root: Path,
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> List[KnowledgeSearchResult]:
    """Execute FTS5 search with BM25 ranking across the knowledge base."""
    root = Path(workspace_root).resolve()
    db_path = get_db_path(root)

    if not db_path.exists():
        index_workspace(root)

    fts_query = sanitize_fts_query(query)
    if not fts_query:
        return []

    conn = sqlite3.connect(str(db_path))
    _init_db(conn)
    cur = conn.cursor()

    results: List[KnowledgeSearchResult] = []
    try:
        if category:
            cat_upper = category.strip().upper()
            sql = """
                SELECT doc_id, title, category,
                       snippet(knowledge_fts, 3, '[', ']', '...', 16) AS snip,
                       source_file, date, rank
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ? AND category = ?
                ORDER BY rank
                LIMIT ?
            """
            cur.execute(sql, (fts_query, cat_upper, limit))
        else:
            sql = """
                SELECT doc_id, title, category,
                       snippet(knowledge_fts, 3, '[', ']', '...', 16) AS snip,
                       source_file, date, rank
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            cur.execute(sql, (fts_query, limit))

        rows = cur.fetchall()
        for r in rows:
            results.append(
                KnowledgeSearchResult(
                    doc_id=r[0],
                    title=r[1],
                    category=r[2],
                    snippet=r[3],
                    source_file=r[4],
                    date=r[5],
                    rank=round(float(r[6]), 3),
                )
            )
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

    return results


def get_knowledge_stats(workspace_root: Path) -> Dict[str, Any]:
    """Retrieve indexing statistics and database metrics."""
    root = Path(workspace_root).resolve()
    db_path = get_db_path(root)
    if not db_path.exists():
        return {
            "exists": False,
            "total_documents": 0,
            "total_files": 0,
            "size_bytes": 0,
            "categories": {},
        }

    conn = sqlite3.connect(str(db_path))
    _init_db(conn)
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM documents")
    total_docs = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM meta_files")
    total_files = cur.fetchone()[0]

    cur.execute("SELECT category, count(*) FROM documents GROUP BY category")
    categories = {row[0]: row[1] for row in cur.fetchall()}

    conn.close()
    size_bytes = db_path.stat().st_size if db_path.exists() else 0

    return {
        "exists": True,
        "total_documents": total_docs,
        "total_files": total_files,
        "size_bytes": size_bytes,
        "categories": categories,
    }
