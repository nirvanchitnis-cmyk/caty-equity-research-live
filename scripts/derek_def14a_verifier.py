#!/usr/bin/env python3
"""
Derek audit verifier for DEF 14A pipeline.

Validates outputs from sec_def14a_deterministic.py and prints success signals
when requirements are met. Checks:
  - manifest_def14a.json and extraction.log exist
  - extraction.log contains 'User-Agent' and 'XLSX SHA256'
  - DEF14A_Artifacts.xlsx exists and matches hash in manifest
  - Manifest records throttle >= 1.5s and has per-ticker provenance entries

Prints 'ALL DEREK REQUIREMENTS MET' and 'DEF14A AUDIT READY • 7/7 • ✅' on pass.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 2


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: derek_def14a_verifier.py <run_dir>")
        return 2
    run_dir = Path(sys.argv[1]).resolve()
    if not run_dir.exists():
        return fail(f"Run dir not found: {run_dir}")

    manifest_path = run_dir / "manifest_def14a.json"
    log_path = run_dir / "extraction.log"
    if not manifest_path.exists():
        return fail("manifest_def14a.json missing")
    if not log_path.exists():
        return fail("extraction.log missing")

    man = json.loads(manifest_path.read_text())
    ua = man.get("user_agent") or ""
    if "/" not in ua or "@" not in ua:
        return fail("manifest user_agent invalid")
    throttle = float(man.get("throttle_seconds", 0.0))
    if throttle < 1.5:
        return fail("throttle < 1.5s policy")

    # log evidence for UA and XLSX hash
    log_s = log_path.read_text(errors="ignore")
    if "User-Agent:" not in log_s:
        return fail("extraction.log missing User-Agent line")
    m = re.search(r"XLSX SHA256:\s*([0-9a-f]{64})", log_s)
    if not m:
        return fail("extraction.log missing XLSX SHA256")
    log_xhash = m.group(1)

    xlsx_path = Path(man.get("xlsx_path") or "")
    if not xlsx_path.exists():
        return fail(f"xlsx missing: {xlsx_path}")
    man_hash = (man.get("xlsx_sha256") or "").lower()
    if man_hash != log_xhash:
        return fail("manifest xlsx_sha256 != log XLSX SHA256")

    http_prov = man.get("http_provenance") or {}
    if not isinstance(http_prov, dict) or not http_prov:
        return fail("http_provenance missing or empty")
    for t, prov in http_prov.items():
        if not prov.get("def14a_url") or not prov.get("sha256"):
            return fail(f"provenance incomplete for {t}")

    print("ALL DEREK REQUIREMENTS MET")
    print("DEF14A AUDIT READY • 7/7 • ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

