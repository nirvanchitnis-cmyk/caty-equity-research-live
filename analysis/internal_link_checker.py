#!/usr/bin/env python3
"""
Internal Link Checker

Scans HTML files in the repo for internal links and verifies the targets exist.
Exits non-zero if broken links are found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator, Tuple

ROOT = Path(__file__).resolve().parents[1]


def iter_html_files() -> Iterator[Path]:
    """Yield HTML files to check.

    Scope intentionally focuses on public pages and index hubs:
    - Root dashboard index + CATY_*.html modules
    - Evidence hub pages under evidence/ and nested index.html files
    Avoids scanning large raw SEC HTML dumps by restricting to index.html
    in nested evidence folders.
    """
    # Root and module pages
    yield from (p for p in [ROOT / "index.html"] if p.is_file())
    for p in ROOT.glob("CATY_*.html"):
        if p.is_file():
            yield p
    # Evidence hubs and nested indexes
    for p in ROOT.glob("evidence/*.html"):
        if p.is_file():
            yield p
    for p in ROOT.glob("evidence/**/index.html"):
        if p.is_file():
            yield p


# Capture href/src attributes with single or double quotes.
# Example matches: href="...", href='...', src="...", src='...'
ATTR_RE = re.compile(r'(?:href|src)\s*=\s*([\"\'])([^\"\']+)\1', re.IGNORECASE)


def is_internal_link(href: str) -> bool:
    href = href.strip()
    if not href:
        return False
    if href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
        return False
    return True


def scan_file(path: Path) -> Iterator[Tuple[str, Path]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in ATTR_RE.finditer(text):
        href = m.group(2)
        if not is_internal_link(href):
            continue
        # Strip fragment and query (e.g., file.html#anchor or file.pdf?x=1)
        clean = href.split('#', 1)[0].split('?', 1)[0]
        if not clean:
            continue
        target = (path.parent / clean).resolve()
        try:
            target.relative_to(ROOT)
        except Exception:
            # Link escapes repo root – treat as broken
            yield (href, target)
            continue
        if not target.exists():
            yield (href, target)


MD_LINK_RE = re.compile(r"!??\[[^\]]*\]\(([^)]+)\)")


def iter_markdown_files() -> Iterator[Path]:
    # Docs and analysis markdown are part of the public navigation and evidence
    for pattern in ("docs/**/*.md", "analysis/**/*.md", "evidence/**/*.md"):
        for p in ROOT.glob(pattern):
            if p.is_file():
                yield p


def scan_markdown(path: Path) -> Iterator[Tuple[str, Path]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in MD_LINK_RE.finditer(text):
        link = m.group(1).strip()
        if not is_internal_link(link):
            continue
        clean = link.split('#', 1)[0].split('?', 1)[0]
        if not clean:
            continue
        target = (path.parent / clean).resolve()
        try:
            target.relative_to(ROOT)
        except Exception:
            yield (link, target)
            continue
        if not target.exists():
            yield (link, target)


def main() -> int:
    broken: list[tuple[Path, str, Path]] = []
    # HTML
    for html in iter_html_files():
        for href, target in scan_file(html):
            broken.append((html, href, target))
    # Markdown
    for md in iter_markdown_files():
        for href, target in scan_markdown(md):
            broken.append((md, href, target))

    if broken:
        print("Broken internal links detected (failing):\n")
        for src, href, tgt in broken:
            try:
                rel_src = src.relative_to(ROOT)
            except Exception:
                rel_src = src
            try:
                rel_tgt = tgt.relative_to(ROOT)
            except Exception:
                rel_tgt = tgt
            print(f" - Source: {rel_src} -> ref='{href}' | target='{rel_tgt}' (missing)")
        return 1

    print("All internal links verified across HTML + Markdown (PASS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
