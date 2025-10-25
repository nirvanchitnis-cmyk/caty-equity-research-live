"""SEC data API fetchers."""

from __future__ import annotations

import datetime as dt
from typing import List, Optional, Sequence

import httpx

from ..cache import ArtifactCacheManager
from ..config import ToolConfig
from ..logging_utils import log_event
from ..models import FilingArtifact, FilingIdentifier, FilingMetadata
from ..throttling import RateLimiter, build_retry_decorator
from .artifact_downloader import ArtifactDownloader

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no}"


class EdgarApiFetcher:
    def __init__(self, config: ToolConfig) -> None:
        self._config = config
        self._limiter = RateLimiter(config)
        self._retry = build_retry_decorator(config.retry_attempts)
        self._downloader = ArtifactDownloader(config, ArtifactCacheManager(config))

    def _resolve_cik(self, identifier: FilingIdentifier) -> Optional[int]:
        ticker = identifier.ticker
        if identifier.cik:
            try:
                return int(identifier.cik)
            except ValueError:
                return None
        if not ticker:
            return None
        url = f"https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": self._config.user_agent}
        with httpx.Client(timeout=self._config.timeout_seconds) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        for record in data.values():
            if record["ticker"].lower() == ticker.lower():
                return int(record["cik_str"])
        return None

    def discover(self, identifier: FilingIdentifier) -> List[FilingMetadata]:
        cik = self._resolve_cik(identifier)
        if cik is None:
            raise ValueError("Unable to resolve CIK")

        url = SEC_SUBMISSIONS_URL.format(cik=cik)

        @self._retry
        def _fetch_submissions() -> List[FilingMetadata]:
            with self._limiter.limit():
                headers = {"User-Agent": self._config.user_agent}
                log_event("Fetching SEC submissions", cik=cik)
                with httpx.Client(timeout=self._config.timeout_seconds) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
            filings = data.get("filings", {}).get("recent", {})
            results: List[FilingMetadata] = []
            accession_numbers = filings.get("accessionNumber", [])
            filing_dates = filings.get("filingDate", [])
            forms = filings.get("form", [])
            primary_docs = filings.get("primaryDocument", [])

            for idx, (accession, filing_date, form) in enumerate(
                zip(accession_numbers, filing_dates, forms)
            ):
                if not form or "14A" not in form:
                    continue
                if identifier.year:
                    filing_year = int(filing_date.split("-")[0])
                    if filing_year != identifier.year:
                        continue
                accession_clean = accession.replace("-", "")
                primary = primary_docs[idx] if idx < len(primary_docs) else ""
                if not primary:
                    primary = "index.htm"
                primary_url = f"{SEC_ARCHIVES_BASE.format(cik=cik, accession_no=accession_clean)}/{primary}"
                metadata = FilingMetadata(
                    accession_number=accession,
                    filing_date=filing_date,
                    form_type=form,
                    primary_document_url=primary_url,
                    exhibit_urls=[],
                )
                results.append(metadata)
            results.sort(key=lambda meta: meta.filing_date, reverse=True)
            return results

        return _fetch_submissions()

    def fetch(
        self,
        metadata: FilingMetadata,
        refresh: bool = False,
    ) -> List[FilingArtifact]:
        urls: Sequence[str] = [metadata.primary_document_url, *metadata.exhibit_urls]
        artifacts = self._downloader.bulk_download(urls, refresh=refresh)
        return artifacts
