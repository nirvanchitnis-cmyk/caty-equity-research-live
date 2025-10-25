"""HTTP fetcher with caching, throttling, and retries."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

import httpx

from .. import cache
from ..config import ToolConfig
from .models import ArtifactMetadata, FetchResult

_DOMAIN_STATE: Dict[str, Dict[str, object]] = {}
_DOMAIN_STATE_LOCK = asyncio.Lock()


async def _get_domain_state(domain: str, rate_limit: float) -> Dict[str, object]:
    async with _DOMAIN_STATE_LOCK:
        if domain not in _DOMAIN_STATE:
            _DOMAIN_STATE[domain] = {
                "lock": asyncio.Lock(),
                "last_request_ts": 0.0,
                "interval": 1.0 / rate_limit if rate_limit > 0 else 0.0,
            }
        return _DOMAIN_STATE[domain]


async def _throttle(domain: str, rate_limit: float) -> None:
    state = await _get_domain_state(domain, rate_limit)
    lock: asyncio.Lock = state["lock"]  # type: ignore[assignment]
    interval = state["interval"]  # type: ignore[assignment]
    async with lock:
        now = time.monotonic()
        last_ts = state["last_request_ts"]  # type: ignore[assignment]
        wait_time = max(0.0, interval - (now - last_ts))
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        state["last_request_ts"] = time.monotonic()


async def fetch_artifact(
    url: str,
    config: ToolConfig = ToolConfig(),
    force_refresh: bool = False,
) -> FetchResult:
    """Fetch an artifact with caching, retries, and throttling."""
    cached_entry = None if force_refresh else cache.get_cached_entry(url, config)
    if cached_entry:
        file_path = cached_entry["file_path"]
        metadata = ArtifactMetadata(
            url=cached_entry["url"],
            content_type=cached_entry.get("content_type") or "application/octet-stream",
            sha256=cached_entry["sha256"],
            size_bytes=Path(file_path).stat().st_size,
            fetched_at=cached_entry.get("fetched_at") or "",
        )
        return FetchResult(success=True, artifact=metadata, file_path=file_path)

    parsed = urlparse(url)
    domain = parsed.netloc
    headers = {
        "User-Agent": config.user_agent,
        "Accept": "*/*",
    }

    attempt = 0
    last_error: str | None = None

    async with httpx.AsyncClient(headers=headers, timeout=config.timeout_seconds, follow_redirects=True) as client:
        while attempt < config.max_retries:
            attempt += 1
            try:
                await _throttle(domain, config.rate_limit_per_sec)
                response = await client.get(url)
            except httpx.HTTPError as exc:
                last_error = str(exc)
                await asyncio.sleep(min(2 ** attempt, 10))
                continue

            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                await asyncio.sleep(min(2 ** attempt, 10))
                continue

            content = response.content
            content_type = response.headers.get("Content-Type", "application/octet-stream").split(";")[0].strip()

            file_path, digest = cache.store_artifact(url, content, content_type, config)
            fetched_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            metadata = ArtifactMetadata(
                url=url,
                content_type=content_type,
                sha256=digest,
                size_bytes=len(content),
                fetched_at=fetched_at,
            )
            return FetchResult(success=True, artifact=metadata, file_path=file_path)

    return FetchResult(success=False, artifact=None, file_path=None, error=last_error or "Unknown error")


def fetch_artifact_sync(
    url: str,
    config: ToolConfig = ToolConfig(),
    force_refresh: bool = False,
) -> FetchResult:
    """Synchronous helper that executes the async fetcher."""

    async def _runner() -> FetchResult:
        return await fetch_artifact(url=url, config=config, force_refresh=force_refresh)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_runner(), loop)
        return future.result()
    return asyncio.run(_runner())


__all__ = ["fetch_artifact", "fetch_artifact_sync"]
