"""Table extraction orchestrator."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import List, Sequence

import pandas as pd
from lxml import html as lxml_html

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
        try:
            tree = lxml_html.parse(str(profile.artifact.path)).getroot()
        except (OSError, ValueError):
            try:
                tables = pd.read_html(str(profile.artifact.path), flavor="lxml")
            except ValueError:
                return []
            return [
                self._build_table_result(section, idx, frame, profile.artifact.url, "html")
                for idx, frame in enumerate(tables[:3])
            ]

        if section.dom_path:
            xpath = f"{section.dom_path}/following::table[position()<=5]"
            table_nodes = tree.xpath(xpath)
        else:
            table_nodes = tree.xpath("//table[position()<=5]")

        results: List[TableExtractionResult] = []
        for idx, node in enumerate(table_nodes):
            try:
                table_html = lxml_html.tostring(node, encoding="unicode")
                frames = pd.read_html(table_html, flavor="lxml")
            except ValueError:
                continue
            for frame_idx, frame in enumerate(frames):
                table_idx = idx * 10 + frame_idx
                results.append(
                    self._build_table_result(
                        section,
                        table_idx,
                        frame,
                        profile.artifact.url,
                        "html",
                    )
                )
        return results[:5]

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
            results.append(
                self._build_table_result(
                    section,
                    idx,
                    frame,
                    profile.artifact.url,
                    "pdf",
                    quality_score=0.7,
                )
            )
        return results

    def _build_table_result(
        self,
        section: SectionSpan,
        idx: int,
        frame: pd.DataFrame,
        source_url: str,
        method: str,
        *,
        quality_score: float = 0.9,
    ) -> TableExtractionResult:
        table_id = f"{section.section_id}_{method}_{idx}"
        snapshot_path = self._dump_snapshot(frame, table_id)
        sha256 = self._hash_table(frame)
        return TableExtractionResult(
            section_id=section.section_id,
            table_id=table_id,
            dataframe=frame,
            raw_snapshot_path=snapshot_path,
            source_method=method,
            quality_score=quality_score,
            source_url=source_url,
            sha256=sha256,
        )

    def _dump_snapshot(self, frame: pd.DataFrame, table_id: str) -> Path:
        snapshot_dir = Path(".cache/def14a_snapshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{table_id}_{uuid.uuid4().hex}.json"
        snapshot_path.write_text(frame.to_json(orient="split"))
        return snapshot_path

    def _hash_table(self, frame: pd.DataFrame) -> str:
        data = frame.to_json(orient="split").encode("utf-8")
        return hashlib.sha256(data).hexdigest()
