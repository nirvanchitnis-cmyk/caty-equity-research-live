"""Executive compensation extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from .base import BaseFactExtractor
from .helpers import build_table_result_from_frame, iter_document_tables


class CompensationFactExtractor(BaseFactExtractor):
    fact_ids = [
        "ceo_name",
        "ceo_total_compensation_current_year",
        "sct_total_compensation_all_neos",
        "ceo_pay_ratio",
        "equity_plan_available_shares",
        "equity_plan_overhang_percent",
    ]

    SUMMARY_HEADER_KEYWORDS = {
        "name": "name",
        "principal position": "name",
        "year": "year",
        "salary": "salary",
        "bonus": "bonus",
        "stock awards": "stock_awards",
        "option awards": "option_awards",
        "non equity incentive": "non_equity",
        "pension value": "pension",
        "deferred compensation": "pension",
        "all other compensation": "other",
        "total": "total",
    }

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        sections = {span.section_id: span for span in section_spans}
        results: Dict[str, FactCandidate] = {}
        documents_list = list(documents)
        tables_list = list(tables)
        table_list = tables_list

        sct_span = sections.get("executive_compensation")
        if sct_span:
            table = self._locate_summary_compensation_table(
                tables_list, sct_span, documents_list
            )
            if table:
                normalized = self._normalize_sct(table.dataframe)
                if not normalized.empty:
                    latest_year = int(normalized["year"].max())
                    ceo_row = self._select_ceo_row(normalized, latest_year)
                    if ceo_row is not None:
                        ceo_name = ceo_row["person_name"]
                        results["ceo_name"] = self._build_fact(
                            "ceo_name",
                            ceo_name,
                            sct_span,
                            table,
                            value_type="string",
                        )
                        results["ceo_total_compensation_current_year"] = self._build_fact(
                            "ceo_total_compensation_current_year",
                            float(ceo_row["total"]),
                            sct_span,
                            table,
                            unit="USD",
                            value_type="currency",
                        )
                    current_year_rows = normalized[normalized["year"] == latest_year]
                    if not current_year_rows.empty:
                        total_sum = float(current_year_rows["total"].sum())
                        results["sct_total_compensation_all_neos"] = self._build_fact(
                            "sct_total_compensation_all_neos",
                            total_sum,
                            sct_span,
                            table,
                            unit="USD",
                            value_type="currency",
                        )

        text_meta = [_extract_text(doc) for doc in documents_list]
        text_blob = "\n".join(text for text, _meta in text_meta)
        provenance_hint = next((meta for _text, meta in text_meta if meta), {})
        ratio_match = re.search(
            r"(?i)(?:ratio.*?was\s+)?(\d+(?:\.\d+)?)\s+(?:to|:)\s*1",
            text_blob,
            re.DOTALL,
        )
        anchors: Sequence[SectionSpan] = (
            [sections["executive_compensation"]]
            if "executive_compensation" in sections
            else []
        )
        if ratio_match:
            results["ceo_pay_ratio"] = FactCandidate(
                fact_id="ceo_pay_ratio",
                value=f"{ratio_match.group(1)}:1",
                value_type="ratio",
                unit=None,
                anchors=anchors,
                extraction_path={
                    "source_text": ratio_match.group(0).strip(),
                    **provenance_hint,
                },
                method="regex",
                confidence_components={
                    "source": 0.85,
                    "parser": 0.9,
                    "header": 0.8,
                    "validation": 0.95,
                    "provenance": 0.85,
                },
            )

        equity_facts = self._extract_equity_plan_facts(section_spans, table_list, documents_list, sections)
        results.update(equity_facts)

        return results

    def _extract_equity_plan_facts(
        self,
        section_spans: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        documents: Sequence[DocumentProfile],
        sections: Mapping[str, SectionSpan],
    ) -> Dict[str, FactCandidate]:
        span = sections.get('executive_compensation')
        results: Dict[str, FactCandidate] = {}
        located = self._locate_equity_plan_table(tables, documents)
        if located and span:
            table, available_shares = located
            if available_shares is not None:
                results['equity_plan_available_shares'] = self._build_fact(
                    'equity_plan_available_shares',
                    int(available_shares),
                    span,
                    table,
                    unit=None,
                    value_type='integer',
                )
        overhang = self._extract_overhang_percent(documents)
        if overhang and span:
            value, snippet, meta = overhang
            extraction = {
                'source_text': snippet.strip(),
                **meta,
            }
            results['equity_plan_overhang_percent'] = FactCandidate(
                fact_id='equity_plan_overhang_percent',
                value=value,
                value_type='percentage',
                unit=None,
                anchors=[span],
                extraction_path=extraction,
                method='regex',
                confidence_components={
                    'source': 0.85,
                    'parser': 0.85,
                    'header': 0.8,
                    'validation': 0.9,
                    'provenance': 0.85,
                },
            )
        return results

    def _locate_equity_plan_table(
        self,
        tables: Sequence[TableExtractionResult],
        documents: Sequence[DocumentProfile],
    ) -> Optional[tuple[TableExtractionResult, Optional[int]]]:
        for table in tables:
            if self._is_equity_plan_table(table.dataframe):
                parsed = self._parse_equity_plan_table(table.dataframe)
                if parsed is not None:
                    return table, parsed
        for document in documents:
            for idx, frame in iter_document_tables(document, max_tables=350):
                if not self._is_equity_plan_table(frame):
                    continue
                parsed = self._parse_equity_plan_table(frame)
                if parsed is not None:
                    table = build_table_result_from_frame(
                        'executive_compensation',
                        frame,
                        document,
                        label=f'equity_{idx}',
                        source_method='fallback_html',
                        quality_score=0.75,
                    )
                    return table, parsed
        return None

    def _is_equity_plan_table(self, frame: pd.DataFrame) -> bool:
        if frame.empty:
            return False
        flattened = ' '.join(str(value).lower() for value in frame.to_numpy().flatten())
        return 'plan category' in flattened and 'remaining available' in flattened

    @staticmethod
    def _get_cell(row: Sequence[str], index: Optional[int]) -> str:
        if index is None:
            return ''
        if index >= len(row):
            return ''
        return row[index]


    def _parse_equity_plan_table(self, frame: pd.DataFrame) -> Optional[int]:
        working = frame.fillna('').astype(str)
        header_row = working.iloc[0].tolist()
        remaining_idx = None
        for idx, header in enumerate(header_row):
            if 'remaining available' in header.lower():
                remaining_idx = idx
                break
        if remaining_idx is None:
            return None
        for row in working.iloc[1:].itertuples(index=False, name=None):
            label = str(row[0]).strip().lower()
            if not label:
                continue
            if label.startswith('total') or label.startswith('equity compensation plans approved'):
                value = self._clean_text(self._get_cell(row, remaining_idx))
                parsed = self._parse_int(value)
                if parsed is not None:
                    return parsed
        return None

    def _extract_overhang_percent(
        self,
        documents: Sequence[DocumentProfile],
    ) -> Optional[tuple[float, str, Dict[str, object]]]:
        text_meta = [_extract_text(doc) for doc in documents]
        for text, meta in text_meta:
            match = re.search(
                r"overhang(?: of)? approximately\s+(\d+(?:\.\d+)?)%",
                text,
                re.IGNORECASE,
            )
            if match:
                value = float(match.group(1))
                snippet = match.group(0)
                return value, snippet, meta
        return None


    def _locate_summary_compensation_table(
        self,
        tables: Iterable[TableExtractionResult],
        span: SectionSpan,
        documents: Sequence[DocumentProfile],
    ) -> Optional[TableExtractionResult]:
        section_tables = [
            table for table in tables if table.section_id == span.section_id
        ]
        for table in section_tables:
            if self._is_summary_table(table.dataframe):
                return table
        for document in documents:
            for idx, frame in iter_document_tables(document, max_tables=350):
                if self._is_summary_table(frame):
                    return build_table_result_from_frame(
                        span.section_id,
                        frame,
                        document,
                        label=f"summary_{idx}",
                        source_method="fallback_html",
                        quality_score=0.75,
                    )
        return None

    def _is_summary_table(self, frame: pd.DataFrame) -> bool:
        if frame.empty:
            return False
        first_row = " ".join(str(value).lower() for value in frame.iloc[0].tolist())
        name_match = "name" in first_row and "principal" in first_row
        total_match = "total" in first_row
        salary_match = "salary" in first_row
        return name_match and total_match and salary_match

    def _normalize_sct(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame()
        working = frame.fillna("").astype(str)
        headers = [
            self._normalize_header(str(cell))
            for cell in working.iloc[0].tolist()
        ]

        records: List[Dict[str, object]] = []
        for raw_row in working.iloc[1:].itertuples(index=False, name=None):
            row_values: Dict[str, object] = {}
            for header, cell in zip(headers, raw_row):
                if not header:
                    continue
                cleaned = self._clean_text(str(cell))
                if cleaned.lower() in {"", "nan"}:
                    continue
                if header == "name":
                    name, role = self._split_name_role(cleaned)
                    row_values["raw_name"] = cleaned
                    row_values["person_name"] = name
                    row_values["role"] = role
                elif header == "year":
                    year = self._parse_year(cleaned)
                    if year is not None:
                        row_values["year"] = year
                else:
                    value = self._parse_currency(cleaned)
                    if value is not None:
                        row_values[header] = value
            if "person_name" in row_values and "year" in row_values:
                numeric_fields = [
                    "salary",
                    "bonus",
                    "stock_awards",
                    "option_awards",
                    "non_equity",
                    "pension",
                    "other",
                    "total",
                ]
                if "total" not in row_values:
                    subtotal = 0.0
                    found = False
                    for field in numeric_fields:
                        if field in row_values:
                            subtotal += float(row_values[field])
                            found = True
                    if found:
                        row_values["total"] = subtotal
                records.append(row_values)

        normalized = pd.DataFrame(records)
        if normalized.empty:
            return normalized
        numeric_columns = [
            col
            for col in [
                "salary",
                "bonus",
                "stock_awards",
                "option_awards",
                "non_equity",
                "pension",
                "other",
                "total",
            ]
            if col in normalized.columns
        ]
        for col in numeric_columns:
            normalized[col] = normalized[col].astype(float)
        normalized["year"] = normalized["year"].astype(int)
        return normalized

    def _select_ceo_row(
        self,
        normalized: pd.DataFrame,
        year: int,
    ) -> Optional[pd.Series]:
        year_rows = normalized[normalized["year"] == year]
        if year_rows.empty:
            return None
        ceo_mask = year_rows["role"].str.contains(
            r"(chief\s+executive|principal\s+executive|ceo)",
            case=False,
            na=False,
        )
        if ceo_mask.any():
            return year_rows[ceo_mask].iloc[0]
        return year_rows.iloc[0]

    def _normalize_header(self, header: str) -> Optional[str]:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", header.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        for keyword, canonical in self.SUMMARY_HEADER_KEYWORDS.items():
            if keyword in cleaned:
                return canonical
        return None

    @staticmethod
    def _split_name_role(value: str) -> tuple[str, str]:
        parts = re.split(r"\s{2,}", value.strip(), maxsplit=1)
        name = re.sub(r"\s+", " ", parts[0]).strip()
        role = ""
        if len(parts) > 1:
            role = re.sub(r"\s+", " ", parts[1]).strip()
        return name, role

    @staticmethod
    def _parse_year(value: str) -> Optional[int]:
        match = re.search(r"(20\d{2})", value)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _parse_int(value: str) -> Optional[int]:
        if not value:
            return None
        cleaned = re.sub(r'[^0-9]', '', value)
        if not cleaned:
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None


    @staticmethod
    def _parse_currency(value: str) -> Optional[float]:
        if not value:
            return None
        cleaned = value.strip().replace("—", "-")
        if cleaned in {"—", "-", "--", "–"}:
            return 0.0
        cleaned = (
            cleaned.replace(",", "")
            .replace("$", "")
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

    @staticmethod
    def _clean_text(value: str) -> str:
        return (
            value.replace(" ", " ")
            .replace("—", "-")
            .strip()
        )

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
    else:
        return doc.artifact.path.read_text(errors="ignore"), meta
    return "\n".join(pages), meta

