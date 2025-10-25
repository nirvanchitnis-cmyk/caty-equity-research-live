"""Locate canonical section spans within normalized documents."""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Tuple

from .heading_rerankers import deterministic, llm_reranker
from .logging_utils import log_event
from .models import DocumentProfile, SectionSpan
from .normalizers import pdf_text


class SectionLocator:
    def __init__(self, section_ids: Sequence[str]) -> None:
        self._section_ids = section_ids

    def locate(self, documents: Sequence[DocumentProfile]) -> Sequence[SectionSpan]:
        spans: List[SectionSpan] = []
        for doc in documents:
            headings = list(_extract_headings(doc))
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
                    )
                )
        log_event("Section locator identified spans", count=len(spans))
        return spans


def _extract_headings(doc: DocumentProfile) -> Iterable[Tuple[str, int, int]]:
    if doc.doc_type == "html":
        text = doc.artifact.path.read_text(errors="ignore")
    elif doc.doc_type.startswith("pdf"):
        pdf_data = pdf_text.extract_pdf_text(doc)
        text = "\n".join(pdf_data["pages"])
    else:
        text = doc.artifact.path.read_text(errors="ignore")
    offset = 0
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            offset += len(line) + 1
            continue
        if _looks_like_heading(cleaned):
            start = offset
            end = offset + len(line)
            yield cleaned, start, end
        offset += len(line) + 1


def _looks_like_heading(text: str) -> bool:
    if len(text) < 4:
        return False
    if text.isupper():
        return True
    if re.match(r"^[A-Z][A-Za-z\s]{3,}$", text) and len(text.split()) <= 10:
        return True
    if text.lower().startswith("proposal"):
        return True
    return False
