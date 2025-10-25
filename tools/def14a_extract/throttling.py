"""Rate limiting and retry policies."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import ToolConfig
from .logging_utils import log_event


class RateLimiter:
    """Simple token bucket limiter."""

    def __init__(self, config: ToolConfig) -> None:
        self._config = config
        self._capacity = max(1.0, config.max_burst_per_second)
        self._tokens = self._capacity
        self._last = time.monotonic()

    def acquire(self) -> None:
        while True:
            now = time.monotonic()
            elapsed = now - self._last
            refill = elapsed * self._config.requests_per_second
            self._tokens = min(self._capacity, self._tokens + refill)
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            time.sleep(0.1)

    async def acquire_async(self) -> None:
        while True:
            now = time.monotonic()
            elapsed = now - self._last
            refill = elapsed * self._config.requests_per_second
            self._tokens = min(self._capacity, self._tokens + refill)
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            await asyncio.sleep(0.1)

    @contextmanager
    def limit(self) -> Iterator[None]:
        self.acquire()
        yield

    @asynccontextmanager
    async def limit_async(self) -> AsyncIterator[None]:
        await self.acquire_async()
        yield


def build_retry_decorator(attempts: int) -> retry:
    return retry(
        retry=retry_if_exception_type((TimeoutError, ConnectionError, ValueError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(attempts),
        reraise=True,
        before_sleep=lambda retry_state: log_event(
            "Retrying request",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
            if retry_state.outcome
            else None,
        ),
    )
