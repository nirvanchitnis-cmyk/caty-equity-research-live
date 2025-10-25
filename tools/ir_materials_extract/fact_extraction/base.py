from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Sequence

from ..section_locators.models import SectionSpan
from ..table_extraction.models import TableExtractionResult
from .models import FactCandidate


class BaseFactExtractor(ABC):
    """Abstract contract for IR fact extractors."""

    @abstractmethod
    def extract(
        self,
        sections: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        normalized_text: str,
        artifact_metadata: dict,
    ) -> Dict[str, FactCandidate]:
        """Return fact_id -> FactCandidate map for the supplied artifact."""
        raise NotImplementedError
