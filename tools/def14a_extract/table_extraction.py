"""Table extraction orchestrator."""

from __future__ import annotations

import hashlib
import json
import tempfile
import uuid
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

from .logging_utils import log_event
from .models import DocumentProfile, SectionSpan, TableExtractionResult


class TableExtractionOrchestrator:
    def __init__(self) -> None:
        pass

    def extract(
        self,
        section: SectionSpan,
        documents: Sequence[DocumentProfile],
    ) -> List[TableExtractionResult]:
        tables: List[TableExtractionResult] = []
        for doc in documents:
            if doc.doc_type == "html":
                tables.extend(self._extract_html_tables(section, doc))
            elif doc.doc_type.startswith("pdf"):
                tables.extend(self._extract_pdf_tables(section, doc))
        log_event(
            "Extracted tables for section",
            section=section.section_id,
            count=len(tables),
        )
        return tables

    def _extract_html_tables(
        self,
        section: SectionSpan,
        profile: DocumentProfile,
    ) -> List[TableExtractionResult]:
        url = profile.artifact.url
        try:
            tables = pd.read_html(str(profile.artifact.path), flavor="lxml")
        except ValueError:
            return []
        results: List[TableExtractionResult] = []
        for idx, frame in enumerate(tables):
            table_id = f"{section.section_id}_html_{idx}"
            snapshot_path = self._dump_snapshot(frame, table_id)
            sha256 = self._hash_table(frame)
            results.append(
                TableExtractionResult(
                    section_id=section.section_id,
                    table_id=table_id,
                    dataframe=frame,
                    raw_snapshot_path=snapshot_path,
                    source_method="html",
                    quality_score=0.9,
                    source_url=profile.artifact.url,
                    sha256=sha256,
                )
            )
        return results

    def _extract_pdf_tables(
        self,
        section: SectionSpan,
        profile: DocumentProfile,
    ) -> List[TableExtractionResult]:
        try:
            import camelot  # type: ignore
        except ImportError:
            return []
        tables = []
        try:
            tables = camelot.read_pdf(
                str(profile.artifact.path),
                pages="all",
                flavor="lattice",
            )
        except Exception:
            return []
        results: List[TableExtractionResult] = []
        for idx, table in enumerate(tables):
            frame = table.df
            table_id = f"{section.section_id}_pdf_{idx}"
            snapshot_path = self._dump_snapshot(frame, table_id)
            sha256 = self._hash_table(frame)
            results.append(
                TableExtractionResult(
                    section_id=section.section_id,
                    table_id=table_id,
                    dataframe=frame,
                    raw_snapshot_path=snapshot_path,
                    source_method="pdf",
                    quality_score=0.7,
                    source_url=profile.artifact.url,
                    sha256=sha256,
                )
            )
        return results

    def _dump_snapshot(self, frame: pd.DataFrame, table_id: str) -> Path:
        snapshot_dir = Path(".cache/def14a_snapshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{table_id}_{uuid.uuid4().hex}.json"
        snapshot_path.write_text(frame.to_json(orient="split"))
        return snapshot_path

    def _hash_table(self, frame: pd.DataFrame) -> str:
        data = frame.to_json(orient="split").encode("utf-8")
        return hashlib.sha256(data).hexdigest()
