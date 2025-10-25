"""Local artifact caching via SQLite index."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import ToolConfig, ensure_cache_dirs
from .logging_utils import log_event
from .models import FilingArtifact


class CacheCorruptionError(RuntimeError):
    """Raised when cached data integrity cannot be verified."""


@dataclass
class CacheRecord:
    url: str
    sha256: str
    path: Path
    mime_type: str
    content_type: str


class ArtifactCacheManager:
    def __init__(self, config: ToolConfig) -> None:
        self._config = config
        ensure_cache_dirs(config)
        self._db = config.cache_db
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    url TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    path TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    content_type TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _compute_sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def store(self, url: str, data: bytes, mime_type: str, content_type: str) -> FilingArtifact:
        sha256 = self._compute_sha256(data)
        file_path = self._config.cache_dir / f"{sha256}"
        if not file_path.exists():
            file_path.write_bytes(data)
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts (url, sha256, path, mime_type, content_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, sha256, str(file_path), mime_type, content_type),
            )
            conn.commit()
        return FilingArtifact(
            url=url,
            path=file_path,
            sha256=sha256,
            mime_type=mime_type,
            content_type=content_type,
        )

    def get(self, url: str) -> Optional[FilingArtifact]:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT sha256, path, mime_type, content_type FROM artifacts WHERE url = ?",
                (url,),
            ).fetchone()
        if not row:
            return None
        sha256, path, mime_type, content_type = row
        path = Path(path)
        if not path.exists():
            log_event("Cache file missing, purging index entry", url=url)
            self.delete(url)
            return None
        data = path.read_bytes()
        if self._compute_sha256(data) != sha256:
            self.delete(url)
            raise CacheCorruptionError(f"Checksum mismatch for cached artifact: {url}")
        return FilingArtifact(
            url=url,
            path=path,
            sha256=sha256,
            mime_type=mime_type,
            content_type=content_type,
        )

    def delete(self, url: str) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("DELETE FROM artifacts WHERE url = ?", (url,))
            conn.commit()
