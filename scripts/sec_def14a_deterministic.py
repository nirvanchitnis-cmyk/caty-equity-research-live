#!/usr/bin/env python3
"""
Deterministic DEF 14A fetcher: downloads latest DEF 14A filings per ticker
and produces a manifest + Excel index with provenance. Enforces SEC UA and
throttle policy. Emits an extraction log with 'User-Agent' and 'XLSX SHA256'
lines to support governance verification.

Outputs under def14a_deterministic/<timestamp>_<tickers>/:
  - DEF14A_<TICKER>_<accn>.html (one per ticker matched)
  - manifest_def14a.json (provenance + xlsx hash)
  - extraction.log (stdout mirror is fine when orchestrated)
  - DEF14A_Artifacts.xlsx (index of downloaded docs)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests


HERE = Path(__file__).resolve().parent


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def sec_headers(ua: str) -> Dict[str, str]:
    return {
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def sleep_throttle(throttle: float):
    time.sleep(max(0.0, float(throttle)))


def http_get(url: str, ua: str, throttle: float, tries: int = 4) -> requests.Response:
    last: Optional[requests.Response] = None
    for i in range(tries):
        r = requests.get(url, headers=sec_headers(ua), timeout=30)
        if r.status_code == 200:
            sleep_throttle(throttle)
            return r
        if r.status_code in (429, 403, 503):
            # Exponential backoff on fair-access related statuses
            time.sleep(max(throttle, 1.5) * (2 ** i))
            last = r
            continue
        last = r
        break
    if last is None:
        raise RuntimeError(f"GET failed (no response) for {url}")
    raise RuntimeError(f"GET {url} -> {last.status_code} {last.text[:200]}")


def load_ticker_map(ua: str, throttle: float) -> Dict[str, str]:
    url = "https://www.sec.gov/files/company_tickers.json"
    r = http_get(url, ua, throttle)
    data = r.json()
    out: Dict[str, str] = {}
    it = data.items() if isinstance(data, dict) else enumerate(data)
    for _, obj in it:
        t = (obj.get("ticker") or "").strip().upper()
        cik = obj.get("cik_str")
        if t and cik is not None:
            out[t] = str(cik)
    return out


def pad10(cik: str) -> str:
    return str(cik).zfill(10)


def accn_nodash(accn: str) -> str:
    return accn.replace("-", "") if accn else accn


@dataclass
class Def14ARecord:
    ticker: str
    cik: str
    accession_number: Optional[str]
    filing_date: Optional[str]
    primary_document: Optional[str]
    def14a_url: Optional[str]
    local_path: Optional[str]
    sha256: Optional[str]


def find_latest_def14a(cik10: str, ua: str, throttle: float) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (accessionNumber, filingDate, primaryDocument) for latest DEF 14A/DEFA14A."""
    url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
    r = http_get(url, ua, throttle)
    js = r.json()
    forms = (js.get("filings", {}).get("recent", {}).get("form", []) or [])
    accns = (js.get("filings", {}).get("recent", {}).get("accessionNumber", []) or [])
    dates = (js.get("filings", {}).get("recent", {}).get("filingDate", []) or [])
    prims = (js.get("filings", {}).get("recent", {}).get("primaryDocument", []) or [])

    latest_idx = None
    latest_date = ""
    for i, (f, d) in enumerate(zip(forms, dates)):
        f = (f or "").strip().upper()
        if f in {"DEF 14A", "DEFA14A"}:
            if (d or "") >= latest_date:
                latest_date = d or ""
                latest_idx = i
    if latest_idx is None:
        return None, None, None
    return accns[latest_idx], dates[latest_idx], prims[latest_idx]


def fetch_def14a_html(cik_str: str, accn: str, primary_doc: str, ua: str, throttle: float) -> Tuple[str, bytes]:
    cik_clean = str(int(cik_str))
    accn_clean = accn_nodash(accn)
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accn_clean}/"
    url = f"{base}{primary_doc}"
    r = http_get(url, ua, throttle)
    return url, r.content


