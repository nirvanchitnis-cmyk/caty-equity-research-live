#!/usr/bin/env python3
"""End-to-end CATY spot refresh with materiality logging and downstream rebuild."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fetch_live_price import fetch_latest_price, update_market_data

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
MARKET_DATA_PATH = DATA_DIR / "market_data_current.json"
MONTE_CARLO_PATH = DATA_DIR / "caty14_monte_carlo.json"
VALUATION_OUTPUTS_PATH = DATA_DIR / "valuation_outputs.json"
MARKET_COE_PATH = ROOT / "analysis" / "market_implied_coe.json"
MONTE_CARLO_MD_PATH = ROOT / "analysis" / "methodologies" / "MONTE_CARLO_VALUATION.md"
PRICE_REFRESH_LOG = LOG_DIR / "price_refresh_log.jsonl"

DEFAULT_THRESHOLD = 1.0  # percent move

SCENARIO_TEMPLATE: List[Dict[str, Any]] = [
    {
        "scenario": "Base (carry)",
        "probability_pct": 50,
        "target_price": 46.62,
        "annual_eps": 4.63,
        "nco_bps": 18,
        "description": "Fed cuts (−50/−25/0 bps blend) with benign credit migration.",
    },
    {
        "scenario": "Guardrail",
        "probability_pct": 30,
        "target_price": 43.71,
        "annual_eps": 4.07,
        "nco_bps": 43,
        "description": "Through-cycle mean NCO (43 bps) and modest rate relief.",
    },
    {
        "scenario": "Stress",
        "probability_pct": 15,
        "target_price": 38.73,
        "annual_eps": 3.11,
        "nco_bps": 85,
        "description": "Movie theatre/retail watchlist migration with flat/+25 bps rates.",
    },
    {
        "scenario": "Severe",
        "probability_pct": 5,
        "target_price": 34.78,
        "annual_eps": 2.35,
        "nco_bps": 120,
        "description": "GFC analogue: CRE downgrades widen losses, limited rate relief.",
    },
]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def format_currency(value: float, decimals: int = 2) -> str:
    return f"${value:,.{decimals}f}"


def format_signed_pct(value: float, *, decimals: int = 1, unicode_minus: bool = False) -> str:
    if abs(value) < 1e-9:
        return f"{0:.{decimals}f}%"
    sign_positive = "+" if value > 0 else ("−" if unicode_minus else "-")
    return f"{sign_positive}{abs(value):.{decimals}f}%"


def compute_return_pct(target: float, spot: float) -> float:
    if spot == 0:
        return 0.0
    return round((target - spot) / spot * 100, 1)


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def format_date_label(date_str: str | None) -> str:
    if not date_str:
        return "latest trading day"
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return date_str
    return parsed.strftime("%B %d, %Y")


@dataclass
class Snapshot:
    price: float
    price_date: str
    normalized_return_pct: float | None
    blended_return_pct: float | None

    @classmethod
    def from_market(cls, payload: Dict[str, Any]) -> "Snapshot":
        metrics = payload.get("calculated_metrics", {})
        return cls(
            price=float(payload.get("price", 0.0)),
            price_date=str(payload.get("price_date", "")),
            normalized_return_pct=_to_float(metrics.get("return_normalized_pct")),
            blended_return_pct=_to_float(metrics.get("return_irc_blended_pct")),
        )


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_materiality(before: Snapshot, after: Snapshot, threshold_pct: float) -> Dict[str, Any]:
    delta_abs = round(after.price - before.price, 2)
    baseline = before.price or after.price
    delta_pct = round((delta_abs / baseline) * 100, 2) if baseline else 0.0
    price_date_changed = before.price_date != after.price_date

    needs_revision = abs(delta_pct) >= threshold_pct
    if not needs_revision and (before.normalized_return_pct is not None and after.normalized_return_pct is not None):
        needs_revision = abs(after.normalized_return_pct - before.normalized_return_pct) >= 1.0
    if not needs_revision and (before.blended_return_pct is not None and after.blended_return_pct is not None):
        needs_revision = abs(after.blended_return_pct - before.blended_return_pct) >= 1.0

    status = "AGENT_REVISIONS_REQUIRED" if needs_revision else "REFRESHED_OK"
    if price_date_changed and not needs_revision:
        status = "REVIEW_NEW_DATE"

    if status == "AGENT_REVISIONS_REQUIRED":
        note = (
            f"Spot moved {format_signed_pct(delta_pct, decimals=2)} vs threshold {threshold_pct:.2f}% – "
            "agent narrative review required."
        )
    elif status == "REVIEW_NEW_DATE":
        note = "Price date changed even though move was immaterial – confirm disclosures."
    else:
        note = "Spot move immaterial; automated narratives remain in tolerance."

    return {
        "threshold_pct": round(threshold_pct, 2),
        "delta_pct": delta_pct,
        "delta_abs": delta_abs,
        "status": status,
        "note": note,
        "timestamp": now_utc().isoformat().replace("+00:00", "Z"),
        "before": {
            "price": round(before.price, 2),
            "price_date": before.price_date,
            "normalized_return_pct": before.normalized_return_pct,
            "irc_blended_return_pct": before.blended_return_pct,
        },
        "after": {
            "price": round(after.price, 2),
            "price_date": after.price_date,
            "normalized_return_pct": after.normalized_return_pct,
            "irc_blended_return_pct": after.blended_return_pct,
        },
    }


def append_log(entry: Dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with PRICE_REFRESH_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True))
        handle.write("\n")


def update_monte_carlo_payload(market_payload: Dict[str, Any]) -> Dict[str, Any]:
    if not MONTE_CARLO_PATH.exists():
        return {}

    monte = load_json(MONTE_CARLO_PATH)
    valuation_outputs = load_json(VALUATION_OUTPUTS_PATH) if VALUATION_OUTPUTS_PATH.exists() else {}

    spot = round(float(market_payload.get("price", 0.0)), 2)
    summary = monte.setdefault("simulation_summary", {})
    target_median = float(summary.get("target_median", 0.0))
    target_mean = float(summary.get("target_mean", 0.0))

    median_return_pct = compute_return_pct(target_median, spot)
    mean_return_pct = compute_return_pct(target_mean, spot)
    summary["spot_price"] = spot
    summary["median_return_pct"] = median_return_pct
    summary["mean_return_pct"] = mean_return_pct
    summary["rating_rationale"] = (
        f"Median {format_signed_pct(median_return_pct)} and mean {format_signed_pct(mean_return_pct)} vs spot "
        "flag downside skew, but delta remains within HOLD guardrails pending Q3 10-Q evidence."
    )

    loss_probability = summary.get("loss_probability", 60.9)
    probability_html = (
        f"<p><strong>P(Target &lt; {format_currency(spot)}):</strong> <strong>{loss_probability:.1f}%</strong></p>"
    )
    summary["probability_of_loss_html"] = probability_html

    key_findings = (
        "<ol>\n"
        f"    <li><strong>Median outcome:</strong> {format_currency(target_median)} "
        f"({format_signed_pct(median_return_pct)} vs spot) =&gt; valuation skew now negative.</li>\n"
        "    <li><strong>Downside tail:</strong> $24.60 5th percentile aligns with severe CRE migration.</li>\n"
        "    <li><strong>Upside tail:</strong> Requires ROTE &gt;14% and NCO &lt;20 bps (probability 17%).</li>\n"
        f"    <li><strong>Loss probability:</strong> {loss_probability:.1f}% of simulations end below {format_currency(spot)}.</li>\n"
        "</ol>"
    )
    summary["key_findings_html"] = key_findings

    confidence = monte.setdefault("confidence_interval", {})
    lower = float(confidence.get("lower_price", 0.0))
    upper = float(confidence.get("upper_price", 0.0))
    confidence["range_dollars"] = round(upper - lower, 1)
    confidence["range_pct_of_spot"] = round(((upper - lower) / spot) * 100, 1) if spot else confidence.get(
        "range_pct_of_spot", 0.0
    )

    probability_block = monte.setdefault("probability_of_loss", {})
    probability_block["loss_probability_display"] = f"{loss_probability:.1f}%"
    probability_block["gain_probability_display"] = f"{100 - loss_probability:.1f}%"

    tables = monte.setdefault("tables", {})

    if "sensitivity" not in tables:
        tables["sensitivity"] = []
    if "methodology_comparison" not in tables:
        tables["methodology_comparison"] = []

    percentiles = [
        ("5th Percentile", 24.60, "Severe CRE migration"),
        ("25th Percentile", 34.64, "Guardrail credit + flat rates"),
        ("50th Percentile (Median)", target_median, "Probability-weighted base"),
        ("75th Percentile", 51.24, "Benign credit"),
        ("95th Percentile", 66.00, "ROTE expansion"),
    ]
    tables["percentiles"] = [
        {
            "row_class": "base-case" if label.startswith("50th") else "",
            "label": label,
            "target_price": format_currency(price),
            "return": format_signed_pct(compute_return_pct(price, spot)),
            "scenario": scenario,
        }
        for label, price, scenario in percentiles
    ]

    scenario_rows = []
    for entry in SCENARIO_TEMPLATE:
        price = float(entry["target_price"])
        scenario_rows.append(
            {
                "scenario": entry["scenario"],
                "probability": f"{entry['probability_pct']}%",
                "target_price": format_currency(price),
                "return": format_signed_pct(compute_return_pct(price, spot)),
                "annual_eps": format_currency(entry["annual_eps"]),
                "nco_bps": f"{entry['nco_bps']} bps",
                "description": entry["description"],
            }
        )
    tables["scenario_breakdown"] = scenario_rows

    valuation_fw = valuation_outputs.get("frameworks", {})
    pw_target = _to_float(valuation_fw.get("probability_weighted", {}).get("target_price"))
    blended_gap_pct = compute_return_pct(pw_target, spot) if pw_target is not None else None

    narratives = monte.setdefault("narratives", {})
    narratives["key_findings_html"] = key_findings
    narratives["probability_of_loss_html"] = probability_html
    narratives["rating_implication_html"] = (
        "<p><strong>Rating Implication:</strong> Negative skew warrants caution, but with spot now "
        f"{format_signed_pct(blended_gap_pct) if blended_gap_pct is not None else 'within guardrails'} "
        "above intrinsic value we maintain a <strong>HOLD</strong> pending fresh evidence.</p>"
    )
    narratives.setdefault(
        "sensitivity_highlight_html",
        "<p class=\"font-size-12\">Sensitivity rerun pending refreshed Monte Carlo drivers.</p>",
    )
    narratives.setdefault(
        "methodology_interpretation_html",
        "<p class=\"font-size-12\">Methodology comparison narrative will refresh after next Monte Carlo rerun.</p>",
    )

    monte["key_findings_html"] = key_findings
    monte["probability_of_loss_html"] = probability_html
    monte["last_updated"] = now_utc().isoformat().replace("+00:00", "Z")

    write_json(MONTE_CARLO_PATH, monte)
    return monte


def update_market_implied_coe(market_payload: Dict[str, Any]) -> Dict[str, Any]:
    if not MARKET_COE_PATH.exists():
        return {}
    data = load_json(MARKET_COE_PATH)
    inputs = data.setdefault("inputs", {})

    spot = float(market_payload.get("price", 0.0))
    inputs["spot"] = round(spot, 2)

    tbvps = float(inputs.get("tbvps", 0.0))
    ptbv = round(spot / tbvps, 3) if tbvps else None
    if ptbv is not None:
        inputs["ptbv"] = ptbv

    roe = float(inputs.get("roe", 0.0))
    growth = float(inputs.get("growth", 0.0))
    model_coe = float(inputs.get("model_coe", 0.0))
    implied_coe = growth + (roe - growth) / ptbv if ptbv else model_coe
    data["implied_coe"] = round(implied_coe, 4)
    data["difference_bps"] = round((implied_coe - model_coe) * 10000, 1)
    data["generated_at"] = now_utc().isoformat().replace("+00:00", "Z")

    write_json(MARKET_COE_PATH, data)
    return data


def update_coe_crosscheck(market_payload: Dict[str, Any], market_implied: Dict[str, Any]) -> None:
    coe_path = DATA_DIR / "caty16_coe_triangulation.json"
    if not coe_path.exists():
        return

    data = load_json(coe_path)
    narratives = data.setdefault("narratives", {})
    validation = data.setdefault("validation", {})
    coe_summary = data.get("coe_summary", {})

    spot = float(market_payload.get("price", 0.0))
    metrics = market_payload.get("calculated_metrics", {})
    tbvps = float(metrics.get("tbvps") or market_implied.get("inputs", {}).get("tbvps") or validation.get("tbvps", 0.0))
    ptbv = round(spot / tbvps, 3) if tbvps else None

    implied_coe_pct = round(float(market_implied.get("implied_coe", 0.0)) * 100, 2)
    model_coe_pct = coe_summary.get("final_coe_pct")
    difference_bps = market_implied.get("difference_bps")
    roe_pct = round(float(market_implied.get("inputs", {}).get("roe", 0.0)) * 100, 2)
    growth_pct = round(float(market_implied.get("inputs", {}).get("growth", 0.0)) * 100, 2)

    if ptbv is not None:
        validation["actual_ptbv"] = ptbv
    validation["price"] = round(spot, 2)
    validation["price_as_of_display"] = format_date_label(market_payload.get("price_date"))
    validation["market_implied_coe_pct"] = implied_coe_pct

    if difference_bps is None:
        diff_sentence = ""
    else:
        if difference_bps >= 0:
            diff_sentence = (
                f" The {difference_bps:.1f} bps gap versus the {model_coe_pct:.2f}% model output remains within tolerance."
            )
        else:
            diff_sentence = (
                f" The {abs(difference_bps):.1f} bps lighter implied COE vs the {model_coe_pct:.2f}% model output sits within tolerance."
            )

    ptbv_text = f"{ptbv:.3f}" if ptbv is not None else "n/a"
    tbvps_text = format_currency(tbvps) if tbvps else "n/a"

    note_html = (
        '<div class="highlight-box info">'
        '<h4>Market-Implied Cross-Check</h4>'
        f'<p>At {format_currency(spot)} spot and TBV {tbvps_text} (P/TBV {ptbv_text}×), '
        f"the Gordon bridge implies a <strong>{implied_coe_pct:.2f}%</strong> cost of equity assuming ROE {roe_pct:.2f}% "
        f"and terminal growth {growth_pct:.2f}%.{diff_sentence}</p>"
        "</div>"
    )
    narratives["market_implied_note_html"] = note_html

    write_json(coe_path, data)


def update_static_html_spot(market_payload: Dict[str, Any]) -> None:
    spot = float(market_payload.get("price", 0.0))
    if spot <= 0:
        return
    pattern = r"(vs spot \$)\d+\.\d{2}"
    replacement = f"\\1{spot:.2f}"
    targets = [ROOT / "CATY_12_valuation_model.html"]
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new_text, count = re.subn(pattern, replacement, text)
        if count:
            path.write_text(new_text, encoding="utf-8")


def update_caty12_narratives(market_payload: Dict[str, Any]) -> None:
    path = DATA_DIR / "caty12_calculated_tables.json"
    if not path.exists():
        return
    data = load_json(path)
    narratives = data.setdefault("narratives", {})
    metrics = market_payload.get("calculated_metrics", {})
    target_irc = metrics.get("target_irc_blended")
    if target_irc is None:
        return
    spot = market_payload.get("price")
    narratives["valuation_bridge_subtitle"] = (
        "Weighted combination of Residual Income, Dividend Discount, and Regression frameworks; "
        f"contributions accumulate to the {format_currency(target_irc)} IRC target vs spot {format_currency(spot)}."
    )
    write_json(path, data)


def replace_block(path: Path, marker: str, new_content: str) -> None:
    """Replace content between <!-- BEGIN AUTOGEN: marker --> and <!-- END AUTOGEN: marker -->."""
    begin = f"<!-- BEGIN AUTOGEN: {marker} -->"
    end = f"<!-- END AUTOGEN: {marker} -->"
    text = path.read_text(encoding="utf-8")
    if begin not in text or end not in text:
        raise ValueError(f"Markers for '{marker}' not found in {path}")

    start_index = text.index(begin) + len(begin)
    end_index = text.index(end)
    updated = text[:start_index] + "\n" + new_content.strip() + "\n" + text[end_index:]
    path.write_text(updated, encoding="utf-8")


def update_monte_carlo_markdown(monte_payload: Dict[str, Any]) -> None:
    if not MONTE_CARLO_MD_PATH.exists() or not monte_payload:
        return

    summary = monte_payload.get("simulation_summary", {})
    confidence = monte_payload.get("confidence_interval", {})
    percentiles = monte_payload.get("tables", {}).get("percentiles", [])

    spot = summary.get("spot_price")
    target_median = summary.get("target_median")
    target_mean = summary.get("target_mean")
    median_return = summary.get("median_return_pct")
    mean_return = summary.get("mean_return_pct")
    loss_probability = monte_payload.get("probability_of_loss", {}).get("loss_probability_pct", 0.0)

    summary_block = "\n".join(
        [
            f"**Monte Carlo Target Price (50th Percentile):** **{format_currency(target_median)}** "
            f"({format_signed_pct(median_return, unicode_minus=True)} vs. {format_currency(spot)} spot)",
            "",
            f"**95% Confidence Interval:** {format_currency(confidence.get('lower_price', 0.0))} to "
            f"{format_currency(confidence.get('upper_price', 0.0))} "
            f"(range: {format_currency(confidence.get('range_dollars', 0.0))}, "
            f"{round(confidence.get('range_pct_of_spot', 0.0), 1):.1f}% of spot price)",
            "",
            "**Key Findings:**",
            f"1. **Distribution Shape:** Right-skewed but centered below spot; mean {format_currency(target_mean)} "
            f"vs median {format_currency(target_median)}.",
            f"2. **Downside Risk (5th percentile):** {format_currency(24.60)} "
            f"({format_signed_pct(compute_return_pct(24.60, spot), unicode_minus=True)} vs. spot) traces to CRE migration.",
            f"3. **Upside Potential (95th percentile):** {format_currency(66.00)} "
            f"({format_signed_pct(compute_return_pct(66.00, spot), unicode_minus=True)} vs. spot) requires ROTE >14% with benign credit.",
            f"4. **Probability of Loss:** {loss_probability:.1f}% (price < {format_currency(spot)} spot) → downside dominates.",
            f"5. **Expected Value:** {format_currency(target_mean)} "
            f"({format_signed_pct(mean_return, unicode_minus=True)} vs. spot) – mean stays below spot despite right tail.",
        ]
    )
    replace_block(MONTE_CARLO_MD_PATH, "mc-summary", summary_block)

    table_lines = [
        f"| Percentile | Target Price | Return vs. Spot ({format_currency(spot)}) | Scenario |",
        "|------------|--------------|--------------------------|----------|",
    ]
    for row in percentiles:
        table_lines.append(
            f"| **{row['label'].replace('(Median)', '').strip()}** | {row['target_price']} | "
            f"**{row['return']}** | {row['scenario']} |"
        )
    replace_block(MONTE_CARLO_MD_PATH, "mc-percentiles-table", "\n".join(table_lines))

    loss_block = (
        f"**P(Target < {format_currency(spot)}):** **{loss_probability:.1f}%** – "
        "loss probability remains above upside despite rate-cut scenarios."
    )
    replace_block(MONTE_CARLO_MD_PATH, "mc-loss-highlight", loss_block)

    rating_block = (
        "Monte Carlo **median {median} ({median_return})** and **mean {mean} ({mean_return})** both trail the share price, "
        "underscoring limited upside until Q3 10-Q clarifies credit migration."
    ).format(
        median=format_currency(target_median),
        median_return=format_signed_pct(median_return, unicode_minus=True),
        mean=format_currency(target_mean),
        mean_return=format_signed_pct(mean_return, unicode_minus=True),
    )
    replace_block(MONTE_CARLO_MD_PATH, "mc-rating-implication", rating_block)


def run_command(command: List[str], label: str) -> None:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed: {result.stderr.strip() or result.stdout.strip()}")


def build_site() -> None:
    run_command(["python3", str(ROOT / "scripts" / "build_site.py")], "build_site.py")


def rebuild_peers() -> None:
    run_command(["python3", str(ROOT / "scripts" / "fetch_peer_prices.py")], "fetch_peer_prices.py")
    run_command(["python3", str(ROOT / "scripts" / "build_peer_comparables.py")], "build_peer_comparables.py")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh CATY market data and rebuild dependent assets.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Materiality threshold in percent for requiring agent revisions (default: 1.0%%).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Trading-day lookback window for yfinance history (default: 5).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip rebuilding the static site after refreshing data.",
    )
    parser.add_argument(
        "--skip-peers",
        action="store_true",
        help="Skip peer price refresh and comparables rebuild.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch latest price and show diffs without mutating files.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    before_payload = load_json(MARKET_DATA_PATH)
    before_snapshot = Snapshot.from_market(before_payload)

    print("=" * 72)
    print("CATY Spot Refresh | yfinance provider | Materiality-aware pipeline")
    print("=" * 72)
    print(f"• Previous close: {format_currency(before_snapshot.price)} (as of {before_snapshot.price_date})")

    price, price_date = fetch_latest_price(days=args.window)
    print(f"• Latest available: {format_currency(price)} (as of {price_date})")

    if args.dry_run:
        temp_payload = dict(before_payload)
        temp_payload["price"] = price
        temp_payload["price_date"] = price_date
        temp_snapshot = Snapshot.from_market(temp_payload)
        materiality = compute_materiality(before_snapshot, temp_snapshot, args.threshold)
        print(f"• Δ vs previous: {materiality['delta_abs']:+.2f} | {materiality['delta_pct']:+.2f}%")
        print(f"• Materiality status: {materiality['status']} ({materiality['note']})")
        print("\n[DRY RUN] No files were changed.")
        return 0

    after_payload = update_market_data(price, price_date)
    after_snapshot = Snapshot.from_market(after_payload)
    materiality = compute_materiality(before_snapshot, after_snapshot, args.threshold)
    after_payload["materiality"] = materiality
    write_json(MARKET_DATA_PATH, after_payload)

    log_entry = {
        "timestamp": now_utc().isoformat().replace("+00:00", "Z"),
        "threshold_pct": args.threshold,
        "provider": "yfinance",
        "materiality": materiality,
    }

    try:
        monte_payload = update_monte_carlo_payload(after_payload)
        market_implied = update_market_implied_coe(after_payload)
        update_coe_crosscheck(after_payload, market_implied)
        update_monte_carlo_markdown(monte_payload)
        update_static_html_spot(after_payload)
        update_caty12_narratives(after_payload)
        if not args.skip_peers:
            rebuild_peers()
        if not args.skip_build:
            build_site()
        log_entry["status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        log_entry["status"] = "error"
        log_entry["error"] = str(exc)
        append_log(log_entry)
        raise
    else:
        append_log(log_entry)

    print(f"• Δ vs previous: {materiality['delta_abs']:+.2f} | {materiality['delta_pct']:+.2f}%")
    print(f"• Materiality status: {materiality['status']}")
    print(f"  {materiality['note']}")
    print(f"• Snapshot logged to {PRICE_REFRESH_LOG.relative_to(ROOT)}")
    if not args.skip_build:
        print("• Site rebuilt via scripts/build_site.py")
    if not args.skip_peers:
        print("• Peer comparables refreshed")

    print("=" * 72)
    if materiality["status"] == "AGENT_REVISIONS_REQUIRED":
        print("ACTION: Agent review is required. Update narrative copy before publishing.")
    else:
        print("All clear: Numerical adjustments within tolerances; narratives auto-updated.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
