"""OCR fallback pipeline using OCRmyPDF and Tesseract."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, List

try:
    import ocrmypdf  # type: ignore
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover - optional dependency guard
    ocrmypdf = None  # type: ignore
    pytesseract = None  # type: ignore
    Image = None  # type: ignore
    convert_from_path = None  # type: ignore

from ..logging_utils import log_event
from ..models import DocumentProfile


def run_ocr(profile: DocumentProfile) -> Dict[str, object]:
    if not all([ocrmypdf, pytesseract, convert_from_path, Image]):
        raise RuntimeError("OCR dependencies not installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_pdf = Path(tmpdir) / "ocr_input.pdf"
        tmp_pdf.write_bytes(profile.artifact.path.read_bytes())
        ocr_output = Path(tmpdir) / "ocr_output.pdf"
        ocrmypdf.ocr(
            str(tmp_pdf),
            str(ocr_output),
            deskew=True,
            rotate_pages=True,
            optimize=1,
            output_type="pdf",
        )
        images = convert_from_path(str(ocr_output))
        pages: List[str] = []
        hocr: List[str] = []
        confidences: List[float] = []
        for image in images:
            text = pytesseract.image_to_string(image)
            hocr_content = pytesseract.image_to_pdf_or_hocr(image, extension="hocr")
            hocr_text = hocr_content.decode("utf-8", errors="ignore")
            pages.append(text)
            hocr.append(hocr_text)
            confidences.append(_estimate_confidence(image))
        log_event("OCR completed", url=profile.artifact.url, pages=len(pages))
    return {
        "pages": pages,
        "hocr": hocr,
        "confidence_by_page": confidences,
    }


def _estimate_confidence(image: "Image.Image") -> float:
    if not pytesseract:
        return 0.0
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    confidences = [float(c) for c in data.get("conf", []) if c != "-1"]
    if not confidences:
        return 0.0
    return sum(confidences) / (len(confidences) * 100.0)
