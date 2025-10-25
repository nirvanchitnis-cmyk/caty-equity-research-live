from abc import ABC, abstractmethod
from typing import Dict, Sequence

from ..models import DocumentProfile, FactCandidate, SectionSpan, TableExtractionResult


class BaseFactExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        section_spans: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        documents: Sequence[DocumentProfile],
        registry: Dict,
    ) -> Dict[str, FactCandidate]:
        """Extract facts from sections/tables. Return dict of fact_id -> FactCandidate."""
        raise NotImplementedError
