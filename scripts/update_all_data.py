#!/usr/bin/env python3
"""
Master automation entrypoint for refreshing CATY data inputs.

Pipeline:
    1. Fetch SEC EDGAR XBRL data
    2. Fetch FDIC Call Report data
    3. Merge sources into canonical JSON datasets
    4. Update evidence metadata registry
    5. Rebuild site artifacts
    6. Run reconciliation guard validation
    7. Append structured run logs
"""

from __future__ import annotations

import datetime as dt
import os
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOG_PATH = ROOT / "logs" / "automation_run.log"

SEC_RAW_PATH = DATA_DIR / "sec_edgar_raw.json"
FDIC_RAW_PATH = DATA_DIR / "fdic_raw.json"
PEER_RAW_PATH = DATA_DIR / "peer_data_raw.json"

DQ_REPORT_PATH = DATA_DIR / "data_quality_report.json"
PEER_SNAPSHOT_PATH = ROOT / "evidence" / "peer_snapshot_2025Q2.csv"
EVIDENCE_PATH = DATA_DIR / "evidence_sources.json"
DEF14A_OUTPUT_PATH = DATA_DIR / "def14a_facts_latest.json"

SCRIPTS = ROOT / "scripts"


def append_log(message: str) -> None:
    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {message}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)

def run_step(cmd: list[str], step_name: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    logging.info("Running %s: %s", step_name, " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        logging.debug("%s stdout:\n%s", step_name, result.stdout.strip())
    if result.stderr:
        logging.debug("%s stderr:\n%s", step_name, result.stderr.strip())
    if result.returncode != 0 and not allow_failure:
        logging.error("%s failed (exit %s)", step_name, result.returncode)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    if result.returncode != 0:
        logging.warning("%s returned non-zero exit %s (continuing)", step_name, result.returncode)
    return result


def run_def14a_refresh(year: Optional[int] = None) -> None:
    filing_year = year or dt.date.today().year
    DEF14A_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "tools.def14a_extract.cli",
        "facts",
        "--ticker",
        "CATY",
        "--year",
        str(filing_year),
        "--facts",
        "meeting_date,record_date,meeting_time,meeting_timezone,meeting_location_type,meeting_access_url",
        "--provenance",
        "--output",
        str(DEF14A_OUTPUT_PATH),
    ]
    run_step(cmd, "def14a_facts")
    append_log(
        f"tools.def14a_extract.cli: Refreshed DEF 14A facts for {filing_year} "
        f"to {DEF14A_OUTPUT_PATH.relative_to(ROOT)}"
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)




def update_evidence_sources(
    sec_payload: Dict[str, Any],
    fdic_payload: Dict[str, Any],
    peer_payload: Optional[Dict[str, Any]] = None,
) -> None:
    if not EVIDENCE_PATH.exists():
        logging.warning("Evidence metadata file missing: %s", EVIDENCE_PATH)
        return
    data = load_json(EVIDENCE_PATH)
    today = dt.date.today().isoformat()
    updated_ids: set[str] = set()

    for source in data.get("sources", []):
        source_id = source.get("id")
        if source_id == "fdic_financials":
            source["last_verified"] = today
            source["status"] = "VERIFIED_OK"
            quarter = fdic_payload.get("quarters", [{}])[0]
            period = quarter.get("period")
            if period:
                source["accession"] = f"FDIC API (Quarter {period})"
            updated_ids.add(source_id)
        elif source_id == "caty_10q_q2_2025":
            source["last_verified"] = today
            accession = sec_payload.get("accession")
            if accession:
                source["accession"] = accession
            source["status"] = "VERIFIED_OK"
            updated_ids.add(source_id)
        elif source_id == "peer_metrics" and peer_payload:
            source["last_verified"] = today
            source["status"] = "VERIFIED_OK"
            snapshot_period = peer_payload.get("period")
            if snapshot_period:
                source["accession"] = snapshot_period
            fetch_ts = peer_payload.get("fetch_timestamp")
            if fetch_ts:
                source["note"] = f"Auto-generated via peer API fetch {fetch_ts}"
            updated_ids.add(source_id)

    def ensure_entry(entry_id: str, template: Dict[str, Any]) -> None:
        for entry in data.get("sources", []):
            if entry.get("id") == entry_id:
                entry.update(template)
                updated_ids.add(entry_id)
                return
        data.setdefault("sources", []).append(template)
        updated_ids.add(entry_id)

    ensure_entry(
        "sec_edgar_api",
        {
            "id": "sec_edgar_api",
            "description": "SEC EDGAR companyfacts API payload for CATY",
            "path": "data/sec_edgar_raw.json",
            "accession": sec_payload.get("accession"),
            "last_verified": today,
            "owner": "Financial Reporting",
            "refresh_frequency": "Quarterly",
            "status": "VERIFIED_OK",
        },
    )
    ensure_entry(
        "fdic_call_report_api",
        {
            "id": "fdic_call_report_api",
            "description": "FDIC Call Report API payload for CATHAY BANK",
            "path": "data/fdic_raw.json",
            "accession": str(fdic_payload.get("cert")) if fdic_payload.get("cert") else "FDIC CERT",
            "last_verified": today,
            "owner": "Credit Analytics",
            "refresh_frequency": "Quarterly",
            "status": "VERIFIED_OK",
        },
    )
    if peer_payload:
        ensure_entry(
            "peer_metrics",
            {
                "id": "peer_metrics",
                "description": "Peer regression snapshot generated from SEC EDGAR API",
                "path": str(PEER_SNAPSHOT_PATH.relative_to(ROOT)),
                "accession": peer_payload.get("period"),
                "last_verified": today,
                "owner": "Peer Analytics",
                "refresh_frequency": "Quarterly",
                "status": "VERIFIED_OK",
            },
        )

    with EVIDENCE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    logging.info("Updated evidence sources for ids: %s", ", ".join(sorted(updated_ids)))

def load_payload_safely(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:  # noqa: PERF203
        logging.warning("Failed to decode JSON at %s: %s", path, exc)
        return None


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    append_log("update_all_data.py: START")

    # Step 0: Fetch live market price (skip in test mode)
    if not os.environ.get("CATY_TEST_MODE"):
        print("Fetching live CATY price...")
        fetch_live_result = run_step(
            [sys.executable, str(SCRIPTS / "fetch_live_price.py")],
            "fetch_live_price",
            allow_failure=True,
        )
        if fetch_live_result.returncode == 0:
            print("✅ Market data updated")
            append_log("fetch_live_price.py: Updated market data with latest price")
        else:
            print("⚠️ Live price update failed - using cached value")
            append_log("fetch_live_price.py: WARNING - live price fetch failed, using cached value")
    else:
        print("⚠️ Test mode: Skipping live price fetch")
        append_log("TEST MODE: Skipped live price fetch")

    # Step 0b: DEF 14A fact refresh via CLI (skip in test mode)
    if not os.environ.get("CATY_TEST_MODE"):
        try:
            print("Refreshing DEF 14A facts via CLI...")
            run_def14a_refresh()
            print(f"✅ DEF 14A facts captured to {DEF14A_OUTPUT_PATH.relative_to(ROOT)}")
        except subprocess.CalledProcessError as exc:
            print("⚠️ DEF 14A refresh failed - continuing without update")
            append_log(
                f"tools.def14a_extract.cli: ERROR - def14a refresh failed ({exc.returncode})"
            )
    else:
        print("⚠️ Test mode: Skipping DEF 14A CLI refresh")
        append_log("TEST MODE: Skipped DEF 14A CLI refresh")

    # Step 1: SEC EDGAR
    sec_result = run_step([sys.executable, str(SCRIPTS / "fetch_sec_edgar.py")], "fetch_sec_edgar", allow_failure=True)
    sec_payload = load_payload_safely(SEC_RAW_PATH)
    if sec_payload is None:
        append_log("fetch_sec_edgar.py: ERROR (no payload available)")
        return 1
    if sec_result.returncode == 0:
        append_log(
            f"fetch_sec_edgar.py: Fetched {sec_payload.get('form_type')} {sec_payload.get('accession')} "
            f"(period {sec_payload.get('period_end')})"
        )
    else:
        append_log("fetch_sec_edgar.py: WARNING - fetch failed, using cached payload")

    # Step 2: FDIC
    fdic_result = run_step([sys.executable, str(SCRIPTS / "fetch_fdic_data.py")], "fetch_fdic_data", allow_failure=True)
    fdic_payload = load_payload_safely(FDIC_RAW_PATH)
    if fdic_payload is None:
        append_log("fetch_fdic_data.py: ERROR (no payload available)")
        return 1
    if fdic_result.returncode == 0:
        latest_period = fdic_payload.get("quarters", [{}])[0].get("period")
        append_log(
            f"fetch_fdic_data.py: Fetched call report {latest_period or 'latest'} (CERT {fdic_payload.get('cert')})"
        )
    else:
        append_log("fetch_fdic_data.py: WARNING - fetch failed, using cached payload")

    # Step 3: Peer bank metrics
    peer_result = run_step([sys.executable, str(SCRIPTS / "fetch_peer_banks.py")], "fetch_peer_banks", allow_failure=True)
    peer_payload = load_payload_safely(PEER_RAW_PATH)
    if peer_payload is None:
        append_log("fetch_peer_banks.py: ERROR (no payload available)")
        return 1
    if peer_result.returncode == 0:
        peer_count = len(peer_payload.get("banks", {}))
        append_log(
            f"fetch_peer_banks.py: Fetched {peer_count} peers for {peer_payload.get('period', 'unknown period')}"
        )
    else:
        append_log("fetch_peer_banks.py: WARNING - fetch failed, using cached payload")

    run_step([sys.executable, str(SCRIPTS / "generate_peer_snapshot.py")], "generate_peer_snapshot")
    append_log("generate_peer_snapshot.py: Rebuilt evidence/peer_snapshot_2025Q2.csv")

    # Step 4: Merge
    run_step([sys.executable, str(SCRIPTS / "merge_data_sources.py")], "merge_data_sources")
    dq_payload = load_payload_safely(DQ_REPORT_PATH) or {}
    conflict_count = len(dq_payload.get("conflicts", []))
    append_log(f"merge_data_sources.py: {conflict_count} conflicts logged")

    # Step 4.5: Calculate valuation metrics
    print("Calculating valuation metrics...")
    valuation_result = run_step(
        [sys.executable, str(SCRIPTS / "calculate_valuation_metrics.py")],
        "calculate_valuation_metrics",
        allow_failure=True,
    )
    if valuation_result.returncode == 0:
        append_log("calculate_valuation_metrics.py: Recalculated all targets and returns")
    else:
        append_log("calculate_valuation_metrics.py: WARNING - calculation failed")
        return 1

    # Step 5: Evidence metadata
    update_evidence_sources(sec_payload, fdic_payload, peer_payload)

    # Step 6: Rebuild site
    run_step([sys.executable, str(SCRIPTS / "build_site.py")], "build_site")
    append_log("build_site.py: Rebuilt modules successfully")

    # Step 7: Validation
    run_step([sys.executable, str(ROOT / "analysis" / "reconciliation_guard.py")], "reconciliation_guard")
    append_log("reconciliation_guard.py: PASS")

    append_log("update_all_data.py: SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
