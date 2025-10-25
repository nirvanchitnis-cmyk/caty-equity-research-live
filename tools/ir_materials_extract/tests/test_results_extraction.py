import pandas as pd

from tools.ir_materials_extract.fact_extraction.results import ResultsFactExtractor
from tools.ir_materials_extract.section_locators.models import SectionSpan
from tools.ir_materials_extract.table_extraction.models import TableExtractionResult



def _mock_table(df: pd.DataFrame) -> TableExtractionResult:
    return TableExtractionResult(
        table_id="tbl-1",
        source_file="sample.pdf",
        method="camelot_lattice",
        dataframe=df,
        confidence=0.95,
        page_number=2,
    )


def _financial_highlights_section() -> SectionSpan:
    return SectionSpan(
        section_id="financial_highlights",
        start_offset=0,
        end_offset=100,
        heading_text="Financial Highlights",
        confidence=0.9,
        source_file="sample.pdf",
        page_number=2,
    )


def test_extract_revenue_and_eps_from_table() -> None:
    df = pd.DataFrame(
        {
            "Metric": ["Q2 2025"],
            "Revenue ($M)": ["200"],
            "Non-GAAP EPS": ["0.45"],
            "GAAP EPS": ["0.39"],
        }
    )

    extractor = ResultsFactExtractor()
    facts = extractor.extract(
        sections=[_financial_highlights_section()],
        tables=[_mock_table(df)],
        normalized_text="",
        artifact_metadata={"url": "https://example.com/pr.pdf", "sha256": "abc"},
    )

    assert facts["revenue_total"].value == 200_000_000
    assert facts["revenue_total"].confidence > 0.8
    assert facts["eps_non_gaap"].value == 0.45
    assert facts["eps_gaap"].value == 0.39


def test_missing_headers_returns_partial_results() -> None:
    df = pd.DataFrame(
        {
            "Metric": ["Q2 2025"],
            "Total Revenue": ["$320"],
        }
    )

    extractor = ResultsFactExtractor()
    facts = extractor.extract(
        sections=[_financial_highlights_section()],
        tables=[_mock_table(df)],
        normalized_text="",
        artifact_metadata={"url": "https://example.com/pr.pdf", "sha256": "abc"},
    )

    assert "revenue_total" in facts
    assert "eps_non_gaap" not in facts
