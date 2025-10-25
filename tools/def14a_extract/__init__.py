"""High-level entrypoints for DEF 14A extraction tool suite."""

from .api import get_def14a_facts  # noqa: F401

try:  # pragma: no cover - CLI optional
    from .cli import app as cli_app  # noqa: F401
except RuntimeError:  # pragma: no cover - CLI optional
    cli_app = None  # type: ignore

__all__ = ["cli_app", "get_def14a_facts"]
