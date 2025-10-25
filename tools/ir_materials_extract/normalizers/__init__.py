"""Content normalizers for IR artifacts."""

from .html_normalizer import normalize_html
from .pdf_normalizer import normalize_pdf

__all__ = ["normalize_html", "normalize_pdf"]
