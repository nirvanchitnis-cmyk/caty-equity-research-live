"""Meeting metadata extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping, Sequence

from dateutil import parser

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from . import BaseFactExtractor


class MeetingFactExtractor(BaseFactExtractor):
    fact_ids = ["meeting_date", "meeting_time", "meeting_timezone", "record_date", "meeting_location_type", "meeting_access_url"]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        results: Dict[str, FactCandidate] = {}
        notice_sections = [span for span in section_spans if span.section_id in ("meeting_overview",)]
        text_sources = []
        provenance_hint = {}
        for doc in documents:
            text, meta = _extract_text_with_meta(doc)
            text_sources.append(text)
            if not provenance_hint:
                provenance_hint = meta
        combined = "\n".join(text_sources)
        patterns = {
            "meeting_date": r"Meeting(?: of Shareholders)? (?:will be|is) held on ([A-Z][a-z]+ \d{1,2}, \d{4})",
            "record_date": r"record at the close of business on ([A-Z][a-z]+ \d{1,2}, \d{4})",
            "meeting_time": r"at (\d{1,2}:\d{2}\s?[ap]\.m\.)",
            "meeting_timezone": r"(\bEastern\b|\bCentral\b|\bPacific\b|\bMountain\b)\s+Time",
            "meeting_location_type": r"(virtual-only|virtual|in-person|hybrid) meeting",
            "meeting_access_url": r"(https?://[^\s,]+)",
        }
        for fact_id, pattern in patterns.items():
            match = re.search(pattern, combined, re.IGNORECASE)
            if not match:
                continue
            value = match.group(1)
            if fact_id in ("meeting_date", "record_date"):
                try:
                    value = parser.parse(value).strftime("%Y-%m-%d")
                except Exception:
                    pass
            results[fact_id] = FactCandidate(
                fact_id=fact_id,
                value=value,
                value_type="string",
                unit=None,
                anchors=notice_sections,
                extraction_path={
                    "source_text": value,
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.9,
                    "parser": 0.9,
                    "header": 0.8,
                    "validation": 1.0,
                    "provenance": 0.8,
                },
            )
        return results


def _extract_text_with_meta(doc: DocumentProfile) -> tuple[str, dict]:
    meta = {
        "source_url": doc.artifact.url,
        "sha256": doc.artifact.sha256,
        "pages": [],
        "dom_path": None,
    }
    if doc.doc_type == "html":
        return doc.artifact.path.read_text(errors="ignore"), meta
    if doc.doc_type.startswith("pdf"):
        from ..normalizers.pdf_text import extract_pdf_text
        pdf_data = extract_pdf_text(doc)
        pages = pdf_data["pages"]
        meta["pages"] = list(range(1, len(pages) + 1))
        if not any(page.strip() for page in pages):
            try:
                from ..normalizers.ocr_pipeline import run_ocr
            except ImportError:
                return "\n".join(pages), meta
            ocr_data = run_ocr(doc)
            pages = ocr_data["pages"]
            meta["pages"] = list(range(1, len(pages) + 1))
        return "\n".join(pages), meta
    return doc.artifact.path.read_text(errors="ignore"), meta
