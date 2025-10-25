"""Data models shared by fetchers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ArtifactMetadata:
    url: str
    content_type: str
    sha256: str
    size_bytes: int
    fetched_at: str  # ISO 8601 timestamp


@dataclass
class FetchResult:
    success: bool
    artifact: Optional[ArtifactMetadata]
    file_path: Optional[Path]
    error: Optional[str] = None


__all__ = ["ArtifactMetadata", "FetchResult"]
