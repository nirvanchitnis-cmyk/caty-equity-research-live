"""HTML normalization utilities."""

from __future__ import annotations

from typing import Dict, Tuple

from bs4 import BeautifulSoup
from lxml import html

from ..models import DocumentProfile


def normalize_html(profile: DocumentProfile) -> Dict[str, object]:
    doc = html.fromstring(profile.artifact.path.read_bytes())
    doc.make_links_absolute(profile.artifact.url)
    text_content = doc.text_content()
    selector_map: Dict[str, Tuple[int, int]] = {}

    soup = BeautifulSoup(profile.artifact.path.read_text(errors="ignore"), "lxml")
    for idx, tag in enumerate(soup.find_all(True)):
        text = tag.get_text(strip=True)
        if not text:
            continue
        selector = tag.name
        selector_map[f"{selector}-{idx}"] = (len(text_content), len(text))

    return {
        "text": text_content,
        "dom": doc,
        "selector_map": selector_map,
    }
