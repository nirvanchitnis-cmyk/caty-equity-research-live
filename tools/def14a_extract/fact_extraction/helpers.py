"""Shared helpers for fact extractors."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Iterator, Optional, Tuple

import pandas as pd

from ..models import DocumentProfile, TableExtractionResult

SNAPSHOT_DIR = Path('.cache/def14a_snapshots')


def iter_document_tables(
    document: DocumentProfile,
    *,
    max_tables: int = 300,
    match: Optional[str] = None,
) -> Iterator[Tuple[int, pd.DataFrame]]:
    """Yield tables from an HTML document using pandas read_html."""
    if document.doc_type != 'html':
        return
    try:
        read_kwargs = {
            'io': str(document.artifact.path),
            'flavor': 'lxml',
        }
        if match is not None:
            read_kwargs['match'] = match
        tables = pd.read_html(**read_kwargs)
    except ValueError:
        return
    for idx, frame in enumerate(tables):
        if idx >= max_tables:
            break
        yield idx, frame


def build_table_result_from_frame(
    section_id: str,
    frame: pd.DataFrame,
    document: DocumentProfile,
    *,
    label: str,
    source_method: str = 'fallback_html',
    quality_score: float = 0.75,
) -> TableExtractionResult:
    """Create a TableExtractionResult from a pandas DataFrame."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    table_id = f"{section_id}_{label}_{uuid.uuid4().hex[:8]}"
    data_json = frame.to_json(orient='split')
    sha256 = hashlib.sha256(data_json.encode('utf-8')).hexdigest()
    snapshot_path = SNAPSHOT_DIR / f"{table_id}.json"
    snapshot_path.write_text(data_json)
    return TableExtractionResult(
        section_id=section_id,
        table_id=table_id,
        dataframe=frame,
        raw_snapshot_path=snapshot_path,
        source_method=source_method,
        quality_score=quality_score,
        source_url=document.artifact.url,
        sha256=sha256,
    )

