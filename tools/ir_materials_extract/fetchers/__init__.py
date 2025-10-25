"""Fetchers for IR materials."""

from .http_fetcher import fetch_artifact, fetch_artifact_sync
from .models import ArtifactMetadata, FetchResult

__all__ = ["fetch_artifact", "fetch_artifact_sync", "ArtifactMetadata", "FetchResult"]
