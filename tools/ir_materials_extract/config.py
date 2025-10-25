"""Configuration helpers for the IR materials extraction toolkit."""

from dataclasses import dataclass
from pathlib import Path

DEFAULT_USER_AGENT = "CATY-Research/ir_extract (contact: research@caty-analysis.com)"
DEFAULT_RATE_LIMIT_PER_DOMAIN = 2.0  # requests per second
DEFAULT_CACHE_DIR = Path(".cache/ir_artifacts")
DEFAULT_CACHE_DB = DEFAULT_CACHE_DIR / "cache_index.sqlite3"


@dataclass(frozen=True)
class ToolConfig:
    """Runtime configuration for fetchers and normalizers."""

    user_agent: str = DEFAULT_USER_AGENT
    rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_DOMAIN
    cache_dir: Path = DEFAULT_CACHE_DIR
    cache_db: Path = DEFAULT_CACHE_DB
    timeout_seconds: int = 30
    max_retries: int = 3


__all__ = [
    "ToolConfig",
    "DEFAULT_USER_AGENT",
    "DEFAULT_RATE_LIMIT_PER_DOMAIN",
    "DEFAULT_CACHE_DIR",
    "DEFAULT_CACHE_DB",
]
