import types
from pathlib import Path

import pandas as pd

from tools.ir_materials_extract.table_extraction import html_tables, pdf_tables


FIXTURES = Path(__file__).parent / "fixtures"


class StubCamelotTable:
    def __init__(self, dataframe: pd.DataFrame, page: int = 1):
        self.df = dataframe
        self.page = str(page)


def test_extract_pdf_tables_with_camelot(monkeypatch) -> None:
    pdf_path = FIXTURES / "sample_earnings_deck.pdf"
    dataframe = pd.DataFrame(
        {
            "Metric": ["Revenue", "Net Income"],
            "Q2 2025": ["750", "210"],
        }
    )

    dummy_module = types.SimpleNamespace(
        read_pdf=lambda *_args, **_kwargs: [StubCamelotTable(dataframe)]
    )
    monkeypatch.setattr(pdf_tables, "camelot", dummy_module, raising=False)
    monkeypatch.setattr(pdf_tables, "tabula", None, raising=False)

    results = pdf_tables.extract_pdf_tables(pdf_path)
    assert len(results) == 1
    result = results[0]
    assert result.method == "camelot_lattice"
    assert result.page_number == 1
    assert list(result.dataframe.columns) == ["Metric", "Q2 2025"]
    assert 0.0 < result.confidence <= 1.0


def test_extract_pdf_tables_falls_back_to_tabula(monkeypatch) -> None:
    pdf_path = FIXTURES / "sample_earnings_deck.pdf"

    stream_df = pd.DataFrame(
        {"Segment": ["Commercial", "Consumer"], "Revenue": ["430", "320"]}
    )

    monkeypatch.setattr(
        pdf_tables,
        "camelot",
        types.SimpleNamespace(read_pdf=lambda *_args, **_kwargs: []),
        raising=False,
    )
    monkeypatch.setattr(
        pdf_tables,
        "tabula",
        types.SimpleNamespace(read_pdf=lambda *_args, **_kwargs: [stream_df]),
        raising=False,
    )

    results = pdf_tables.extract_pdf_tables(pdf_path)
    assert len(results) == 1
    result = results[0]
    assert result.method == "tabula_stream"
    assert result.dom_selector is None
    assert 0.0 < result.confidence <= 1.0


def test_extract_html_tables() -> None:
    html_path = FIXTURES / "sample_press_release.html"
    results = html_tables.extract_html_tables(html_path)
    assert len(results) == 2

    first = results[0]
    assert first.method == "pandas_html"
    assert first.dom_selector == "table:nth-of-type(1)"
    assert "Financial Highlights" in first.raw_html
    assert list(first.dataframe.columns) == ["Metric", "Q2 2025", "Q2 2024"]
    assert first.confidence > 0.2

    second = results[1]
    assert second.dataframe.iloc[1, 0] == "Consumer Banking"
    assert second.confidence > 0.2

def test_extract_html_tables_with_no_tables() -> None:
    html_path = FIXTURES / "sample_press_release_no_tables.html"
    results = html_tables.extract_html_tables(html_path)
    assert results == []
