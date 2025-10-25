from __future__ import annotations

import re
from typing import Dict, Sequence

from ..section_locators.models import SectionSpan
from ..table_extraction.models import TableExtractionResult
from .base import BaseFactExtractor
from .models import FactCandidate


_RANGE_PATTERN = re.compile(
    r"\$?\s*(\d+(?:\.\d+)?)\s*(B|BILLION|M|MILLION)"
    r"\s*(?:to|-|–|—)\s*\$?\s*(\d+(?:\.\d+)?)\s*(B|BILLION|M|MILLION)",
    re.IGNORECASE,
)


class GuidanceFactExtractor(BaseFactExtractor):
    """Extract revenue guidance ranges from narrative text."""

    def extract(
        self,
        sections: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        normalized_text: str,
        artifact_metadata: dict,
    ) -> Dict[str, FactCandidate]:
        results: Dict[str, FactCandidate] = {}

        guidance_sections = [s for s in sections if s.section_id == "guidance"]
        if not guidance_sections:
            return results

        section = guidance_sections[0]
        section_text = normalized_text[section.start_offset : section.end_offset]

        match = _RANGE_PATTERN.search(section_text)
        if not match:
            return results

        low_val = self._normalize_value(match.group(1), match.group(2))
        high_val = self._normalize_value(match.group(3), match.group(4))

        anchor = match.group(0).strip()
        metadata = {
            "source_url": artifact_metadata.get("url", ""),
            "file_sha256": artifact_metadata.get("sha256", ""),
            "doc_type": artifact_metadata.get("doc_type", ""),
        }

        results["guidance_revenue_low"] = FactCandidate(
            fact_id="guidance_revenue_low",
            value=low_val,
            value_type="currency",
            unit="USD",
            currency="USD",
            method="regex",
            confidence=0.8,
            anchor_text=anchor,
            **metadata,
        )

        results["guidance_revenue_high"] = FactCandidate(
            fact_id="guidance_revenue_high",
            value=high_val,
            value_type="currency",
            unit="USD",
            currency="USD",
            method="regex",
            confidence=0.8,
            anchor_text=anchor,
            **metadata,
        )

        midpoint = (low_val + high_val) / 2
        results["guidance_revenue_mid"] = FactCandidate(
            fact_id="guidance_revenue_mid",
            value=midpoint,
            value_type="currency",
            unit="USD",
            currency="USD",
            method="calculated",
            confidence=0.9,
            validation={"cross_checks": ["(low + high) / 2"], "warnings": []},
            anchor_text=anchor,
            **metadata,
        )

        return results

    @staticmethod
    def _normalize_value(raw_value: str, unit_token: str) -> float:
        value = float(raw_value)
        unit = unit_token.upper()
        if unit.startswith("B"):
            return value * 1_000_000_000
        if unit.startswith("M"):
            return value * 1_000_000
        return value
