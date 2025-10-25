from typing import List

from .audit import AuditFactExtractor
from .base import BaseFactExtractor
from .compensation import CompensationFactExtractor
from .meeting import MeetingFactExtractor
from .ownership import BeneficialOwnershipExtractor
from .governance import GovernanceFactExtractor


def build_fact_extractors() -> List[BaseFactExtractor]:
    """Build the default set of fact extractors."""
    return [
        MeetingFactExtractor(),
        AuditFactExtractor(),
        CompensationFactExtractor(),
        BeneficialOwnershipExtractor(),
        GovernanceFactExtractor(),
    ]


__all__ = [
    "BaseFactExtractor",
    "build_fact_extractors",
    "AuditFactExtractor",
    "CompensationFactExtractor",
    "MeetingFactExtractor",
    "BeneficialOwnershipExtractor",
    "GovernanceFactExtractor",
]
