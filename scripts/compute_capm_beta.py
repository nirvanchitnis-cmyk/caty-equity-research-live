#!/usr/bin/env python3
"""
Compute CAPM beta and CAPM-implied COE using 2 years of weekly returns for
CATY vs. KBW Regional Bank ETF (KBWR). Falls back to KRE if KBWR data absent.

Outputs:
  - analysis/capm_beta_results.json
  - analysis/capm_beta_results.md

Dependencies:
  - yfinance (pip install yfinance)

Usage:
  python3 scripts/compute_capm_beta.py --start 2023-01-01 --rf 0.0423 --erp 0.0585
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "analysis" / "capm_beta_results.json"
OUT_MD = ROOT / "analysis" / "capm_beta_results.md"


def _ensure_dirs() -> None:
    (ROOT / "analysis").mkdir(parents=True, exist_ok=True)


def fetch_prices(ticker: str, start: str, end: str) -> pd.Series:
    import yfinance as yf  # type: ignore
    data = yf.download(ticker, start=start, end=end, interval="1wk", progress=False, auto_adjust=False)
    if data.empty:
        return pd.Series(dtype=float)
    cols = data.columns
    series = None
    if isinstance(cols, pd.MultiIndex):
        if ("Adj Close", ticker) in cols:
            series = data[("Adj Close", ticker)]
        elif ("Close", ticker) in cols:
            series = data[("Close", ticker)]
    else:
        if "Adj Close" in cols:
            series = data["Adj Close"]
        elif "Close" in cols:
            series = data["Close"]
    if series is None or series.empty:
        return pd.Series(dtype=float)
    return pd.Series(series).rename(ticker)


def compute_weekly_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def run_capm(cat_returns: pd.Series, bench_returns: pd.Series) -> Dict:
    df = pd.concat([cat_returns, bench_returns], axis=1, join="inner").dropna()
    df.columns = ["caty", "bench"]
    x = df["bench"]
    y = df["caty"]
    n = len(df)
    x_mean = x.mean(); y_mean = y.mean()
    cov = ((x - x_mean) * (y - y_mean)).sum()
    var = ((x - x_mean) ** 2).sum()
    beta = float('nan') if var == 0 else cov / var
    alpha = y_mean - beta * x_mean if var != 0 else float('nan')
    ss_tot = ((y - y_mean) ** 2).sum()
    ss_res = ((y - (alpha + beta * x)) ** 2).sum() if var != 0 else float('nan')
    r2 = 1 - ss_res / ss_tot if isinstance(ss_res, float) and ss_tot != 0 else float('nan')
    return {"beta": float(beta), "alpha": float(alpha), "r2": float(r2), "observations": n}


def to_markdown(result: Dict, rf: float, erp: float, bench: str) -> str:
    coe = rf + result["beta"] * erp if not pd.isna(result["beta"]) else float('nan')
    lines = ["# CAPM Beta & COE (Weekly, ~2y)", ""]
    lines.append(f"Benchmark: {bench}")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Beta | {result['beta']:.4f} |")
    lines.append(f"| Alpha (weekly) | {result['alpha']:.5f} |")
    lines.append(f"| R^2 | {result['r2']:.4f} |")
    lines.append(f"| Observations | {result['observations']} |")
    lines.append(f"| COE (Rf + β×ERP) | {(coe*100):.2f}% |")
    return "\n".join(lines)


def main() -> int:
    _ensure_dirs()
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=(datetime.utcnow() - timedelta(days=730)).strftime("%Y-%m-%d"))
    parser.add_argument("--end", default=datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--rf", type=float, default=0.0423, help="Risk-free rate (annualized, decimal)")
    parser.add_argument("--erp", type=float, default=0.0585, help="Equity risk premium (annualized, decimal)")
    args = parser.parse_args()

    # Try KBWR, fallback to KRE
    bench = "KBWR"
    try:
        cat = fetch_prices("CATY", args.start, args.end)
        idx = fetch_prices(bench, args.start, args.end)
        if idx.empty:
            bench = "KRE"
            idx = fetch_prices(bench, args.start, args.end)
    except Exception as e:
        raise SystemExit(f"Error fetching prices: {e}")

    if cat.empty or idx.empty:
        raise SystemExit("Empty price series; check network or ticker availability.")

    res = run_capm(compute_weekly_returns(cat), compute_weekly_returns(idx))
    coe = args.rf + res["beta"] * args.erp if not pd.isna(res["beta"]) else float('nan')
    payload = {"benchmark": bench, "rf": args.rf, "erp": args.erp, "result": res, "coe": coe}
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    OUT_MD.write_text(to_markdown(res, args.rf, args.erp, bench))
    print(f"Wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
