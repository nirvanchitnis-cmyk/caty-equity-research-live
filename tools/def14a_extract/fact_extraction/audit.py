"""Audit fees and auditor identity extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping, Optional, Sequence

import pandas as pd

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from .base import BaseFactExtractor
from .helpers import build_table_result_from_frame, iter_document_tables


class AuditFactExtractor(BaseFactExtractor):
    fact_ids = [
        "auditor_name",
        "audit_fees_current_year",
        "audit_fees_prior_year",
        "audit_related_fees_current_year",
        "tax_fees_current_year",
        "other_fees_current_year",
    ]

    KNOWN_AUDITORS = [
        "PricewaterhouseCoopers LLP",
        "Deloitte & Touche LLP",
        "Ernst & Young LLP",
        "KPMG LLP",
        "Grant Thornton LLP",
        "BDO USA, P.C.",
        "Crowe LLP",
        "RSM US LLP",
        "Baker Tilly US, LLP",
        "Moss Adams LLP",
        "Marcum LLP",
    ]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        spans = {span.section_id: span for span in section_spans}
        audit_span = spans.get("audit_fees")
        results: Dict[str, FactCandidate] = {}
        documents_list = list(documents)
        tables_list = list(tables)

        if audit_span:
            table = self._locate_audit_table(tables_list, audit_span, documents_list)
            if table:
                parsed = self._normalize_audit_fees(table.dataframe)
                for fact_id, value in parsed.items():
                    if value is None:
                        continue
                    results[fact_id] = self._build_currency_fact(
                        fact_id,
                        value,
                        audit_span,
                        table,
                    )

        text_meta = [_extract_text(doc) for doc in documents_list]
        text_blob = "\n".join(text for text, _meta in text_meta)
        provenance_hint = next((meta for _text, meta in text_meta if meta), {})
        auditor_info = self._extract_auditor_name(text_blob)
        anchors: Sequence[SectionSpan] = [audit_span] if audit_span else []
        if auditor_info:
            auditor_name, snippet = auditor_info
            results["auditor_name"] = FactCandidate(
                fact_id="auditor_name",
                value=auditor_name,
                value_type="string",
                unit=None,
                anchors=anchors,
                extraction_path={
                    "source_text": snippet.strip(),
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.9,
                    "parser": 0.85,
                    "header": 0.85,
                    "validation": 0.9,
                    "provenance": 0.85,
                },
            )

        return results

    def _locate_audit_table(
        self,
        tables: Iterable[TableExtractionResult],
        span: SectionSpan,
        documents: Sequence[DocumentProfile],
    ) -> Optional[TableExtractionResult]:
        section_tables = [
            table for table in tables if table.section_id == span.section_id
        ]
        for table in section_tables:
            if self._is_audit_table(table.dataframe):
                return table
        for document in documents:
            for idx, frame in iter_document_tables(document, max_tables=350):
                if self._is_audit_table(frame):
                    return build_table_result_from_frame(
                        span.section_id,
                        frame,
                        document,
                        label=f"audit_{idx}",
                        source_method="fallback_html",
                        quality_score=0.75,
                    )
        return None

    def _is_audit_table(self, frame: pd.DataFrame) -> bool:
        if frame.empty:
            return False
        contains_label = frame.applymap(
            lambda value: isinstance(value, str) and "audit fees" in value.lower()
        ).any().any()
        if contains_label:
            return True
        first_row = " ".join(str(value).lower() for value in frame.iloc[0].tolist())
        return "audit fees" in first_row or "principal accountant fees" in first_row

    def _normalize_audit_fees(self, frame: pd.DataFrame) -> Dict[str, Optional[float]]:
        result: Dict[str, Optional[float]] = {
            "audit_fees_current_year": None,
            "audit_fees_prior_year": None,
            "audit_related_fees_current_year": None,
            "tax_fees_current_year": None,
            "other_fees_current_year": None,
        }
        if frame.empty:
            return result
        working = frame.fillna("").astype(str)
        header_text = " ".join(working.iloc[0].tolist())
        years = self._extract_years(header_text)
        prior_year_exists = len(years) > 1
        for raw_row in working.iloc[1:].itertuples(index=False, name=None):
            label = str(raw_row[0]).lower().strip()
            category = self._categorize_fee(label)
            if not category:
                continue
            row_text = " ".join(str(cell) for cell in raw_row)
            numbers = self._extract_numeric_values(row_text)
            if not numbers:
                continue
            while len(numbers) > 2 and numbers[0] == 0.0 and numbers[1] != 0.0:
                numbers.pop(0)
            current_value = numbers[0] if numbers else None
            prior_value = numbers[1] if len(numbers) > 1 else None
            if current_value is None:
                continue
            if category == "audit":
                result["audit_fees_current_year"] = current_value
                if prior_year_exists and prior_value is not None:
                    result["audit_fees_prior_year"] = prior_value
            elif category == "audit_related":
                result["audit_related_fees_current_year"] = current_value
            elif category == "tax":
                result["tax_fees_current_year"] = current_value
            elif category == "other":
                result["other_fees_current_year"] = current_value
        return result

    @staticmethod
    def _extract_years(text: str) -> Sequence[int]:
        candidates = re.findall(r"20\d{2}", text)
        ordered: list[int] = []
        for value in candidates:
            year = int(value)
            if year not in ordered:
                ordered.append(year)
        return ordered

    @staticmethod
    def _categorize_fee(label: str) -> Optional[str]:
        if "audit-related" in label or "audit related" in label:
            return "audit_related"
        if "audit" in label:
            return "audit"
        if "tax" in label:
            return "tax"
        if "other" in label:
            return "other"
        return None

    def _extract_numeric_values(self, text: str) -> Sequence[float]:
        tokens = re.findall(r"\(?\$?[\d,]+(?:\.\d+)?\)?|—|--|–|-", text)
        values: list[float] = []
        for token in tokens:
            cleaned = token.strip()
            if not cleaned:
                continue
            bare = cleaned.replace("$", "").replace(",", "").replace("(", "").replace(")", "")
            if bare.isdigit() and len(bare) <= 2:
                continue
            value = self._parse_currency(cleaned)
            if value is None:
                continue
            values.append(value)
        return values

    @staticmethod
    def _parse_currency(value: str) -> Optional[float]:
        cleaned = value.strip().replace("—", "-")
        if cleaned in {"—", "-", "--", "–"}:
            return 0.0
        cleaned = (
            cleaned.replace("$", "")
            .replace(",", "")
            .replace(" ", "")
        )
        negative = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            negative = True
            cleaned = cleaned[1:-1]
        cleaned = cleaned.strip()
        if not cleaned:
            return None
        try:
            number = float(cleaned)
            return -number if negative else number
        except ValueError:
            digits = re.sub(r"[^\d\.]", "", cleaned)
            if not digits:
                return None
            try:
                number = float(digits)
                return -number if negative else number
            except ValueError:
                return None

    def _extract_auditor_name(self, text: str) -> Optional[tuple[str, str]]:
        patterns = [
            r"appointment of\s+([A-Z][A-Za-z&\.,\s]+?)\s+as our independent registered public accounting firm",
            r"has selected\s+([A-Z][A-Za-z&\.,\s]+?)\s+(?:to continue to serve as|to serve as|as)\s+our independent registered public accounting firm",
            r"has appointed\s+([A-Z][A-Za-z&\.,\s]+?)\s+as our independent registered public accounting firm",
            r"independent registered public accounting firm[^.,]*,\s+([A-Z][A-Za-z&\.,\s]+)",
            r"services are provided by\s+([A-Z][A-Za-z&\.,\s]+?)(?:,|\.)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = self._clean_auditor_name(match.group(1))
                if candidate:
                    return candidate, match.group(0)
        lowered = text.lower()
        for firm in self.KNOWN_AUDITORS:
            pos = lowered.find(firm.lower())
            if pos != -1:
                snippet = text[pos:pos + len(firm)]
                return firm, snippet
        return None

    @staticmethod
    def _clean_auditor_name(name: str) -> Optional[str]:
        cleaned = re.sub(r"\s+", " ", name).strip(" ,.;:")
        if not cleaned:
            return None
        cleaned = re.split(r"\s+(?:during|for|within)\b", cleaned, maxsplit=1)[0]
        return cleaned.strip(" ,.;:")

    def _build_currency_fact(
        self,
        fact_id: str,
        value: float,
        span: SectionSpan,
        table: TableExtractionResult,
    ) -> FactCandidate:
        return FactCandidate(
            fact_id=fact_id,
            value=float(value),
            value_type="currency",
            unit="USD",
            anchors=[span],
            extraction_path={
                "table_id": table.table_id,
                "sha256": table.sha256,
                "source_url": table.source_url,
                "snapshot_path": str(table.raw_snapshot_path),
            },
            method="table",
            confidence_components={
                "source": 0.9,
                "parser": 0.9,
                "header": 0.9,
                "validation": 0.95,
                "provenance": 0.9,
            },
        )


def _extract_text(doc: DocumentProfile) -> tuple[str, dict]:
    meta = {
        "source_url": doc.artifact.url,
        "sha256": doc.artifact.sha256,
        "pages": [],
        "dom_path": None,
    }
    if doc.doc_type == "html":
        from ..normalizers.html_normalizer import normalize_html

        normalized = normalize_html(doc)
        meta["selector_map"] = normalized.get("selector_map", {})
        return normalized.get("text", ""), meta
    if doc.doc_type.startswith("pdf"):
        from ..normalizers.pdf_text import extract_pdf_text
        pdf_data = extract_pdf_text(doc)
        pages = pdf_data["pages"]
        if not any(page.strip() for page in pages):
            try:
                from ..normalizers.ocr_pipeline import run_ocr
            except ImportError:
                return "\n".join(pages), meta
            ocr = run_ocr(doc)
            pages = ocr["pages"]
        meta["pages"] = list(range(1, len(pages) + 1))
        return "\n".join(pages), meta
    return doc.artifact.path.read_text(errors="ignore"), meta

