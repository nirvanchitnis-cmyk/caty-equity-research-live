#!/usr/bin/env python3
"""Generate an explicit driver-to-financial bridge with reproducible elasticities."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEPOSIT_SCENARIOS_PATH = ROOT / "analysis" / "deposit_rate_scenarios.json"
CREDIT_SCENARIOS_PATH = ROOT / "analysis" / "credit_stress_scenarios.json"
DEPOSIT_BETA_PATH = ROOT / "analysis" / "deposit_beta_regressions.json"
INCOME_SNAPSHOT_PATH = ROOT / "data" / "caty02_income_statement.json"
MARKET_DATA_PATH = ROOT / "data" / "market_data_current.json"
OUTPUT_PATH = ROOT / "analysis" / "driver_elasticities.json"

SIGNIFICANCE_THRESHOLD = 2.0

# Rate / credit combinations to surface in the bridge.
BRIDGE_CASES = [
    {"name": "Base run-rate", "fed_delta_bps": 0, "credit": "Base LTM"},
    {"name": "Rate cut 50 bps", "fed_delta_bps": -50, "credit": "Base LTM"},
    {"name": "Credit guardrail", "fed_delta_bps": 0, "credit": "Guardrail"},
    {"name": "Cut 50 bps + guardrail credit", "fed_delta_bps": -50, "credit": "Guardrail"},
    {"name": "Credit stress (85 bps)", "fed_delta_bps": 0, "credit": "Stress"},
]


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_base_snapshot() -> Dict:
    income_payload = load_json(INCOME_SNAPSHOT_PATH)["q3_2025_snapshot"]
    market_payload = load_json(MARKET_DATA_PATH)
    return {
        "net_interest_income_m": income_payload["net_interest_income_millions"],
        "noninterest_income_m": income_payload["noninterest_income_millions"],
        "noninterest_expense_m": income_payload["noninterest_expense_millions"],
        "provision_m": income_payload["provision_millions"],
        "net_income_m": income_payload["net_income_millions"],
        "eps": income_payload["eps_diluted"],
        "tax_rate": income_payload["effective_tax_rate_pct"] / 100.0,
        "shares_out_m": market_payload["calculated_metrics"]["shares_outstanding_millions"],
    }


def index_rate_scenarios() -> Dict[int, Dict]:
    payload = load_json(DEPOSIT_SCENARIOS_PATH)
    return {item["fed_change_bps"]: item for item in payload["scenarios"]}


def index_credit_scenarios() -> Dict[str, Dict]:
    payload = load_json(CREDIT_SCENARIOS_PATH)
    return {item["scenario"]: item for item in payload["scenarios"]}


def load_deposit_scenario_series() -> Tuple[List[float], List[float], List[float]]:
    payload = load_json(DEPOSIT_SCENARIOS_PATH)
    deltas: List[float] = []
    eps_values: List[float] = []
    tbv_values: List[float] = []
    for item in payload["scenarios"]:
        deltas.append(float(item["fed_change_bps"]))
        eps_values.append(float(item["quarterly_eps"]))
        tbv_values.append(float(item["tbvps"]))
    return deltas, eps_values, tbv_values


def load_credit_scenario_series() -> Tuple[List[float], List[float], List[float]]:
    payload = load_json(CREDIT_SCENARIOS_PATH)
    nco_bps = [float(item["nco_bps"]) for item in payload["scenarios"]]
    eps_values = [float(item["eps"]) for item in payload["scenarios"]]
    tbv_values = [float(item["tbvps"]) for item in payload["scenarios"]]
    return nco_bps, eps_values, tbv_values


def linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    if len(x) != len(y):
        raise ValueError("Regression inputs x and y must share length")
    n = len(x)
    if n < 3:
        return {"slope": math.nan, "intercept": math.nan, "r2": math.nan, "std_err": math.nan, "t_stat": math.nan, "dof": n - 2}

    x_mean = sum(x) / n
    y_mean = sum(y) / n
    sxx = sum((xi - x_mean) ** 2 for xi in x)
    if sxx == 0:
        return {"slope": math.nan, "intercept": math.nan, "r2": math.nan, "std_err": math.nan, "t_stat": math.nan, "dof": n - 2}

    sxy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean

    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    ss_res = sum(res ** 2 for res in residuals)
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else math.nan

    dof = n - 2
    if dof <= 0:
        return {"slope": slope, "intercept": intercept, "r2": r2, "std_err": math.nan, "t_stat": math.nan, "dof": dof}

    variance = ss_res / dof
    std_err = math.sqrt(variance / sxx) if sxx else math.nan
    t_stat = slope / std_err if std_err and not math.isnan(std_err) else math.nan

    return {"slope": slope, "intercept": intercept, "r2": r2, "std_err": std_err, "t_stat": t_stat, "dof": dof}


def format_regression(reg: Dict[str, float], base_value: float, unit_label: str, scale: float = 10.0) -> Dict:
    slope = reg["slope"]
    intercept = reg["intercept"]
    per_scale = slope * scale if not math.isnan(slope) else math.nan
    elasticity_pct = (per_scale / base_value * 100.0) if base_value and not math.isnan(per_scale) else math.nan
    key_suffix = f"{int(scale)}{unit_label}"
    return {
        "equation": None if math.isnan(slope) else f"y = {intercept:.4f} + {slope:.6f}×Δ{unit_label}",
        "slope_per_unit": None if math.isnan(slope) else round(slope, 6),
        f"slope_per_{key_suffix}": None if math.isnan(per_scale) else round(per_scale, 4),
        f"elasticity_pct_per_{key_suffix}": None if math.isnan(elasticity_pct) else round(elasticity_pct, 2),
        "intercept": None if math.isnan(intercept) else round(intercept, 4),
        "r2": None if math.isnan(reg["r2"]) else round(reg["r2"], 4),
        "std_err": None if math.isnan(reg["std_err"]) else round(reg["std_err"], 6),
        "t_stat": None if math.isnan(reg["t_stat"]) else round(reg["t_stat"], 2),
        "degrees_of_freedom": reg["dof"],
        "significant": bool(reg.get("t_stat") and not math.isnan(reg["t_stat"]) and abs(reg["t_stat"]) >= SIGNIFICANCE_THRESHOLD),
        "significance_threshold_abs_t": SIGNIFICANCE_THRESHOLD,
        "scale_reference": f"{int(scale)} {unit_label}",
    }


def summarize_regressions(base_eps: float) -> Dict[str, Dict]:
    fed_delta, eps_series, tbv_series = load_deposit_scenario_series()
    nco_bps, credit_eps_series, credit_tbv_series = load_credit_scenario_series()

    deposit_eps_reg = linear_regression(fed_delta, eps_series)
    deposit_tbv_reg = linear_regression(fed_delta, tbv_series)
    credit_eps_reg = linear_regression(nco_bps, credit_eps_series)
    credit_tbv_reg = linear_regression(nco_bps, credit_tbv_series)

    deposit_payload = {
        "dependent": "Quarterly EPS and TBVPS",
        "independent": "Fed funds delta (bps vs Q3 base)",
        "sample": {
            "points": len(fed_delta),
            "range_bps": [min(fed_delta), max(fed_delta)] if fed_delta else None,
            "source": str(DEPOSIT_SCENARIOS_PATH.relative_to(ROOT)),
            "underlying_beta_sample": load_json(DEPOSIT_BETA_PATH).get("quarters", []),
        },
        "eps_regression": format_regression(deposit_eps_reg, base_eps, "bps"),
        "tbvps_regression": format_regression(deposit_tbv_reg, tbv_series[0] if tbv_series else math.nan, "bps"),
    }

    credit_payload = {
        "dependent": "Quarterly EPS and TBVPS",
        "independent": "Net charge-offs (bps)",
        "sample": {
            "points": len(nco_bps),
            "range_bps": [min(nco_bps), max(nco_bps)] if nco_bps else None,
            "source": str(CREDIT_SCENARIOS_PATH.relative_to(ROOT)),
            "fdic_series": "FDIC NTLNLSCOQR (through-cycle mean = 42.8 bps)",
        },
        "eps_regression": format_regression(credit_eps_reg, base_eps, "bps"),
        "tbvps_regression": format_regression(
            credit_tbv_reg, credit_tbv_series[0] if credit_tbv_series else math.nan, "bps"
        ),
    }

    return {"rate_path": deposit_payload, "credit_loss": credit_payload}


def deposit_beta_significance() -> Dict:
    payload = load_json(DEPOSIT_BETA_PATH)
    regressions = payload.get("regressions", {})
    products: List[Dict] = []
    for code, stats in regressions.items():
        t_stat = stats.get("t_stat")
        products.append(
            {
                "product": code,
                "beta": stats.get("beta"),
                "t_stat": t_stat,
                "r2": stats.get("r2"),
                "observations": stats.get("observations"),
                "significant": bool(t_stat is not None and abs(t_stat) >= SIGNIFICANCE_THRESHOLD),
            }
        )
    return {
        "source": str(DEPOSIT_BETA_PATH.relative_to(ROOT)),
        "significance_threshold_abs_t": SIGNIFICANCE_THRESHOLD,
        "products": products,
    }


def compute_bridge() -> Dict:
    base = load_base_snapshot()
    rate_map = index_rate_scenarios()
    credit_map = index_credit_scenarios()

    bridges: List[Dict] = []
    for case in BRIDGE_CASES:
        rate_case = rate_map.get(case["fed_delta_bps"])
        credit_case = credit_map.get(case["credit"])
        if rate_case is None:
            raise KeyError(f"Missing rate scenario for {case['fed_delta_bps']} bps")
        if credit_case is None:
            raise KeyError(f"Missing credit scenario '{case['credit']}'")

        nii = base["net_interest_income_m"] + rate_case["nii_delta_m"]
        provision = base["provision_m"] + credit_case["incremental_provision_m"]
        noninterest_income = base["noninterest_income_m"]
        noninterest_expense = base["noninterest_expense_m"]
        pre_tax = nii + noninterest_income - noninterest_expense - provision
        tax = pre_tax * base["tax_rate"]
        net_income = pre_tax - tax
        eps = net_income / base["shares_out_m"]

        bridge = {
            "name": case["name"],
            "fed_change_bps": case["fed_delta_bps"],
            "credit_scenario": case["credit"],
            "financials": {
                "net_interest_income_m": round(nii, 2),
                "noninterest_income_m": round(noninterest_income, 2),
                "noninterest_expense_m": round(noninterest_expense, 2),
                "provision_m": round(provision, 2),
                "pre_tax_income_m": round(pre_tax, 2),
                "tax_expense_m": round(tax, 2),
                "net_income_m": round(net_income, 2),
                "eps": round(eps, 2),
            },
            "deltas": {
                "nii_delta_m": round(rate_case["nii_delta_m"], 2),
                "interest_expense_delta_m": round(rate_case["interest_expense_delta_m"], 2),
                "provision_delta_m": round(credit_case["incremental_provision_m"], 2),
                "eps_delta": round(eps - base["eps"], 2),
            },
            "inputs": {
                "net_interest_income_base_m": base["net_interest_income_m"],
                "noninterest_income_base_m": base["noninterest_income_m"],
                "noninterest_expense_base_m": base["noninterest_expense_m"],
                "provision_base_m": base["provision_m"],
                "tax_rate": round(base["tax_rate"], 4),
                "shares_out_m": round(base["shares_out_m"], 2),
            },
        }
        bridges.append(bridge)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_snapshot": base,
        "bridge_cases": bridges,
        "metadata": {
            "sources": {
                "net_interest_income": "Form 8-K Exhibit 99.1 (Q3 2025)",
                "deposit_betas": "analysis/deposit_rate_scenarios.json",
                "credit": "analysis/credit_stress_scenarios.json",
                "shares": "data/market_data_current.json",
            }
        },
    }

    payload["regressions"] = summarize_regressions(base["eps"])
    payload["deposit_beta_significance"] = deposit_beta_significance()
    return payload


def main() -> int:
    payload = compute_bridge()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
