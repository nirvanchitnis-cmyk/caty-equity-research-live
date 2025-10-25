from pathlib import Path

from tools.def14a_extract.fact_extraction.meeting import MeetingFactExtractor
from tools.def14a_extract.models import DocumentProfile, FilingArtifact
from tools.def14a_extract.section_locator import SectionLocator


def _build_html_proxy(tmp_path: Path) -> DocumentProfile:
    html_content = """
    <html>
      <body>
        <h2>NOTICE OF ANNUAL MEETING OF STOCKHOLDERS</h2>
        <p>The annual meeting will be held on Monday, May 12, 2025 at 5:00 p.m., Pacific Time,
        exclusively in a virtual meeting format. Stockholders of record at the close of business on
        March 25, 2025 may attend the virtual meeting at
        <a href="https://www.virtualshareholdermeeting.com/CATY2025">https://www.virtualshareholdermeeting.com/CATY2025</a>.
        </p>
        <h2>EXECUTIVE COMPENSATION</h2>
        <table>
          <tr><th>Name</th><th>Title</th><th>2024 Total</th></tr>
          <tr><td>Irene Oh</td><td>Chief Executive Officer</td><td>$6,500,000</td></tr>
        </table>
      </body>
    </html>
    """.strip()
    file_path = tmp_path / "proxy.html"
    file_path.write_text(html_content)
    artifact = FilingArtifact(
        url="https://example.com/proxy.html",
        path=file_path,
        sha256="abc123",
        mime_type="text/html",
        content_type="text/html",
    )
    return DocumentProfile(artifact=artifact, doc_type="html", confidence=0.95, page_count=None)


def test_section_locator_identifies_dom_paths(tmp_path):
    profile = _build_html_proxy(tmp_path)
    locator = SectionLocator(["meeting_overview", "executive_compensation"])
    spans = locator.locate([profile])
    ids = {span.section_id: span for span in spans}
    assert "meeting_overview" in ids
    assert ids["meeting_overview"].dom_path is not None
    assert ids["executive_compensation"].dom_path is not None


def test_meeting_extractor_uses_normalized_html(tmp_path):
    profile = _build_html_proxy(tmp_path)
    locator = SectionLocator(["meeting_overview"])
    spans = locator.locate([profile])
    extractor = MeetingFactExtractor()
    facts = extractor.extract(spans, [], [profile], {})
    assert "meeting_date" in facts
    assert facts["meeting_date"].value == "2025-05-12"
    assert "record_date" in facts
    assert facts["record_date"].value == "2025-03-25"
    assert facts["meeting_location_type"].value == "virtual-only"
    assert facts["meeting_access_url"].value.startswith("https://www.virtualshareholdermeeting.com")
