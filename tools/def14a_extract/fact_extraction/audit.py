"""Audit fees and auditor identity extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping, Optional

import pandas as pd

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from . import BaseFactExtractor


class AuditFactExtractor(BaseFactExtractor):
    fact_ids = [
        "auditor_name",
        "audit_fees_current_year",
        "audit_fees_prior_year",
        "audit_related_fees_current_year",
        "tax_fees_current_year",
        "other_fees_current_year",
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
        if audit_span:
            table = self._find_table(tables, audit_span)
            if table:
                normalized = self._normalize_audit_fees(table.dataframe)
                for key, value in normalized.items():
                    if value is None:
                        continue
                    results[key] = FactCandidate(
                        fact_id=key,
                        value=value,
                        value_type="currency",
                        unit="USD",
                        anchors=[audit_span],
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
                            "header": 0.85,
                            "validation": 0.95,
                            "provenance": 0.9,
                        },
                    )
        text_meta = [_extract_text(doc) for doc in documents]
        text_blob = "\n".join(text for text, _meta in text_meta)
        provenance_hint = next((meta for _text, meta in text_meta if meta), {})
        auditor_match = re.search(
            r"(?:audit committee has selected|our independent registered public accounting firm|provided by)\s+([A-Za-z&\s\.,]+?)(?:\.)",
            text_blob,
            re.IGNORECASE,
        )
        if auditor_match:
            results["auditor_name"] = FactCandidate(
                fact_id="auditor_name",
                value=auditor_match.group(1).strip(),
                value_type="string",
                unit=None,
                anchors=[audit_span] if audit_span else [],
                extraction_path={
                    "source_text": auditor_match.group(0),
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.8,
                    "parser": 0.85,
                    "header": 0.8,
                    "validation": 0.9,
                    "provenance": 0.8,
                },
            )
        return results

    def _find_table(
        self,
        tables: Iterable[TableExtractionResult],
        span: SectionSpan,
    ) -> Optional[TableExtractionResult]:
        for table in tables:
            if table.section_id == span.section_id:
                return table
        return None

    def _normalize_audit_fees(self, frame: pd.DataFrame) -> Dict[str, Optional[float]]:
        clean = frame.copy()
        clean.columns = [
            str(col).strip().lower().replace("\n", " ").replace("  ", " ")
            for col in clean.columns
        ]
        mapping = {}
        for col in clean.columns:
            if "audit-related" in col:
                mapping[col] = "audit_related"
            elif "audit" in col and "related" not in col:
                mapping[col] = "audit"
            elif "tax" in col:
                mapping[col] = "tax"
            elif "other" in col:
                mapping[col] = "other"
            elif "total" in col:
                mapping[col] = "total"
        clean = clean.rename(columns=mapping)
        numeric_cols = [col for col in clean.columns if col in {"audit", "audit_related", "tax", "other"}]
        result: Dict[str, Optional[float]] = {
            "audit_fees_current_year": None,
            "audit_fees_prior_year": None,
            "audit_related_fees_current_year": None,
            "tax_fees_current_year": None,
            "other_fees_current_year": None,
        }
        for idx, row in clean.iterrows():
            if "audit" in row and not pd.isna(row["audit"]):
                if result["audit_fees_current_year"] is None:
                    result["audit_fees_current_year"] = self._clean_currency(row["audit"])
                else:
                    result["audit_fees_prior_year"] = self._clean_currency(row["audit"])
            if "audit_related" in row and not pd.isna(row["audit_related"]):
                result["audit_related_fees_current_year"] = self._clean_currency(row["audit_related"])
            if "tax" in row and not pd.isna(row["tax"]):
                result["tax_fees_current_year"] = self._clean_currency(row["tax"])
            if "other" in row and not pd.isna(row["other"]):
                result["other_fees_current_year"] = self._clean_currency(row["other"])
        return result

    def _clean_currency(self, value: object) -> float:
        text = str(value)
        digits = re.sub(r"[^\d\.\-]", "", text)
        if not digits:
            return 0.0
        return float(digits)



def _extract_text(doc: DocumentProfile) -> tuple[str, dict]:
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
