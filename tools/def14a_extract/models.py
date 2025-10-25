"""Shared dataclasses and type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Sequence

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class FilingIdentifier:
    cik: Optional[str] = None
    ticker: Optional[str] = None
    year: Optional[int] = None
    form_type: str = "DEF 14A"


@dataclass(frozen=True)
class FilingMetadata:
    accession_number: str
    filing_date: str
    form_type: str
    primary_document_url: str
    exhibit_urls: Sequence[str] = field(default_factory=list)


@dataclass(frozen=True)
class FilingArtifact:
    url: str
    path: Path
    sha256: str
    mime_type: str
    content_type: str


@dataclass(frozen=True)
class DocumentProfile:
    artifact: FilingArtifact
    doc_type: str
    confidence: float
    page_count: Optional[int] = None


@dataclass(frozen=True)
class SectionSpan:
    section_id: str
    start_offset: int
    end_offset: int
    heading_text: str
    score: float
    source: str
    dom_path: Optional[str] = None


@dataclass
class FactCandidate:
    fact_id: str
    value: object
    value_type: str
    unit: Optional[str]
    anchors: Sequence[SectionSpan]
    extraction_path: Mapping[str, object]
    method: str
    confidence_components: Mapping[str, float]


@dataclass
class ValidationReport:
    warnings: Sequence[str] = field(default_factory=list)
    adjustments: Mapping[str, float] = field(default_factory=dict)
    invalid_facts: Sequence[str] = field(default_factory=list)


@dataclass
class FactWithProvenance:
    value: object
    value_type: str
    unit: Optional[str]
    fiscal_year: Optional[int]
    issuer_cik: Optional[str]
    filing_accession: str
    source_url: str
    file_sha256: str
    page_numbers: Sequence[int]
    dom_path: Optional[str]
    table_id: Optional[str]
    method: str
    confidence: float
    validation: Mapping[str, Sequence[str]]


@dataclass
class FactRequest:
    ticker: Optional[str] = None
    cik: Optional[str] = None
    year: Optional[int] = None
    facts: Optional[Sequence[str]] = None
    include_provenance: bool = False
    refresh: bool = False
    output_path: Optional[Path] = None


FactCollection = Dict[str, FactWithProvenance]


@dataclass
class TableExtractionResult:
    section_id: str
    table_id: str
    dataframe: "pd.DataFrame"  # type: ignore[name-defined]
    raw_snapshot_path: Path
    source_method: str
    quality_score: float
    source_url: str
    sha256: str
