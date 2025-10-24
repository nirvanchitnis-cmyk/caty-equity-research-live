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
    # Check hub and module pages; skip large raw SEC HTMLs
    patterns = [
        ROOT / "index.html",
        *ROOT.glob("CATY_*.html"),
        *ROOT.glob("evidence/*.html"),
        *ROOT.glob("evidence/workpapers/*.html"),
    ]
    for p in patterns:
        if p.is_file():
            yield p


HREF_RE = re.compile(r'href=\"([^\"]+)\"')


def is_internal_link(href: str) -> bool:
    href = href.strip()
    if not href:
        return False
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return False
    return True


def scan_file(path: Path) -> Iterator[Tuple[str, Path]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in HREF_RE.finditer(text):
        href = m.group(1)
        if not is_internal_link(href):
            continue
        # Strip fragments (e.g., file.html#anchor or file.pdf#page=6)
        clean_href = href.split('#', 1)[0]
        target = (path.parent / clean_href).resolve()
        try:
            target.relative_to(ROOT)
        except Exception:
            # Link escapes repo root – treat as broken
            yield (href, target)
            continue
        if not target.exists():
            yield (href, target)


def main() -> int:
    broken: list[tuple[Path, str, Path]] = []
    for html in iter_html_files():
        for href, target in scan_file(html):
            broken.append((html, href, target))

    if broken:
        print("Broken internal links detected (failing):\n")
        for src, href, tgt in broken:
            print(f" - Source: {src.relative_to(ROOT)} -> href='{href}' | target='{tgt.relative_to(ROOT)}' (missing)")
        return 1

    print("All internal links verified (PASS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
