"""Cross-check validators for extracted IR facts."""

from __future__ import annotations

from typing import Dict

from .models import FactCandidate


def validate_guidance_midpoint(facts: Dict[str, FactCandidate]) -> None:
    """Flag midpoint inconsistencies when low/high are present."""
    keys = {"guidance_revenue_low", "guidance_revenue_high", "guidance_revenue_mid"}
    if not keys.issubset(facts):
        return

    low = facts["guidance_revenue_low"].value
    high = facts["guidance_revenue_high"].value
    midpoint = facts["guidance_revenue_mid"].value

    expected = (low + high) / 2
    if abs(midpoint - expected) > 1.0:
        facts["guidance_revenue_mid"].validation.setdefault("warnings", []).append(
            f"Midpoint {midpoint:,.0f} != expected {expected:,.0f}"
        )
        facts["guidance_revenue_mid"].confidence *= 0.8


def validate_segment_totals(facts: Dict[str, FactCandidate]) -> None:
    """Ensure that segment sums reconcile to the reported total."""
    if "segment_revenue_total" not in facts:
        return

    segment_keys = [
        key
        for key in facts
        if key.startswith("segment_revenue_") and key != "segment_revenue_total"
    ]
    if not segment_keys:
        return

    total = facts["segment_revenue_total"].value
    calculated = sum(facts[key].value for key in segment_keys)
    tolerance = max(total * 0.01, 1.0)

    if abs(calculated - total) > tolerance:
        facts["segment_revenue_total"].validation.setdefault("warnings", []).append(
            f"Segment sum {calculated:,.0f} != Total {total:,.0f}"
        )
        facts["segment_revenue_total"].confidence *= 0.7


def validate_all(facts: Dict[str, FactCandidate]) -> Dict[str, FactCandidate]:
    """Run all validation routines in place and return the facts dict."""
    validate_guidance_midpoint(facts)
    validate_segment_totals(facts)
    return facts


__all__ = [
    "validate_all",
    "validate_guidance_midpoint",
    "validate_segment_totals",
]
