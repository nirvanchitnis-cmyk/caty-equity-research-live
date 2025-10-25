"""Fallback HTML index scraper for SEC filings."""

from __future__ import annotations

from typing import List

import httpx
from bs4 import BeautifulSoup

from ..config import ToolConfig
from ..logging_utils import log_event
from ..models import FilingIdentifier, FilingMetadata
from ..throttling import RateLimiter, build_retry_decorator


class HtmlIndexFetcher:
    def __init__(self, config: ToolConfig) -> None:
        self._config = config
        self._limiter = RateLimiter(config)
        self._retry = build_retry_decorator(config.retry_attempts)

    def scrape(self, identifier: FilingIdentifier) -> List[FilingMetadata]:
        if not identifier.cik:
            raise ValueError("CIK required for index scraping")
        year = identifier.year or ""
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={identifier.cik}&type=DEF%2014A&dateb={year}&owner=exclude&count=100"

        @self._retry
        def _scrape() -> List[FilingMetadata]:
            with self._limiter.limit():
                headers = {"User-Agent": self._config.user_agent}
                log_event("Scraping EDGAR HTML index", url=url)
                with httpx.Client(timeout=self._config.timeout_seconds) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", class_="tableFile2")
            if not table:
                return []
            rows = table.find_all("tr")
            metadata: List[FilingMetadata] = []
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                form_type = cells[0].get_text(strip=True)
                if "14A" not in form_type:
                    continue
                filing_date = cells[3].get_text(strip=True)
                link = cells[1].find("a")
                if not link:
                    continue
                href = link["href"]
                primary_url = f"https://www.sec.gov{href}"
                accession_number = href.split("/")[-2]
                metadata.append(
                    FilingMetadata(
                        accession_number=accession_number,
                        filing_date=filing_date,
                        form_type=form_type,
                        primary_document_url=primary_url,
                        exhibit_urls=[],
                    )
                )
            return metadata

        return _scrape()
