from tools.ir_materials_extract.fact_extraction.guidance import GuidanceFactExtractor
from tools.ir_materials_extract.section_locators.models import SectionSpan


def test_guidance_revenue_extraction() -> None:
    extractor = GuidanceFactExtractor()

    guidance_text = (
        "Outlook for Q4 2025\n\n"
        "We expect revenue to be in the range of $1.2 billion to $1.3 billion. "
        "Non-GAAP EPS is expected to be $0.45 to $0.50."
    )

    sections = [
        SectionSpan(
            section_id="guidance",
            start_offset=0,
            end_offset=len(guidance_text),
            heading_text="Outlook for Q4 2025",
            confidence=0.9,
            source_file="test.html",
            page_number=None,
        )
    ]

    artifact_metadata = {
        "url": "https://example.com/earnings.html",
        "sha256": "abc123",
        "doc_type": "press_release",
    }

    facts = extractor.extract(sections, [], guidance_text, artifact_metadata)

    assert "guidance_revenue_low" in facts
    assert "guidance_revenue_high" in facts
    assert "guidance_revenue_mid" in facts

    assert facts["guidance_revenue_low"].value == 1_200_000_000
    assert facts["guidance_revenue_high"].value == 1_300_000_000
    assert facts["guidance_revenue_mid"].value == 1_250_000_000

    assert facts["guidance_revenue_low"].confidence >= 0.8
    assert facts["guidance_revenue_mid"].method == "calculated"
