"""Public exports for the IR materials extraction toolkit."""

from __future__ import annotations

from .config import ToolConfig
from .pipeline import extract_facts_from_url

try:  # pragma: no cover - optional CLI dependency guard
    from .cli import app as cli_app
except RuntimeError:  # pragma: no cover
    cli_app = None  # type: ignore
except ImportError:  # pragma: no cover
    cli_app = None  # type: ignore

__all__ = ["ToolConfig", "extract_facts_from_url", "cli_app"]
