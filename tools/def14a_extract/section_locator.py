"""Locate canonical section spans within normalized documents."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

from lxml import html as lxml_html

from .heading_rerankers import deterministic, llm_reranker
from .logging_utils import log_event
from .models import DocumentProfile, SectionSpan
from .normalizers import pdf_text

# Capture visible headings plus bolded paragraph/div constructs that proxies often use.
HEADING_XPATH = (
    "//h1|//h2|//h3|//h4|//h5|//h6"
    "|//p[strong]|//p[b]|//div[strong]|//div[b]"
    "|//*[@role='heading']"
)


class SectionLocator:
    def __init__(self, section_ids: Sequence[str]) -> None:
        self._section_ids = section_ids

    def locate(self, documents: Sequence[DocumentProfile]) -> Sequence[SectionSpan]:
        spans: List[SectionSpan] = []
        for doc in documents:
            headings = list(_extract_headings(doc))
            if not headings:
                continue
            for section_id in self._section_ids:
                candidates = deterministic.find_heading_candidates(section_id, headings)
                if not candidates:
                    continue
                ranked = llm_reranker.rerank_candidates(section_id, candidates)
                best = ranked[0]
                spans.append(
                    SectionSpan(
                        section_id=section_id,
                        start_offset=best.start_offset,
                        end_offset=best.end_offset,
                        heading_text=best.heading_text,
                        score=best.score,
                        source="llm_rerank" if ranked != candidates else "deterministic",
                        dom_path=best.dom_path,
                    )
                )
        log_event("Section locator identified spans", count=len(spans))
        return spans


def _extract_headings(doc: DocumentProfile) -> Iterable[Tuple[str, int, int, Optional[str]]]:
    if doc.doc_type == "html":
        yield from _extract_html_headings(doc)
    elif doc.doc_type.startswith("pdf"):
        yield from _extract_pdf_headings(doc)
    else:
        yield from _extract_text_headings(doc)


def _extract_html_headings(doc: DocumentProfile) -> Iterable[Tuple[str, int, int, Optional[str]]]:
    try:
        tree = lxml_html.parse(str(doc.artifact.path)).getroot()
    except (OSError, ValueError):
        text = doc.artifact.path.read_text(errors="ignore")
        yield from _iter_headings_from_lines(text)
        return

    headings: List[Tuple[str, int, int, Optional[str]]] = []
    for idx, element in enumerate(tree.xpath(HEADING_XPATH)):
        text = " ".join(element.itertext()).strip()
        if not text or not _looks_like_heading(text):
            continue
        dom_path = tree.getroottree().getpath(element)
        headings.append((text, idx, idx, dom_path))

    if headings:
        yield from headings
    else:
        text = tree.text_content()
        yield from _iter_headings_from_lines(text)


def _extract_pdf_headings(doc: DocumentProfile) -> Iterable[Tuple[str, int, int, Optional[str]]]:
    pdf_data = pdf_text.extract_pdf_text(doc)
    text = "\n".join(pdf_data["pages"])
    yield from _iter_headings_from_lines(text)


def _extract_text_headings(doc: DocumentProfile) -> Iterable[Tuple[str, int, int, Optional[str]]]:
    text = doc.artifact.path.read_text(errors="ignore")
    yield from _iter_headings_from_lines(text)


def _iter_headings_from_lines(text: str) -> Iterable[Tuple[str, int, int, Optional[str]]]:
    offset = 0
    for idx, line in enumerate(text.splitlines()):
        cleaned = line.strip()
        if cleaned and _looks_like_heading(cleaned):
            start = offset
            end = offset + len(line)
            yield cleaned, start, end, None
        offset += len(line) + 1


def _looks_like_heading(text: str) -> bool:
    normalized = text.strip()
    if len(normalized) < 4:
        return False
    if normalized.isupper():
        return True
    if re.match(r"^[A-Z][A-Za-z0-9\s\-\&:]{3,}$", normalized) and len(normalized.split()) <= 18:
        return True
    if normalized.lower().startswith("proposal"):
        return True
    if "meeting" in normalized.lower() and len(normalized.split()) <= 25:
        return True
    return False
