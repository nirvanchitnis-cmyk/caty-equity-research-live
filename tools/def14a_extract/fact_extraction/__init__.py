"""Factories for fact extraction engines."""

from __future__ import annotations

class BaseFactExtractor:
    fact_ids: List[str] = []

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        raise NotImplementedError


from typing import Dict, Iterable, List, Mapping  # noqa: E402

from ..models import DocumentProfile, FactCandidate, SectionSpan, TableExtractionResult  # noqa: E402
from . import audit, compensation, meeting, ownership  # noqa: E402


def build_fact_extractors() -> List["BaseFactExtractor"]:
    return [
        meeting.MeetingFactExtractor(),
        ownership.BeneficialOwnershipExtractor(),
        compensation.CompensationFactExtractor(),
        audit.AuditFactExtractor(),
    ]
