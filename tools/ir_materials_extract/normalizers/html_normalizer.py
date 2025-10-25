"""Utilities to convert HTML artifacts into normalized text payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from bs4 import BeautifulSoup


def normalize_html(html_path: Path) -> Dict[str, object]:
    """Normalize an HTML artifact into structured text and metadata."""
    html_content = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "lxml")

    text_chunks = []
    dom_index: Dict[str, Dict[str, int]] = {}
    running_offset = 0

    for idx, element in enumerate(soup.find_all(True)):
        snippet = element.get_text(" ", strip=True)
        if not snippet:
            continue
        key = f"{element.name}[{idx}]"
        dom_index[key] = {"offset": running_offset, "length": len(snippet)}
        text_chunks.append(snippet)
        running_offset += len(snippet) + 1

    normalized_text = "\n".join(text_chunks)

    links = []
    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        if href:
            links.append(href)

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    return {
        "text": normalized_text,
        "dom_index": dom_index,
        "links": links,
        "title": title,
    }


__all__ = ["normalize_html"]
