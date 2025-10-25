"""Beneficial ownership extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping

import pandas as pd

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from . import BaseFactExtractor


class BeneficialOwnershipExtractor(BaseFactExtractor):
    fact_ids = ["beneficial_owners_over5pct"]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        section_index = {span.section_id: span for span in section_spans}
        target_span = section_index.get("beneficial_ownership")
        if not target_span:
            return {}
        table = self._find_table(tables, target_span)
        if table is None:
            return {}
        normalized = self._normalize_table(table.dataframe)
        return {
            "beneficial_owners_over5pct": FactCandidate(
                fact_id="beneficial_owners_over5pct",
                value=normalized.to_dict(orient="records"),
                value_type="table",
                unit=None,
                anchors=[target_span],
                extraction_path={
                    "table_id": table.table_id,
                    "source_url": table.source_url,
                    "sha256": table.sha256,
                    "snapshot_path": str(table.raw_snapshot_path),
                },
                method="table",
                confidence_components={
                    "source": 0.85,
                    "parser": 0.9,
                    "header": 0.85,
                    "validation": 0.95,
                    "provenance": 0.9,
                },
            )
        }

    def _find_table(
        self,
        tables: Iterable[TableExtractionResult],
        span: SectionSpan,
    ) -> TableExtractionResult | None:
        for table in tables:
            if table.section_id == span.section_id:
                return table
        return None

    def _normalize_table(self, frame: pd.DataFrame) -> pd.DataFrame:
        renamed = frame.rename(
            columns=lambda col: str(col).lower().strip().replace(" ", "_"),
        )
        columns = renamed.columns.tolist()
        mapping = {}
        for col in columns:
            if "name" in col:
                mapping[col] = "name"
            elif "address" in col:
                mapping[col] = "address"
            elif "shares" in col or "amount" in col:
                mapping[col] = "shares"
            elif "%" in col or "percent" in col:
                mapping[col] = "percent"
        normalized = renamed.rename(columns=mapping)
        for col in ("shares", "percent"):
            if col in normalized.columns:
                normalized[col] = normalized[col].astype(str).apply(self._clean_numeric)
        keep_cols = [c for c in ("name", "address", "shares", "percent") if c in normalized.columns]
        return normalized[keep_cols]

    def _clean_numeric(self, value: str) -> float:
        digits = re.sub(r"[^\d\.\-]", "", value)
        if not digits:
            return 0.0
        try:
            return float(digits)
        except ValueError:
            return 0.0
