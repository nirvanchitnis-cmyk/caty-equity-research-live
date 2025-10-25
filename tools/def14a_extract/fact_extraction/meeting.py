"""Meeting metadata extraction."""

from __future__ import annotations

import html
import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from dateutil import parser

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from . import BaseFactExtractor


class MeetingFactExtractor(BaseFactExtractor):
    fact_ids = [
        "meeting_date",
        "meeting_time",
        "meeting_timezone",
        "record_date",
        "meeting_location_type",
        "meeting_access_url",
    ]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        results: Dict[str, FactCandidate] = {}
        notice_sections = [span for span in section_spans if span.section_id == "meeting_overview"]

        text_sources: List[str] = []
        provenance_hint: Dict[str, object] = {}
        for doc in documents:
            text, meta = _extract_text_with_meta(doc)
            if text:
                text_sources.append(text)
            if not provenance_hint:
                provenance_hint = meta

        combined = html.unescape("\n".join(text_sources))
        if not combined.strip():
            return results

        def _add_fact(fact_id: str, value: object, source_text: str, value_type: str = "string", unit: Optional[str] = None) -> None:
            if fact_id in results or value in (None, ""):
                return
            results[fact_id] = FactCandidate(
                fact_id=fact_id,
                value=value,
                value_type=value_type,
                unit=unit,
                anchors=notice_sections,
                extraction_path={
                    "source_text": source_text.strip(),
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.9,
                    "parser": 0.9,
                    "header": 0.85 if notice_sections else 0.75,
                    "validation": 1.0,
                    "provenance": 0.85,
                },
            )

        meeting_date_match = _search_any(
            combined,
            [
                r"will be held on\s+([A-Za-z0-9,\s]+?\d{4})(?:\s*,?\s+at|\.)",
                r"will hold (?:its )?annual meeting on\s+([A-Za-z0-9,\s]+?\d{4})(?:\s*,?\s+at|\.)",
                r"annual meeting on\s+([A-Za-z0-9,\s]+?\d{4})",
            ],
        )
        if meeting_date_match:
            raw_date = meeting_date_match.group(1).strip()
            parsed = _safe_parse_date(raw_date)
            _add_fact("meeting_date", parsed or raw_date, meeting_date_match.group(0))

        record_date_match = _search_any(
            combined,
            [
                r"stockholders of record at the close of business on\s+([A-Za-z0-9,\s]+?\d{4})",
                r"record date\s+(?:is|was)\s+([A-Za-z0-9,\s]+?\d{4})",
                r"record date\s+(?:on|as of)\s+([A-Za-z0-9,\s]+?\d{4})",
            ],
        )
        if record_date_match:
            raw_record = record_date_match.group(1)
            parsed_record = _safe_parse_date(raw_record)
            _add_fact("record_date", parsed_record or raw_record, record_date_match.group(0))

        time_match = re.search(r"at\s+(\d{1,2}:\d{2}\s?(?:a|p)\.?m\.?)", combined, re.IGNORECASE)
        if time_match:
            _add_fact("meeting_time", _normalize_time(time_match.group(1)), time_match.group(0))

        tz_match = re.search(r"\b(Eastern|Central|Pacific|Mountain)\s+Time\b", combined, re.IGNORECASE)
        if tz_match:
            _add_fact("meeting_timezone", tz_match.group(1).title(), tz_match.group(0))

        location_value = _infer_meeting_format(combined)
        if location_value:
            value, snippet = location_value
            _add_fact("meeting_location_type", value, snippet)

        url_match = re.search(
            r"(https?://[A-Za-z0-9\.\-_/]*virtualshareholdermeeting[^\s<\"]+|https?://[^\s<\"]+lumi[^\s<\"]+)",
            combined,
            re.IGNORECASE,
        )
        if not url_match:
            url_match = re.search(r"(https?://[^\s<\"]+)", combined)
        if url_match:
            url = url_match.group(1).rstrip(".,)")
            _add_fact("meeting_access_url", url, url_match.group(0))

        return results


def _extract_text_with_meta(doc: DocumentProfile) -> tuple[str, Dict[str, object]]:
    meta: Dict[str, object] = {
        "source_url": doc.artifact.url,
        "sha256": doc.artifact.sha256,
        "pages": [],
        "dom_path": None,
    }
    if doc.doc_type == "html":
        from ..normalizers.html_normalizer import normalize_html

        normalized = normalize_html(doc)
        text = normalized.get("text", "")
        meta["selector_map"] = normalized.get("selector_map", {})
        return text, meta
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


def _search_any(text: str, patterns: Sequence[str]) -> Optional[re.Match[str]]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match
    return None


def _safe_parse_date(value: str) -> Optional[str]:
    try:
        return parser.parse(value).strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        return None


def _normalize_time(value: str) -> str:
    cleaned = value.strip().replace(".", "").upper()
    cleaned = cleaned.replace(" ", "")
    if cleaned.endswith("AM") or cleaned.endswith("PM"):
        hours, suffix = cleaned[:-2], cleaned[-2:]
        return f"{hours}{suffix}"
    return value.strip()


def _infer_meeting_format(text: str) -> Optional[tuple[str, str]]:
    lowered = text.lower()
    match = re.search(r"(virtual-only|exclusively in a virtual[^.]+)", lowered, re.IGNORECASE)
    if match:
        return "virtual-only", match.group(0)
    if re.search(r"virtual", lowered) and re.search(r"in-person", lowered):
        snippet = re.search(r"(virtual[^.]+in-person[^.]+)", text, re.IGNORECASE)
        snippet_text = snippet.group(0) if snippet else "virtual and in-person"
        return "hybrid", snippet_text
    match_virtual = re.search(r"(virtual (?:meeting|format))", text, re.IGNORECASE)
    if match_virtual:
        return "virtual", match_virtual.group(0)
    match_in_person = re.search(r"(in-person meeting|at our headquarters)", text, re.IGNORECASE)
    if match_in_person:
        return "in-person", match_in_person.group(0)
    return None
