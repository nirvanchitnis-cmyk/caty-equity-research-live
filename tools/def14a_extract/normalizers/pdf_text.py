"""PDF text extraction utilities."""

from __future__ import annotations

from typing import Dict, List

try:  # pragma: no cover - optional dependency guard
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore

from ..logging_utils import log_event
from ..models import DocumentProfile


def extract_pdf_text(profile: DocumentProfile) -> Dict[str, object]:
    pages: List[str] = []
    layout_tokens: List[Dict[str, str]] = []
    stats = {"page_count": 0, "text_pages": 0}
    if not pdfplumber:
        log_event("pdfplumber not installed; skipping PDF text extraction", url=profile.artifact.url)
        return {"pages": pages, "layout_tokens": layout_tokens, "stats": stats}
    with pdfplumber.open(str(profile.artifact.path)) as pdf:
        stats["page_count"] = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                stats["text_pages"] += 1
            pages.append(text)
            layout_tokens.append({"width": str(page.width), "height": str(page.height)})
    if stats["page_count"] and stats["text_pages"] / stats["page_count"] < 0.2:
        log_event("Low text yield from PDF, OCR suggested", url=profile.artifact.url)
    return {
        "pages": pages,
        "layout_tokens": layout_tokens,
        "stats": stats,
    }
