from tools.def14a_extract.provenance import ProvenanceAssembler
from tools.def14a_extract.models import (
    FactCandidate,
    FilingMetadata,
    SectionSpan,
    ValidationReport,
)


def test_provenance_confidence_bounds():
    assembler = ProvenanceAssembler()
    candidate = FactCandidate(
        fact_id="meeting_date",
        value="2024-05-12",
        value_type="string",
        unit=None,
        anchors=[
            SectionSpan(
                section_id="meeting_overview",
                start_offset=0,
                end_offset=10,
                heading_text="NOTICE OF ANNUAL MEETING",
                score=0.9,
                source="deterministic",
            )
        ],
        extraction_path={"source_url": "https://example.com", "sha256": "abc", "pages": [1]},
        method="regex",
        confidence_components={
            "source": 1.0,
            "parser": 0.9,
            "header": 0.9,
            "validation": 1.0,
            "provenance": 1.0,
        },
    )
    metadata = FilingMetadata(
        accession_number="0000000000-24-000001",
        filing_date="2024-04-01",
        form_type="DEF 14A",
        primary_document_url="https://example.com/def14a",
    )
    report = ValidationReport()
    facts = assembler.attach({"meeting_date": candidate}, report, metadata)
    value = facts["meeting_date"]
    assert 0 <= value.confidence <= 1
