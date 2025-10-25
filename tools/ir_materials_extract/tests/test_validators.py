from tools.ir_materials_extract.fact_extraction.models import FactCandidate
from tools.ir_materials_extract.fact_extraction.validators import (
    validate_all,
    validate_guidance_midpoint,
    validate_segment_totals,
)


def test_validate_guidance_midpoint_flags_mismatch() -> None:
    facts = {
        "guidance_revenue_low": FactCandidate(
            fact_id="guidance_revenue_low",
            value=1_000_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "guidance_revenue_high": FactCandidate(
            fact_id="guidance_revenue_high",
            value=1_200_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "guidance_revenue_mid": FactCandidate(
            fact_id="guidance_revenue_mid",
            value=1_050_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.9,
        ),
    }

    validate_guidance_midpoint(facts)
    warnings = facts["guidance_revenue_mid"].validation["warnings"]
    assert warnings, "Expected midpoint validation warning"
    assert facts["guidance_revenue_mid"].confidence < 0.9


def test_validate_segment_totals_executes() -> None:
    facts = {
        "segment_revenue_commercial": FactCandidate(
            fact_id="segment_revenue_commercial",
            value=300_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "segment_revenue_consumer": FactCandidate(
            fact_id="segment_revenue_consumer",
            value=200_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "segment_revenue_total": FactCandidate(
            fact_id="segment_revenue_total",
            value=600_000_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.95,
        ),
    }

    validate_segment_totals(facts)
    warnings = facts["segment_revenue_total"].validation["warnings"]
    assert warnings, "Expected warning when segment sum != total"


def test_validate_all_runs_suite() -> None:
    facts = {
        "guidance_revenue_low": FactCandidate(
            fact_id="guidance_revenue_low",
            value=1_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "guidance_revenue_high": FactCandidate(
            fact_id="guidance_revenue_high",
            value=2_000,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "guidance_revenue_mid": FactCandidate(
            fact_id="guidance_revenue_mid",
            value=1_400,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.9,
        ),
        "segment_revenue_a": FactCandidate(
            fact_id="segment_revenue_a",
            value=50,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "segment_revenue_b": FactCandidate(
            fact_id="segment_revenue_b",
            value=60,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.8,
        ),
        "segment_revenue_total": FactCandidate(
            fact_id="segment_revenue_total",
            value=120,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=0.9,
        ),
    }

    validate_all(facts)
    assert facts["guidance_revenue_mid"].validation["warnings"]
    assert facts["segment_revenue_total"].validation["warnings"]
