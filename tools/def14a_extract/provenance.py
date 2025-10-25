"""Attach provenance metadata and compute confidence scores."""

from __future__ import annotations

from typing import Dict, Mapping

from .models import FactCandidate, FactWithProvenance, FilingMetadata, ValidationReport


class ProvenanceAssembler:
    def __init__(self) -> None:
        pass

    def attach(
        self,
        facts: Mapping[str, FactCandidate],
        validation: ValidationReport,
        metadata: FilingMetadata,
    ) -> Dict[str, FactWithProvenance]:
        results: Dict[str, FactWithProvenance] = {}
        for fact_id, fact in facts.items():
            components = fact.confidence_components
            confidence = (
                components.get("source", 1.0)
                * components.get("parser", 1.0)
                * components.get("header", 1.0)
                * components.get("validation", 1.0)
                * components.get("provenance", 1.0)
            )
            results[fact_id] = FactWithProvenance(
                value=fact.value,
                value_type=fact.value_type,
                unit=fact.unit,
                fiscal_year=fact.extraction_path.get("fiscal_year"),
                issuer_cik=metadata.accession_number.split("-")[0],
                filing_accession=metadata.accession_number,
                source_url=fact.extraction_path.get("source_url", metadata.primary_document_url),
                file_sha256=fact.extraction_path.get("sha256", ""),
                page_numbers=fact.extraction_path.get("pages", []),
                dom_path=fact.extraction_path.get("dom_path"),
                table_id=fact.extraction_path.get("table_id"),
                method=fact.method,
                confidence=min(max(confidence, 0.0), 1.0),
                validation={
                    "cross_checks": validation.warnings,
                    "warnings": list(validation.warnings),
                },
            )
        return results
