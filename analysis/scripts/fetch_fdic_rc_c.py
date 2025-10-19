"""Utility script to pull FDIC Schedule RC-C balances for Cathay Bank (CERT 18503).

Outputs:
  - JSON payload saved under evidence/raw/fdic_CATY_20250630_financials.json

This mirrors the extraction described in evidence/fdic_call_report_reconciliation.md
and should be rerun whenever new quarters are evaluated.
"""

from pathlib import Path
import json
import requests


FDIC_API = "https://api.fdic.gov/banks/financials"
PARAMS = {
    "filters": "CERT:18503 AND REPDTE:20250630",
    "fields": "LNLS,LNLSGR,LNLSNET,LNRECNOT,LNRECNFM,LNREMULT,LNRENROT,LNRENROW,LNRELOC,LNREAG,REPDTE",
    "format": "json",
}


def main() -> None:
    response = requests.get(FDIC_API, params=PARAMS, timeout=30)
    response.raise_for_status()
    data = response.json()

    output_path = Path(__file__).resolve().parents[2] / "evidence" / "raw" / "fdic_CATY_20250630_financials.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))
    print(f"FDIC payload written to {output_path}")


if __name__ == "__main__":
    main()
