"""Quantify price sensitivities to net charge-off and deposit beta shocks."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np


PEER_CSV = Path(__file__).resolve().parents[1] / "evidence" / "peer_snapshot_2025Q2.csv"
OUTPUT_MD = Path(__file__).resolve().parents[1] / "evidence" / "valuation_sensitivity_summary.md"

# Balance sheet inputs (USD millions unless noted)
AVERAGE_LOANS = 19_448.955  # Average loans used in valuation bridge
TANGIBLE_COMMON_EQUITY = 2_465.091  # Average tangible common equity
TBVPS = 36.16
TOTAL_DEPOSITS = 20_006.0
NON_INTEREST_DDA_RATIO = 0.17  # From Q2'25 presentation
TAX_RATE = 0.20


def load_peer_regression() -> Tuple[float, float]:
    with PEER_CSV.open() as fh:
        reader = csv.DictReader(fh)
        peers = [row for row in reader if row["Ticker"] not in {"CATY", ""} and "Median" not in row.get("Company", "")]

    rote = np.array([float(p["ROTE_Pct"]) for p in peers if float(p["ROTE_Pct"]) > 0])
    ptbv = np.array([float(p["P_TBV"]) for p in peers if float(p["ROTE_Pct"]) > 0])
    slope, intercept = np.polyfit(rote, ptbv, deg=1)
    return slope, intercept


def price_for_rote(rote: float, slope: float, intercept: float) -> float:
    return (intercept + slope * rote) * TBVPS


def nco_price_delta(bps_delta: float, slope: float) -> float:
    delta_provision = (bps_delta / 10_000) * AVERAGE_LOANS
    delta_net_income = delta_provision * (1 - TAX_RATE)
    delta_rote = - (delta_net_income / TANGIBLE_COMMON_EQUITY) * 100
    return slope * delta_rote * TBVPS


def deposit_beta_price_delta(bps_delta: float, slope: float) -> float:
    interest_bearing_base = TOTAL_DEPOSITS * (1 - NON_INTEREST_DDA_RATIO)
    delta_interest_expense = (bps_delta / 10_000) * interest_bearing_base
    delta_net_income = delta_interest_expense * (1 - TAX_RATE)
    delta_rote = - (delta_net_income / TANGIBLE_COMMON_EQUITY) * 100
    return slope * delta_rote * TBVPS


def main() -> None:
    slope, intercept = load_peer_regression()
    base_price = price_for_rote(11.95, slope, intercept)

    nco_delta_10 = nco_price_delta(10, slope)
    nco_delta_25 = nco_price_delta(25, slope)
    nco_delta_50 = nco_price_delta(50, slope)

    beta_delta_10 = deposit_beta_price_delta(10, slope)
    beta_delta_25 = deposit_beta_price_delta(25, slope)
    beta_delta_50 = deposit_beta_price_delta(50, slope)

    markdown_lines = [
        "# Valuation Sensitivity Summary\n",
        "Baseline implied price (regression path): ${:.2f}".format(base_price),
        "",
        "## Net charge-off shocks\n",
        "Assumption: provision delta fully flows to after-tax earnings (20% tax).",
        "",
        "| NCO Shock | Price Impact |", 
        "|-----------|--------------|",
        "| +10 bps | ${:.2f} |".format(nco_delta_10),
        "| +25 bps | ${:.2f} |".format(nco_delta_25),
        "| +50 bps | ${:.2f} |".format(nco_delta_50),
        "",
        "## Deposit beta shocks\n",
        "Interest-bearing deposit base assumed at {:.1f}B (83% of total).".format(TOTAL_DEPOSITS * (1 - NON_INTEREST_DDA_RATIO) / 1_000),
        "",
        "| Beta Shock | Price Impact |",
        "|------------|--------------|",
        "| +10 bps | ${:.2f} |".format(beta_delta_10),
        "| +25 bps | ${:.2f} |".format(beta_delta_25),
        "| +50 bps | ${:.2f} |".format(beta_delta_50),
        "",
        "## Usage\n",
        "- Apply these deltas on top of scenario prices to articulate elasticities (e.g., +10 bps NCO reduces price by ${:.2f}).".format(nco_delta_10),
        "- Update TOTAL_DEPOSITS and NON_INTEREST_DDA_RATIO once Q3'25 figures are available.",
        "",
        "Generated via `analysis/valuation_sensitivity.py`.",
    ]

    OUTPUT_MD.write_text("\n".join(markdown_lines) + "\n")


if __name__ == "__main__":
    main()
