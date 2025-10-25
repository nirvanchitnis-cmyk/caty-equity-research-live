import pandas as pd

from tools.ir_materials_extract.fact_extraction.segments import SegmentFactExtractor
from tools.ir_materials_extract.section_locators.models import SectionSpan
from tools.ir_materials_extract.table_extraction.models import TableExtractionResult



def _segment_section() -> SectionSpan:
    return SectionSpan(
        section_id="segment_results",
        start_offset=0,
        end_offset=150,
        heading_text="Segment Results",
        confidence=0.9,
        source_file="sample.pdf",
        page_number=5,
    )


def _segment_table(df: pd.DataFrame) -> TableExtractionResult:
    return TableExtractionResult(
        table_id="segment-1",
        source_file="sample.pdf",
        method="camelot_lattice",
        dataframe=df,
        confidence=0.92,
        page_number=5,
    )


def test_segment_extraction_with_total_validation() -> None:
    df = pd.DataFrame(
        {
            "Segment": ["Commercial Banking", "Consumer Banking", "Total"],
            "Revenue ($M)": ["430", "320", "750"],
        }
    )

    extractor = SegmentFactExtractor()
    facts = extractor.extract(
        sections=[_segment_section()],
        tables=[_segment_table(df)],
        normalized_text="",
        artifact_metadata={"url": "https://example.com/deck.pdf", "sha256": "def"},
    )

    assert facts["segment_revenue_commercial_banking"].value == 430_000_000
    assert facts["segment_revenue_consumer_banking"].value == 320_000_000
    assert facts["segment_revenue_total"].value == 750_000_000
    assert not facts["segment_revenue_total"].validation["warnings"]


def test_segment_validation_adds_warning_on_mismatch() -> None:
    df = pd.DataFrame(
        {
            "Segment": ["Commercial Banking", "Consumer Banking", "Total"],
            "Revenue ($M)": ["430", "320", "760"],
        }
    )

    extractor = SegmentFactExtractor()
    facts = extractor.extract(
        sections=[_segment_section()],
        tables=[_segment_table(df)],
        normalized_text="",
        artifact_metadata={"url": "https://example.com/deck.pdf", "sha256": "ghi"},
    )

    warnings = facts["segment_revenue_total"].validation["warnings"]
    assert warnings, "Expected mismatch warning when total row does not equal sum"
