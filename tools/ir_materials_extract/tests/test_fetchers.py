import asyncio
from pathlib import Path

import httpx

from tools.ir_materials_extract.cache import get_cached_entry
from tools.ir_materials_extract.config import ToolConfig
from tools.ir_materials_extract.fetchers.http_fetcher import fetch_artifact
from tools.ir_materials_extract.normalizers.html_normalizer import normalize_html
from tools.ir_materials_extract.normalizers import pdf_normalizer


class DummyAsyncClient:
    """Simple AsyncClient stand-in for controlled HTTP responses."""

    call_count = 0

    def __init__(self, *_, **__):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str) -> httpx.Response:
        DummyAsyncClient.call_count += 1
        content = f"<html><body>Payload for {url}</body></html>".encode()
        return httpx.Response(
            status_code=200,
            content=content,
            headers={"Content-Type": "text/html"},
        )


def test_fetcher_uses_cache(tmp_path: Path, monkeypatch) -> None:
    config = ToolConfig(
        cache_dir=tmp_path / "cache",
        cache_db=tmp_path / "cache" / "index.sqlite3",
        max_retries=2,
    )

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)
    DummyAsyncClient.call_count = 0

    url = "https://example.com/ir/test"

    first = asyncio.run(fetch_artifact(url, config=config))
    assert first.success
    assert first.file_path and first.file_path.exists()
    assert DummyAsyncClient.call_count == 1

    cached = get_cached_entry(url, config=config)
    assert cached is not None

    second = asyncio.run(fetch_artifact(url, config=config))
    assert second.success
    assert DummyAsyncClient.call_count == 1  # cache hit, no extra request


def test_html_normalizer() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_ir_page.html"
    payload = normalize_html(fixture)
    assert "Investor Relations" in payload["text"]
    assert payload["title"] == "Sample IR Page"
    assert any("press" in link for link in payload["links"])


def test_pdf_normalizer_stub(monkeypatch, tmp_path: Path) -> None:
    sample_pages = [
        {"page_num": 1, "text": "Hello IR", "char_count": 7},
        {"page_num": 2, "text": "Second page", "char_count": 11},
    ]

    monkeypatch.setattr(
        pdf_normalizer, "_extract_with_pdfplumber", lambda path: sample_pages
    )
    monkeypatch.setattr(pdf_normalizer, "_fallback_extract", lambda path: [])

    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-FAKE")

    result = pdf_normalizer.normalize_pdf(pdf_path)
    assert "Hello IR" in result["text"]
    assert result["text_yield"] >= 9
    assert result["needs_ocr"] is True
