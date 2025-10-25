"""Fact registry loader and validation."""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import yaml

from .logging_utils import log_event

REGISTRY_PATH = Path(__file__).parent / "data" / "facts.registry.yaml"


class RegistryError(RuntimeError):
    """Raised when registry cannot be loaded."""


def _validate_fact_entry(entry: Mapping[str, Any]) -> None:
    required = {"id", "label"}
    missing = required - entry.keys()
    if missing:
        raise RegistryError(f"Missing required keys {missing} in fact registry entry")


@functools.lru_cache(maxsize=1)
def load_registry(path: Path = REGISTRY_PATH) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        raise RegistryError(f"Fact registry file missing: {path}")
    data = yaml.safe_load(path.read_text())
    if "facts" not in data:
        raise RegistryError("Registry missing `facts` root key")
    facts = {}
    for entry in data["facts"]:
        _validate_fact_entry(entry)
        facts[entry["id"]] = entry
    log_event("Loaded fact registry", count=len(facts))
    return facts


def dump_registry(path: Path = REGISTRY_PATH) -> str:
    return json.dumps(load_registry(path), indent=2)
