"""Validation logic for extracted facts."""

from __future__ import annotations

from typing import Dict, Mapping, Sequence

from .models import FactCandidate, ValidationReport


class ValidationSuite:
    def __init__(self) -> None:
        pass

    def validate(self, facts: Mapping[str, FactCandidate]) -> ValidationReport:
        warnings = []
        adjustments: Dict[str, float] = {}
        invalid_facts: Sequence[str] = []
        meeting_date = facts.get("meeting_date")
        record_date = facts.get("record_date")
        if meeting_date and record_date:
            try:
                from dateutil import parser

                m_date = parser.parse(str(meeting_date.value))
                r_date = parser.parse(str(record_date.value))
                if r_date > m_date:
                    warnings.append("Record date occurs after meeting date")
            except Exception:
                warnings.append("Failed to parse meeting/record dates for validation")
        return ValidationReport(warnings=warnings, adjustments=adjustments, invalid_facts=invalid_facts)