def write_manifest(run_dir: Path, ua: str, throttle: float, xlsx_path: Path, records: List[Def14ARecord]):
    prov = {}
    for rec in records:
        prov[rec.ticker] = {
            "def14a_url": rec.def14a_url,
            "sha256": rec.sha256,
            "accession_number": rec.accession_number,
            "filing_date": rec.filing_date,
            "primary_document": rec.primary_document,
        }
    man = {
        "pipeline": "def14a",
        "user_agent": ua,
        "throttle_seconds": float(throttle),
        "generated_at_utc": utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_dir": str(run_dir.resolve()),
        "xlsx_path": str(xlsx_path.resolve()),
        "xlsx_sha256": sha256_bytes(xlsx_path.read_bytes()),
        "http_provenance": prov,
    }
    (run_dir / "manifest_def14a.json").write_text(json.dumps(man, indent=2))
    return man


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic DEF 14A fetcher for CATY Equity Research")
    ap.add_argument("--tickers", required=True, help="Space-separated tickers, e.g. 'CATY EWBC CVBF'")
    ap.add_argument("--user-agent", required=True, help="Organization/email@domain.com")
    ap.add_argument("--throttle", type=float, default=1.5)
    ap.add_argument("--outdir", default="evidence/raw/def14a/runs")
    args = ap.parse_args()

    ua = args.user_agent
    if "/" not in ua or "@" not in ua:
        print("ERROR: --user-agent must be Organization/email@domain.com", file=sys.stderr)
        return 2
    throttle = max(1.5, float(args.throttle))
    tickers = [t.strip().upper() for t in args.tickers.split() if t.strip()]
    if not tickers:
        print("ERROR: no tickers provided", file=sys.stderr)
        return 2

    # Run directory
    ts = utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.outdir) / f"{ts}_{'_'.join(tickers)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Start log banner
    log_path = run_dir / "extraction.log"
    with log_path.open("w", encoding="utf-8") as log:
        ts_now = utcnow().strftime("%Y%m%d_%H%M%S")
        log.write(f"Run: {ts_now}\n")
        log.write(f"User-Agent: {ua}\n")
        log.write(f"Throttle: {throttle:.1f}s (>=1.5s policy)\n")
        log.flush()

    # Map tickers -> CIK
    tmap = load_ticker_map(ua, throttle)

    records: List[Def14ARecord] = []
    for t in tickers:
        cik = tmap.get(t)
        if not cik:
            msg = f"WARNING: No CIK for {t}; skipping\n"
            sys.stderr.write(msg)
            with log_path.open("a", encoding="utf-8") as log:
                log.write(msg)
            continue
        cik10 = pad10(cik)
        accn, fdate, prim = find_latest_def14a(cik10, ua, throttle)
        if not accn or not prim:
            msg = f"WARNING: No DEF 14A found for {t}; skipping\n"
            sys.stderr.write(msg)
            with log_path.open("a", encoding="utf-8") as log:
                log.write(msg)
            continue
        url, blob = fetch_def14a_html(str(cik), accn, prim, ua, throttle)
        h = sha256_bytes(blob)
        local_name = f"DEF14A_{t}_{accn_nodash(accn)}.html"
        local_path = run_dir / local_name
        local_path.write_bytes(blob)
        rec = Def14ARecord(
            ticker=t,
            cik=str(int(cik)),
            accession_number=accn,
            filing_date=fdate,
            primary_document=prim,
            def14a_url=url,
            local_path=str(local_path),
            sha256=h,
        )
        records.append(rec)
        line = f"DEF14A: {t} date={fdate} accn={accn} primary={prim} url={url} SHA256={h}\n"
        print(line, end="")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(line)

    if not records:
        print("ERROR: no DEF 14A documents fetched", file=sys.stderr)
        return 3

    # Write index Excel
    df = pd.DataFrame([asdict(r) for r in records])
    xlsx_path = run_dir / "DEF14A_Artifacts.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name="def14a_docs", index=False)

    xhash = sha256_bytes(xlsx_path.read_bytes())
    print(f"XLSX SHA256: {xhash}")
    with (run_dir / "extraction.log").open("a", encoding="utf-8") as log:
        log.write(f"XLSX SHA256: {xhash}\n")

    # Manifest for governance
    write_manifest(run_dir, ua, throttle, xlsx_path, records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
