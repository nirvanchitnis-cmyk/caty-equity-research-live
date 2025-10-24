#!/usr/bin/env python3
"""
Evidence Hash Manifest Generator

Computes SHA256 hashes for files under evidence/ and writes evidence/manifest_sha256.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence"
OUT = EVID / "manifest_sha256.json"


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not EVID.exists():
        print("evidence/ directory not found")
        return 0

    manifest: Dict[str, str] = {}
    exts = {".html", ".htm", ".pdf", ".json", ".csv", ".zip", ".gz", ".txt", ".md", ".xlsx"}
    for path in EVID.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            key = str(path.relative_to(ROOT))
            manifest[key] = sha256_file(path)

    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Hashed {len(manifest)} evidence files → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

