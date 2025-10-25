from pathlib import Path

from tools.ir_materials_extract.normalizers.html_normalizer import normalize_html
from tools.ir_materials_extract.section_locators import locate_sections


FIXTURES = Path(__file__).parent / "fixtures"


def test_locate_sections_in_press_release() -> None:
    html_path = FIXTURES / "sample_press_release.html"
    normalized = normalize_html(html_path)
    text = normalized["text"]

    spans = locate_sections(text, source_file=str(html_path))

    section_ids = {span.section_id for span in spans}
    assert "financial_highlights" in section_ids
    assert "segment_results" in section_ids

    guidance_spans = [span for span in spans if span.section_id == "guidance"]
    assert len(guidance_spans) == 1
    assert guidance_spans[0].start_offset > 0
    assert "Outlook for Q4 2025" in guidance_spans[0].heading_text

    highlights = next(span for span in spans if span.section_id == "financial_highlights")
    assert highlights.start_offset < highlights.end_offset
    assert "Financial Highlights" in highlights.heading_text
    assert 0.5 <= highlights.confidence <= 1.0


def test_locate_sections_with_empty_text() -> None:
    spans = locate_sections("", source_file="empty.html")
    assert spans == []
