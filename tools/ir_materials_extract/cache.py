"""Simple SQLite-backed cache for downloaded IR artifacts."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional, Tuple

from .config import ToolConfig

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    url TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    content_type TEXT,
    fetched_at TEXT,
    file_path TEXT
);
"""


def _ensure_initialized(config: ToolConfig) -> None:
    """Create cache directory and initialize SQLite schema if needed."""
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(config.cache_db) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(SCHEMA)
        conn.commit()


def _extension_for_mime(content_type: Optional[str]) -> str:
    if not content_type:
        return ".bin"
    if "pdf" in content_type:
        return ".pdf"
    if "html" in content_type or "text" in content_type:
        return ".html"
    if "json" in content_type:
        return ".json"
    return ".bin"


def get_cached_entry(url: str, config: ToolConfig = ToolConfig()) -> Optional[dict]:
    """Return cached metadata dictionary for URL if present."""
    _ensure_initialized(config)
    with sqlite3.connect(config.cache_db) as conn:
        row = conn.execute(
            "SELECT url, sha256, content_type, fetched_at, file_path FROM artifacts WHERE url = ?",
            (url,),
        ).fetchone()
    if not row:
        return None
    url_value, digest, content_type, fetched_at, file_path = row
    path = Path(file_path)
    if not path.exists():
        with sqlite3.connect(config.cache_db) as conn:
            conn.execute("DELETE FROM artifacts WHERE url = ?", (url,))
            conn.commit()
        return None
    return {
        "url": url_value,
        "sha256": digest,
        "content_type": content_type,
        "fetched_at": fetched_at,
        "file_path": path,
    }


def get_cached(url: str, config: ToolConfig = ToolConfig()) -> Optional[Path]:
    entry = get_cached_entry(url, config)
    if not entry:
        return None
    return Path(entry["file_path"])


def is_cached(url: str, config: ToolConfig = ToolConfig()) -> bool:
    return get_cached(url, config) is not None


def store_artifact(
    url: str,
    content: bytes,
    content_type: Optional[str],
    config: ToolConfig = ToolConfig(),
) -> Tuple[Path, str]:
    """Persist artifact content to disk and record metadata in cache."""
    _ensure_initialized(config)
    digest = sha256(content).hexdigest()
    extension = _extension_for_mime(content_type)
    file_path = config.cache_dir / f"{digest}{extension}"
    if not file_path.exists():
        file_path.write_bytes(content)
    fetched_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(config.cache_db) as conn:
        conn.execute(
            """
            INSERT INTO artifacts (url, sha256, content_type, fetched_at, file_path)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                sha256=excluded.sha256,
                content_type=excluded.content_type,
                fetched_at=excluded.fetched_at,
                file_path=excluded.file_path
            """,
            (url, digest, content_type, fetched_at, str(file_path)),
        )
        conn.commit()
    return file_path, digest


__all__ = ["get_cached", "store_artifact", "is_cached", "get_cached_entry"]
