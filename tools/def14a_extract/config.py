"""Global configuration for the DEF 14A extraction toolkit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_USER_AGENT = (
    "caty-equity-research-live/def14a_extract (contact: research-ops@catyfinance.com)"
)
DEFAULT_REQUESTS_PER_SECOND = 2.0
MAX_BURST_REQUESTS_PER_SECOND = 10.0
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_CACHE_DIR = Path(".cache/def14a_artifacts")
DEFAULT_CACHE_DB = DEFAULT_CACHE_DIR / "cache_index.sqlite3"


@dataclass(frozen=True)
class ToolConfig:
    """Runtime configuration for fetchers and pipelines."""

    user_agent: str = DEFAULT_USER_AGENT
    requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND
    max_burst_per_second: float = MAX_BURST_REQUESTS_PER_SECOND
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    cache_dir: Path = DEFAULT_CACHE_DIR
    cache_db: Path = DEFAULT_CACHE_DB


def ensure_cache_dirs(config: ToolConfig) -> None:
    """Ensure cache directories exist."""

    config.cache_dir.mkdir(parents=True, exist_ok=True)
