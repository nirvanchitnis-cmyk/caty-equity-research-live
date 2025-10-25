"""IR artifact discovery utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import httpx
import yaml
from bs4 import BeautifulSoup

from ..config import ToolConfig

_PROFILE_CACHE: Dict[str, Dict[str, str]] = {}


def _load_profiles() -> Dict[str, Dict[str, str]]:
    global _PROFILE_CACHE
    if _PROFILE_CACHE:
        return _PROFILE_CACHE
    profile_path = Path(__file__).parent / "site_profiles.yaml"
    with profile_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    profiles: Dict[str, Dict[str, str]] = {}
    for entry in data.get("profiles", []):
        ticker = entry.get("ticker")
        if ticker:
            profiles[ticker.upper()] = entry
    _PROFILE_CACHE = profiles
    return profiles


def _artifact_paths_for_type(profile: Dict[str, str], artifact_type: str) -> List[str]:
    mapping = {
        "press_release": "press_releases_path",
        "presentation": "presentations_path",
        "financials": "financials_path",
        "supplemental": "financials_path",
    }
    key = mapping.get(artifact_type)
    if not key:
        return []
    value = profile.get(key)
    if not value:
        return []
    return [value]


def _period_matches(period: str, text: str) -> bool:
    if not period:
        return True
    period_lower = period.lower()
    if period_lower in text.lower():
        return True
    year_match = re.search(r"(19|20)\d{2}", period)
    if year_match and year_match.group(0) in text:
        return True
    return False


def _is_candidate_url(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return False
    path = parsed.path.lower()
    if not path or path == "/":
        return False
    if any(path.endswith(ext) for ext in (".pdf", ".html", ".htm", ".txt")):
        return True
    segments = [segment for segment in path.split("/") if segment]
    if any(keyword in path for keyword in ("press", "earnings", "presentation", "news")):
        if len(segments) > 2:
            return True
    return False


def discover_ir_artifacts(
    ticker: str,
    period: Optional[str] = None,
    artifact_types: Optional[List[str]] = None,
    config: ToolConfig = ToolConfig(),
) -> List[str]:
    """Discover candidate IR artifact URLs for a given ticker."""
    ticker_key = ticker.upper()
    profile = _load_profiles().get(ticker_key)
    if not profile:
        raise ValueError(f"No IR profile found for ticker '{ticker_key}'")

    artifact_types = artifact_types or ["press_release", "presentation"]

    headers = {"User-Agent": config.user_agent}
    timeout = config.timeout_seconds

    discovered: List[str] = []
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        for artifact_type in artifact_types:
            paths = _artifact_paths_for_type(profile, artifact_type)
            for relative_path in paths:
                base_url = profile["ir_base"].rstrip("/")
                index_url = urljoin(base_url + "/", relative_path.lstrip("/"))
                try:
                    response = client.get(index_url)
                except httpx.HTTPError:
                    continue
                if response.status_code >= 500:
                    continue

                soup = BeautifulSoup(response.text, "lxml")
                for link in soup.select("a[href]"):
                    href = link.get("href")
                    if not href:
                        continue
                    full_url = urljoin(index_url, href.strip())
                    full_url = full_url.split("#", 1)[0]
                    anchor_text = link.get_text(" ", strip=True)
                    combined_text = " ".join(filter(None, [anchor_text, full_url]))
                    if period and not _period_matches(period, combined_text):
                        continue
                    if _is_candidate_url(full_url):
                        discovered.append(full_url)

        if len(discovered) < 5:
            discovered.extend(_discover_from_aux_feeds(client, profile, period))

    seen: Set[str] = set()
    unique_urls: List[str] = []
    for url in discovered:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    if len(unique_urls) < 5:
        unique_urls.extend(_discover_from_sec_feed(ticker_key, config))

    final_seen: Set[str] = set()
    deduped: List[str] = []
    for url in unique_urls:
        if url not in final_seen:
            final_seen.add(url)
            deduped.append(url)

    filtered = [url for url in deduped if _is_material_link(url)]
    return filtered if filtered else deduped


def _discover_from_aux_feeds(
    client: httpx.Client,
    profile: Dict[str, str],
    period: Optional[str],
) -> List[str]:
    """Fallback discovery using site-level sitemaps or RSS feeds."""
    base_url = profile["ir_base"]
    sitemap_candidates = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
        urljoin(base_url, "/rss.xml"),
        urljoin(base_url, "/feed"),
    ]
    collected: List[str] = []

    for sitemap_url in sitemap_candidates:
        try:
            resp = client.get(sitemap_url)
        except httpx.HTTPError:
            continue
        if resp.status_code >= 500 or not resp.text.strip():
            continue
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            continue

        if root.tag.lower().endswith("rss"):
            link_elements = root.findall(".//{*}item/{*}link")
        else:
            link_elements = root.findall(".//{*}loc")

        for element in link_elements:
            url_text = (element.text or "").strip()
            url_text = url_text.split("#", 1)[0]
            if not url_text:
                continue
            if not _is_candidate_url(url_text):
                continue
            if period and not _period_matches(period, url_text):
                continue
            collected.append(url_text)
            if len(collected) >= 20:
                break
        if collected:
            break
    return collected


def _discover_from_sec_feed(ticker: str, config: ToolConfig) -> List[str]:
    """Leverage the SEC Atom feed as a last-resort discovery fallback."""
    feed_url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={ticker}&type=8-K&count=40&output=atom"
    )
    headers = {
        "User-Agent": config.user_agent,
        "Accept": "application/atom+xml",
    }
    try:
        resp = httpx.get(feed_url, headers=headers, timeout=config.timeout_seconds)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return []

    collected: List[str] = []
    for entry in root.findall(".//{*}entry"):
        link_el = entry.find(".//{*}link")
        href = link_el.get("href") if link_el is not None else None
        if not href:
            href = entry.findtext(".//{*}id")
        if not href:
            continue
        collected.append(href)
        if len(collected) >= 20:
            break
    return collected


def _is_material_link(url: str) -> bool:
    """Heuristic to filter navigation anchors and hub pages."""
    parsed = urlparse(url)
    if parsed.fragment:
        return False
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in (".pdf", ".html", ".htm", ".txt")):
        return True
    segments = [segment for segment in path.split("/") if segment]
    return len(segments) > 2


__all__ = ["discover_ir_artifacts"]
