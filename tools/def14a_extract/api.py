"""Public API surface for DEF 14A extraction."""

from __future__ import annotations

from typing import Dict, List, Sequence

from .config import ToolConfig, ensure_cache_dirs
from .fact_extraction import build_fact_extractors
from .fetchers.edgar_api import EdgarApiFetcher
from .fetchers.index_scraper import HtmlIndexFetcher
from .logging_utils import log_event
from .models import (
    DocumentProfile,
    FactCollection,
    FactCandidate,
    FactRequest,
    FilingIdentifier,
    FilingMetadata,
    TableExtractionResult,
)
from .normalizers.document_classifier import classify_artifact
from .provenance import ProvenanceAssembler
from .registry import load_registry
from .section_locator import SectionLocator
from .table_extraction import TableExtractionOrchestrator
from .validators import ValidationSuite

SECTION_IDS = [
    "meeting_overview",
    "beneficial_ownership",
    "executive_compensation",
    "audit_fees",
]


def get_def14a_facts(request: FactRequest) -> FactCollection:
    if not request.ticker and not request.cik:
        raise ValueError("Ticker or CIK is required")

    config = ToolConfig()
    ensure_cache_dirs(config)
    registry = load_registry()
    identifier = FilingIdentifier(
        ticker=request.ticker,
        cik=request.cik,
        year=request.year,
        form_type="DEF 14A",
    )

    api_fetcher = EdgarApiFetcher(config)
    metadata_list = api_fetcher.discover(identifier)

    if not metadata_list and identifier.cik:
        html_fetcher = HtmlIndexFetcher(config)
        metadata_list = html_fetcher.scrape(identifier)

    if not metadata_list:
        raise RuntimeError("No DEF 14A filings found for the supplied parameters")

    metadata = metadata_list[0]
    artifacts = api_fetcher.fetch(metadata, refresh=request.refresh)
    documents = [classify_artifact(artifact) for artifact in artifacts]

    section_locator = SectionLocator(SECTION_IDS)
    section_spans = section_locator.locate(documents)

    table_extractor = TableExtractionOrchestrator()
    tables: List[TableExtractionResult] = []
    for span in section_spans:
        tables.extend(table_extractor.extract(span, documents))

    fact_extractors = build_fact_extractors()
    fact_candidates: Dict[str, FactCandidate] = {}
    requested = set(request.facts or registry.keys())

    for extractor in fact_extractors:
        extracted = extractor.extract(section_spans, tables, documents, registry)
        for fact_id, candidate in extracted.items():
            if fact_id not in requested:
                continue
            fact_candidates[fact_id] = candidate

    validator = ValidationSuite()
    validation_report = validator.validate(fact_candidates)

    assembler = ProvenanceAssembler()
    fact_collection = assembler.attach(fact_candidates, validation_report, metadata)
    log_event("Produced DEF 14A facts", count=len(fact_collection))
    return fact_collection
