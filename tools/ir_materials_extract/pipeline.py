"""End-to-end orchestration for IR materials fact extraction."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, Optional
from urllib.parse import unquote, urlparse

from .config import ToolConfig
from .fact_extraction import (
    GuidanceFactExtractor,
    ResultsFactExtractor,
    SegmentFactExtractor,
    validate_all,
)
from .fact_extraction.models import FactCandidate
from .fetchers import fetch_artifact_sync
from .normalizers import normalize_html, normalize_pdf
from .section_locators import locate_sections
from .table_extraction import extract_html_tables, extract_pdf_tables


def _content_type_from_suffix(path: Path, raw_content_type: str) -> str:
    """Normalize content type using both server mime type and file suffix."""
    if "html" in raw_content_type or path.suffix.lower() in {".html", ".htm"}:
        return "text/html"
    if "pdf" in raw_content_type or path.suffix.lower() == ".pdf":
        return "application/pdf"
    return raw_content_type or "application/octet-stream"


def _resolve_local_artifact(url: str) -> tuple[Path, str, str]:
    parsed = urlparse(url)
    local_path = Path(unquote(parsed.path))
    artifact_path = local_path if local_path.is_absolute() else Path.cwd() / local_path
    if not artifact_path.exists():
        raise FileNotFoundError(f"Local artifact not found: {artifact_path}")
    content_type = _content_type_from_suffix(artifact_path, "")
    sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    return artifact_path, content_type, sha256


def extract_facts_from_url(
    url: str,
    fact_ids: Optional[Iterable[str]] = None,
    *,
    force_refresh: bool = False,
    config: Optional[ToolConfig] = None,
) -> Dict[str, FactCandidate]:
    """Fetch an artifact, extract facts, and return structured candidates."""
    active_config = config or ToolConfig()
    parsed = urlparse(url)

    if parsed.scheme == "file":
        artifact_path, content_type, sha256 = _resolve_local_artifact(url)
    else:
        fetch_result = fetch_artifact_sync(url, config=active_config, force_refresh=force_refresh)
        if not fetch_result.success or not fetch_result.file_path:
            error = fetch_result.error or "unknown error"
            raise RuntimeError(f"Failed to fetch artifact for {url}: {error}")
        artifact_path = Path(fetch_result.file_path)
        fetched_meta = fetch_result.artifact
        content_type = _content_type_from_suffix(
            artifact_path,
            fetched_meta.content_type.lower() if fetched_meta else "",
        )
        sha256 = fetched_meta.sha256 if fetched_meta else ""

    if content_type.startswith("text/html"):
        normalized = normalize_html(artifact_path)
        tables = extract_html_tables(artifact_path)
    elif content_type.startswith("application/pdf"):
        normalized = normalize_pdf(artifact_path)
        tables = extract_pdf_tables(artifact_path)
    else:
        raise ValueError(f"Unsupported content type '{content_type}' for {url}")

    text = str(normalized.get("text") or "")
    sections = locate_sections(text, str(artifact_path))

    metadata = {
        "url": url,
        "sha256": sha256,
        "content_type": content_type,
    }

    extractors = (
        GuidanceFactExtractor(),
        ResultsFactExtractor(),
        SegmentFactExtractor(),
    )

    fact_map: Dict[str, FactCandidate] = {}
    for extractor in extractors:
        extracted = extractor.extract(sections, tables, text, metadata)
        fact_map.update(extracted)

    validated = validate_all(fact_map)

    if fact_ids is not None:
        requested = {fact_id for fact_id in fact_ids}
        validated = {key: value for key, value in validated.items() if key in requested}

    return validated


__all__ = ["extract_facts_from_url"]
