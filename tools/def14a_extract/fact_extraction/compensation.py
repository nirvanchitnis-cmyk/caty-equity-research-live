"""Executive compensation extraction."""

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


class CompensationFactExtractor(BaseFactExtractor):
    fact_ids = [
        "ceo_name",
        "ceo_total_compensation_current_year",
        "sct_total_compensation_all_neos",
        "ceo_pay_ratio",
    ]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        sections = {span.section_id: span for span in section_spans}
        results: Dict[str, FactCandidate] = {}
        sct_span = sections.get("executive_compensation")
        if sct_span:
            table = self._find_table(tables, sct_span)
            if table:
                normalized = self._normalize_sct(table.dataframe)
                ceo_row = normalized[normalized["role"].str.contains("chief executive", case=False, na=False)]
                ceo_name = ceo_row["name"].iloc[0] if not ceo_row.empty else None
                ceo_total = ceo_row["total"].iloc[0] if not ceo_row.empty else None
                if ceo_name:
                    results["ceo_name"] = self._build_fact(
                        "ceo_name",
                        ceo_name,
                        sct_span,
                        table,
                        value_type="string",
                    )
                if ceo_total is not None:
                    results["ceo_total_compensation_current_year"] = self._build_fact(
                        "ceo_total_compensation_current_year",
                        float(ceo_total),
                        sct_span,
                        table,
                        unit="USD",
                        value_type="currency",
                    )
                results["sct_total_compensation_all_neos"] = self._build_fact(
                    "sct_total_compensation_all_neos",
                    float(normalized["total"].sum()),
                    sct_span,
                    table,
                    unit="USD",
                    value_type="currency",
                )
        text_meta = [_extract_text(doc) for doc in documents]
        text_blob = "\n".join(text for text, _meta in text_meta)
        provenance_hint = next((meta for _text, meta in text_meta if meta), {})
        ratio_match = re.search(r"CEO Pay Ratio.*?(\d+(?:\.\d+)?:1)", text_blob, re.IGNORECASE | re.DOTALL)
        if ratio_match:
            results["ceo_pay_ratio"] = FactCandidate(
                fact_id="ceo_pay_ratio",
                value=ratio_match.group(1),
                value_type="ratio",
                unit=None,
                anchors=[sections["executive_compensation"]] if "executive_compensation" in sections else [],
                extraction_path={
                    "source_text": ratio_match.group(0),
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.8,
                    "parser": 0.9,
                    "header": 0.8,
                    "validation": 0.95,
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

    def _normalize_sct(self, frame: pd.DataFrame) -> pd.DataFrame:
        clean = frame.copy()
        clean.columns = [
            str(col).strip().lower().replace("\n", " ").replace("  ", " ")
            for col in clean.columns
        ]
        clean = clean.rename(
            columns={
                "name and principal position": "name",
                "principal position": "role",
            }
        )
        if "name" not in clean.columns:
            clean.rename(columns={clean.columns[0]: "name"}, inplace=True)
        if "role" not in clean.columns and len(clean.columns) > 1:
            clean.rename(columns={clean.columns[1]: "role"}, inplace=True)
        numeric_cols = [col for col in clean.columns if re.search(r"\d{4}", col) or "total" in col]
        for col in numeric_cols:
            clean[col] = (
                clean[col]
                .astype(str)
                .str.replace(r"[^\d\.\-]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )
        clean["total"] = clean[numeric_cols].max(axis=1) if numeric_cols else 0
        if "role" not in clean.columns:
            clean["role"] = ""
        return clean[["name", "role", "total"]]

    def _build_fact(
        self,
        fact_id: str,
        value: object,
        span: SectionSpan,
        table: TableExtractionResult,
        *,
        unit: Optional[str] = None,
        value_type: str = "string",
    ) -> FactCandidate:
        return FactCandidate(
            fact_id=fact_id,
            value=value,
            value_type=value_type,
            unit=unit,
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
                "header": 0.85,
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
    else:
        return doc.artifact.path.read_text(errors="ignore"), meta
    return "\n".join(pages), meta
