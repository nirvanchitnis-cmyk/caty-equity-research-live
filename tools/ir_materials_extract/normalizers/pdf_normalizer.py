"""Normalize PDF artifacts into text payloads (no OCR in Phase 1)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:
    import pdfplumber
except ImportError:  # pragma: no cover - optional dependency missing at runtime.
    pdfplumber = None  # type: ignore

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:  # pragma: no cover - optional dependency missing at runtime.
    pdfminer_extract_text = None  # type: ignore


def _extract_with_pdfplumber(pdf_path: Path) -> List[Dict[str, object]]:
    pages: List[Dict[str, object]] = []
    if not pdfplumber:
        return pages
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(
                {
                    "page_num": page_index,
                    "text": text,
                    "char_count": len(text),
                }
            )
    return pages


def _fallback_extract(pdf_path: Path) -> List[Dict[str, object]]:
    if not pdfminer_extract_text:
        return []
    text = pdfminer_extract_text(str(pdf_path)) or ""
    if not text:
        return []
    return [
        {
            "page_num": 1,
            "text": text,
            "char_count": len(text),
        }
    ]


def normalize_pdf(pdf_path: Path) -> Dict[str, object]:
    """Return text payload, per-page data, and heuristics for PDF artifacts."""
    pages = _extract_with_pdfplumber(pdf_path)
    if not pages:
        pages = _fallback_extract(pdf_path)

    full_text = "\n".join(page["text"] for page in pages if page["text"]) if pages else ""
    total_chars = sum(page.get("char_count", 0) for page in pages)
    page_count = len(pages) or 1
    text_yield = total_chars / page_count if page_count else 0.0

    metadata: Dict[str, object] = {}
    if pdfplumber:
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                metadata = pdf.metadata or {}
        except Exception:  # pragma: no cover - best-effort metadata extraction.
            metadata = {}

    result = {
        "text": full_text,
        "pages": pages,
        "text_yield": float(text_yield),
        "metadata": metadata,
    }

    if page_count > 0 and text_yield < 50:
        result["needs_ocr"] = True
    else:
        result["needs_ocr"] = False

    return result


__all__ = ["normalize_pdf"]
