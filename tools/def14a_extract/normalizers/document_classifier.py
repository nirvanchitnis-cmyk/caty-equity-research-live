"""Determine artifact type confidence scores."""

from __future__ import annotations

import mimetypes
from pathlib import Path

try:  # pragma: no cover - optional dependency guard
    from pdfminer.pdfparser import PDFSyntaxError
except ImportError:  # pragma: no cover
    PDFSyntaxError = Exception  # type: ignore

try:  # pragma: no cover - optional dependency guard
    from PyPDF2 import PdfReader  # type: ignore
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore

from ..logging_utils import log_event
from ..models import DocumentProfile, FilingArtifact


def sniff_content_type(artifact: FilingArtifact) -> str:
    if artifact.content_type:
        return artifact.content_type
    guessed, _ = mimetypes.guess_type(artifact.url)
    return guessed or "application/octet-stream"


def classify_artifact(artifact: FilingArtifact) -> DocumentProfile:
    content_type = sniff_content_type(artifact)
    path = Path(artifact.path)
    doc_type = "text"
    confidence = 0.6
    page_count = None
    if content_type in ("text/html", "application/xhtml+xml"):
        doc_type = "html"
        confidence = 0.95
    elif content_type in ("text/plain",):
        doc_type = "text"
        confidence = 0.8
    elif content_type in ("application/pdf",):
        doc_type = "pdf_native"
        confidence = 0.9
        try:
            if not PdfReader:
                raise ImportError("PyPDF2 not installed")
            reader = PdfReader(str(path))
            page_count = len(reader.pages)
            if all((page.extract_text() or "").strip() == "" for page in reader.pages[:3]):
                doc_type = "pdf_scanned"
                confidence = 0.6
        except (PDFSyntaxError, Exception):  # broad except to degrade gracefully
            doc_type = "pdf_scanned"
            confidence = 0.4
    else:
        log_event("Unknown content type", url=artifact.url, content_type=content_type)

    return DocumentProfile(
        artifact=artifact,
        doc_type=doc_type,
        confidence=confidence,
        page_count=page_count,
    )
