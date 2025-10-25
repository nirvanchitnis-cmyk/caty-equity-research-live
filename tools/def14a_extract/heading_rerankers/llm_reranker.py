"""Optional LLM-based heading reranker.

This module keeps the interface minimal so the pipeline can run without LLM
support when the dependency is absent. If no LLM client is configured, the
reranker simply returns the original candidates.
"""

from __future__ import annotations

from typing import List, Sequence

from .deterministic import HeadingCandidate


def rerank_candidates(
    section_id: str,
    candidates: Sequence[HeadingCandidate],
) -> List[HeadingCandidate]:
    # Placeholder for optional integration; maintain deterministic behavior by default.
    return list(candidates)
