"""Low-level download helpers for SEC artifacts."""

from __future__ import annotations

import mimetypes
from typing import Iterable, List, Sequence

import httpx

from ..cache import ArtifactCacheManager
from ..config import ToolConfig
from ..logging_utils import log_event
from ..models import FilingArtifact
from ..throttling import RateLimiter, build_retry_decorator


class ArtifactDownloader:
    def __init__(self, config: ToolConfig, cache: ArtifactCacheManager) -> None:
        self._config = config
        self._cache = cache
        self._limiter = RateLimiter(config)
        self._retry = build_retry_decorator(config.retry_attempts)

    def download(self, url: str, refresh: bool = False) -> FilingArtifact:
        cached = None if refresh else self._cache.get(url)
        if cached:
            return cached

        @self._retry
        def _make_request() -> FilingArtifact:
            with self._limiter.limit():
                headers = {
                    "User-Agent": self._config.user_agent,
                    "Accept": "*/*",
                }
                log_event("Fetching artifact", url=url)
                with httpx.Client(
                    timeout=self._config.timeout_seconds,
                ) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "application/octet-stream")
                    main_type = content_type.split(";")[0].strip()
                    mime = main_type or mimetypes.guess_type(url)[0] or "application/octet-stream"
                    return self._cache.store(url, response.content, mime, main_type)

        return _make_request()

    def bulk_download(self, urls: Sequence[str], refresh: bool = False) -> List[FilingArtifact]:
        return [self.download(url, refresh=refresh) for url in urls]
