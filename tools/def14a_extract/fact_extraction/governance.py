"""Governance-related fact extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .base import BaseFactExtractor
from ..models import DocumentProfile, FactCandidate, SectionSpan, TableExtractionResult


class GovernanceFactExtractor(BaseFactExtractor):
    """Extract board composition facts (total nominees, independent nominees)."""

    fact_ids = ["director_nominees_total", "director_nominees_independent"]

    QUOTE_CLASS = "\"'“”‘’"

    FALLBACK_PATTERNS: Mapping[str, Sequence[str]] = {
        "director_nominees_total": (
            r"consists of (?P<count>[\w\-]+)\s+directors",
            r"consist of (?P<count>[\w\-]+)\s+directors",
            r"expected to consist of (?P<count>[\w\-]+)\s+directors",
        ),
        "director_nominees_independent": (
            fr"of which (?P<count>[\w\-]+)\s+(?:will be|are)\s+(?:considered\s+)?[{QUOTE_CLASS}]?independent",
            fr"(?P<count>[\w\-]+)\s+(?:independent directors|independent members)",
            fr"(?P<count>[\w\-]+)\s+are\s+independent\s+directors",
        ),
    }

    NUMBER_WORDS: Mapping[str, int] = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
    }

    def extract(
        self,
        section_spans: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        documents: Sequence[DocumentProfile],
        registry: Dict,
    ) -> Dict[str, FactCandidate]:
        spans_by_id = {span.section_id: span for span in section_spans}
        target_span = (
            spans_by_id.get("election_of_directors")
            or spans_by_id.get("meeting_overview")
            or spans_by_id.get("beneficial_ownership")
        )
        if not target_span:
            return {}

        text_cache = self._build_text_cache(documents)
        if not text_cache:
            return {}

        section_text, provenance_hint = self._get_section_text(target_span, text_cache)
        if not section_text.strip():
            return {}

        results: Dict[str, FactCandidate] = {}

        text_sources = [section_text] + [text for _, text in text_cache]

        total_value, total_snippet = self._extract_with_patterns(
            text_sources,
            self._registry_patterns("director_nominees_total", registry),
        )
        if total_value is not None:
            results["director_nominees_total"] = FactCandidate(
                fact_id="director_nominees_total",
                value=total_value,
                value_type="integer",
                unit=None,
                anchors=[target_span],
                extraction_path={
                    "section": target_span.section_id,
                    "source_text_snippet": total_snippet,
                    "source_url": provenance_hint.get("source_url"),
                    "sha256": provenance_hint.get("sha256"),
                    "dom_path": target_span.dom_path,
                },
                method="regex",
                confidence_components={
                    "source": 0.90,
                    "parser": 0.90,
                    "header": 0.90 if target_span.section_id == "election_of_directors" else 0.80,
                    "validation": 0.95,
                    "provenance": 0.90,
                },
            )

        indep_value, indep_snippet = self._extract_with_patterns(
            text_sources,
            self._registry_patterns("director_nominees_independent", registry),
        )
        if indep_value is not None:
            results["director_nominees_independent"] = FactCandidate(
                fact_id="director_nominees_independent",
                value=indep_value,
                value_type="integer",
                unit=None,
                anchors=[target_span],
                extraction_path={
                    "section": target_span.section_id,
                    "source_text_snippet": indep_snippet,
                    "source_url": provenance_hint.get("source_url"),
                    "sha256": provenance_hint.get("sha256"),
                    "dom_path": target_span.dom_path,
                },
                method="regex",
                confidence_components={
                    "source": 0.90,
                    "parser": 0.85,
                    "header": 0.95 if target_span.section_id == "election_of_directors" else 0.80,
                    "validation": 0.90,
                    "provenance": 0.85,
                },
            )

        return results

    def _build_text_cache(
        self,
        documents: Sequence[DocumentProfile],
    ) -> List[Tuple[DocumentProfile, str]]:
        cache: List[Tuple[DocumentProfile, str]] = []
        for document in documents:
            text = self._extract_document_text(document)
            if text:
                cache.append((document, text))
        return cache

    def _registry_patterns(
        self,
        fact_id: str,
        registry: Mapping[str, object],
    ) -> Sequence[str]:
        fact_entry = registry.get(fact_id, {}) if isinstance(registry, Mapping) else {}
        patterns: List[str] = []
        if isinstance(fact_entry, Mapping):
            pattern_defs = fact_entry.get("patterns", [])
            if isinstance(pattern_defs, Sequence):
                for pattern_def in pattern_defs:
                    if isinstance(pattern_def, Mapping):
                        regex = pattern_def.get("regex")
                        if isinstance(regex, str) and regex.strip():
                            patterns.append(regex)
        patterns.extend(self.FALLBACK_PATTERNS.get(fact_id, ()))
        return patterns

    def _extract_with_patterns(
        self,
        texts: Sequence[str],
        patterns: Sequence[str],
    ) -> Tuple[Optional[int], Optional[str]]:
        for text in texts:
            if not text:
                continue
            for pattern in patterns:
                if not pattern:
                    continue
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if not match:
                    continue
                groupdict = match.groupdict()
                raw_value = groupdict.get("count") if "count" in groupdict else match.group(0)
                if raw_value is None:
                    continue
                try:
                    value = self._parse_number(raw_value)
                except ValueError:
                    continue
                snippet = match.group(0).strip()
                return value, snippet
        return None, None

    def _parse_number(self, raw: str) -> int:
        digits = re.findall(r"\d+", raw.replace(",", ""))
        if digits:
            return int(digits[0])
        cleaned = re.sub(r"[^\w\-]", " ", raw).strip().lower()
        cleaned = cleaned.replace("-", " ")
        tokens = cleaned.split()
        if not tokens:
            raise ValueError(f"Cannot parse number from '{raw}'")
        if len(tokens) == 1 and tokens[0] in self.NUMBER_WORDS:
            return self.NUMBER_WORDS[tokens[0]]
        if len(tokens) == 2 and all(token in self.NUMBER_WORDS for token in tokens):
            return self.NUMBER_WORDS[tokens[0]] + self.NUMBER_WORDS[tokens[1]]
        if tokens[0] in self.NUMBER_WORDS:
            return self.NUMBER_WORDS[tokens[0]]
        raise ValueError(f"Cannot parse number from '{raw}'")

    def _extract_document_text(self, document: DocumentProfile) -> str:
        try:
            if document.doc_type == "html":
                from ..normalizers.html_normalizer import normalize_html

                return str(normalize_html(document).get("text", ""))
            if document.doc_type.startswith("pdf"):
                from ..normalizers.pdf_text import extract_pdf_text

                pdf_data = extract_pdf_text(document)
                pages = pdf_data.get("pages", [])
                if pages and any(page.strip() for page in pages):
                    return "\n".join(pages)
                try:
                    from ..normalizers.ocr_pipeline import run_ocr
                except ImportError:
                    return "\n".join(pages)
                ocr_data = run_ocr(document)
                return "\n".join(ocr_data.get("pages", []))
        except Exception:  # noqa: BLE001
            return ""
        try:
            return document.artifact.path.read_text(errors="ignore")
        except OSError:
            return ""

    def _get_section_text(
        self,
        span: SectionSpan,
        cache: Sequence[Tuple[DocumentProfile, str]],
    ) -> Tuple[str, Dict[str, object]]:
        heading_raw = (span.heading_text or "").strip()
        heading_lower = heading_raw.lower()
        keywords = [
            "of which eight will be considered",
            "expected to consist of",
            "board currently consists of",
            heading_lower,
            "proposal one",
            "election of directors",
        ]
        keywords = [kw for kw in keywords if kw]

        fallback_text = ""
        fallback_meta: Dict[str, object] = {}

        for document, text in cache:
            if not fallback_text:
                fallback_text = text
                fallback_meta = {
                    "source_url": document.artifact.url,
                    "sha256": document.artifact.sha256,
                    "dom_path": span.dom_path,
                }

            text_lower = text.lower()
            text_lower = (
                text_lower.replace("\u2014", " ")
                .replace("\u2013", " ")
                .replace("\u2012", " ")
                .replace("\u2010", " ")
                .replace("\u00a0", " ")
            )

            for keyword in keywords:
                normalized = (
                    keyword.replace("\u2014", " ")
                    .replace("\u2013", " ")
                    .replace("\u2012", " ")
                    .replace("\u2010", " ")
                )
                tokens = [token for token in re.split(r"\s+", normalized) if token]
                if not tokens:
                    continue
                pattern = r"\s+".join(re.escape(token) for token in tokens)
                for match in re.finditer(pattern, text_lower):
                    context_start = max(0, match.start() - 200)
                    context = text_lower[context_start:match.start()]
                    if "table of contents" in context:
                        continue
                    idx = match.start()
                    start = max(0, idx - 500)
                    end = min(len(text), idx + 12000)
                    return text[start:end], {
                        "source_url": document.artifact.url,
                        "sha256": document.artifact.sha256,
                        "dom_path": span.dom_path,
                    }

        return fallback_text, fallback_meta
