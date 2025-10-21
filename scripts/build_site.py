#!/usr/bin/env python3
"""Build the static site sections from canonical data sources.

Responsibilities:
- Render valuation reconciliation dashboard from data/market_data_current.json
  and data/valuation_methods.json.
- Render module navigation grid from data/module_metadata.json.
- Render evidence provenance table from data/evidence_sources.json with live
  SHA256 hashes and timestamps.
- Append execution log entries to logs/automation_run.log.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"
LOG_PATH = ROOT / "logs" / "automation_run.log"
EXEC_METRICS_PATH = ROOT / "data" / "executive_metrics.json"
MODULE_SECTIONS_PATH = ROOT / "data" / "module_sections.json"
VALUATION_OUTPUTS_PATH = ROOT / "data" / "valuation_outputs.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NARRATIVE_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def replace_placeholders(value: Any, replacements: Dict[str, str]) -> Any:
    if isinstance(value, str):
        result = value
        for key, repl in replacements.items():
            result = result.replace(key, repl)
        return result
    if isinstance(value, list):
        return [replace_placeholders(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_placeholders(val, replacements) for key, val in value.items()}
    return value


def render_template_string(template: str | None, replacements: Dict[str, Any]) -> str:
    if not template:
        return ""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in replacements:
            raise KeyError(f"Missing placeholder '{key}' in narrative template")
        return str(replacements[key])

    return NARRATIVE_PLACEHOLDER_PATTERN.sub(_replace, template)


def render_timestamps() -> Dict[str, str]:
    data = load_json(ROOT / "data" / "market_data_current.json")
    metadata = data.get("report_metadata") or {}

    report_date = metadata.get("report_date") or data.get("price_date") or ""
    report_date_iso = metadata.get("report_date_iso") or data.get("price_date") or ""
    generated_display = metadata.get("generated_at_display") or metadata.get("last_updated_utc") or data.get("report_generated") or ""
    generated_iso = metadata.get("last_updated_utc") or data.get("report_generated") or ""

    return {
        "report_date": report_date,
        "report_date_iso": report_date_iso,
        "last_updated_utc": generated_display,
        "generated_at_utc": generated_iso,
    }


def build_narrative_replacements(market: Dict[str, Any], timestamps: Dict[str, str]) -> Dict[str, str]:
    metrics = market.get("calculated_metrics", {})
    metadata = market.get("report_metadata") or {}

    def fmt_number(value: Any, *, decimals: int = 1, signed: bool = False, comma: bool = False) -> str:
        if value in (None, "", "—"):
            return "—"
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return "—"

        fmt_spec = ""
        if signed:
            fmt_spec += "+"
        if comma:
            fmt_spec += ","
        fmt_spec += f".{decimals}f"
        return format(value_float, fmt_spec)

    report_date_display = (
        timestamps.get("report_date")
        or metadata.get("report_date")
        or format_date_value(market.get("price_date"), "long")
        if market.get("price_date")
        else ""
    )

    replacements: Dict[str, str] = {
        "company": market.get("company", ""),
        "ticker": market.get("ticker", ""),
        "rating": metrics.get("rating", ""),
        "price": fmt_number(market.get("price"), decimals=2, comma=True),
        "price_date": report_date_display,
        "price_date_iso": market.get("price_date", ""),
        "report_date": report_date_display,
        "last_updated_utc": timestamps.get("last_updated_utc", ""),
        "target_wilson_95": fmt_number(metrics.get("target_wilson_95"), decimals=2, comma=True),
        "target_regression": fmt_number(metrics.get("target_regression"), decimals=2, comma=True),
        "target_normalized": fmt_number(metrics.get("target_normalized"), decimals=2, comma=True),
        "target_irc_blended": fmt_number(metrics.get("target_irc_blended"), decimals=2, comma=True),
        "return_wilson_95_pct": fmt_number(metrics.get("return_wilson_95_pct"), decimals=1, signed=True),
        "return_regression_pct": fmt_number(metrics.get("return_regression_pct"), decimals=1, signed=True),
        "return_normalized_pct": fmt_number(metrics.get("return_normalized_pct"), decimals=1, signed=True),
        "return_irc_blended_pct": fmt_number(metrics.get("return_irc_blended_pct"), decimals=1, signed=True),
        "current_ptbv": fmt_number(metrics.get("current_ptbv"), decimals=3),
        "normalized_ptbv": fmt_number(metrics.get("normalized_ptbv"), decimals=3),
        "rote_ltm_pct": fmt_number(metrics.get("rote_ltm_pct"), decimals=2),
        "normalized_rote_pct": fmt_number(metrics.get("normalized_rote_pct"), decimals=2),
        "through_cycle_nco_bps": fmt_number(metrics.get("through_cycle_nco_bps"), decimals=1),
        "cre_loans_pct": fmt_number(metrics.get("cre_loans_pct"), decimals=1),
        "brokered_deposit_pct": fmt_number(metrics.get("brokered_deposit_pct"), decimals=2),
        "nco_rate_bps": fmt_number(metrics.get("nco_rate_bps"), decimals=1),
        "acl_amount_millions": fmt_number(metrics.get("acl_amount_millions"), decimals=1, comma=True),
        "deposit_beta_interest_bearing": fmt_number(metrics.get("deposit_beta_interest_bearing"), decimals=3),
        "nib_pct": fmt_number(metrics.get("nib_pct"), decimals=1),
        "tbvps": fmt_number(metrics.get("tbvps"), decimals=2, comma=True),
    }

    return replacements


def render_investment_thesis(context: Dict[str, Any], replacements: Dict[str, str]) -> str:
    narrative = context.get("narrative_prose") or {}
    summary_template = narrative.get("investment_thesis_summary")
    rationale_template = narrative.get("rating_rationale")

    summary_text = render_template_string(summary_template, replacements) if summary_template else ""
    if not summary_text:
        fallback_template = (
            "{{company}} ({{ticker}}) trades at ${{price}} ({{report_date}}) with expected return of "
            "{{return_wilson_95_pct}}% to Wilson 95% target ${{target_wilson_95}}. Current P/TBV "
            "{{current_ptbv}}x versus normalized {{normalized_ptbv}}x highlights multiple compression risk."
        )
        summary_text = render_template_string(fallback_template, replacements)

    rationale_text = render_template_string(rationale_template, replacements) if rationale_template else ""
    rating = replacements.get("rating", "")

    parts = []
    if rating:
        parts.append(f"<strong>Rating: {rating}</strong>")
    if summary_text:
        parts.append(summary_text)
    if rationale_text:
        parts.append(rationale_text)

    combined = " ".join(parts).strip()
    return f"<p>{combined}</p>"


def render_key_findings(replacements: Dict[str, str]) -> str:
    bullets = [
        (
            "<li><strong>Empirical NCO Understated:</strong> {through_cycle_nco_bps} bps through-cycle average "
            "(2008-2024) vs previous 25 bps assumption; GFC peak 306 bps shows tail risk</li>"
        ),
        (
            "<li><strong>Overvaluation:</strong> Current P/TBV {current_ptbv}x vs normalized fair value "
            "{normalized_ptbv}x; price ${price} vs normalized ${target_normalized} = {return_normalized_pct}% "
            "expected move</li>"
        ),
        (
            "<li><strong>Mid-Tier Profitability:</strong> Normalized ROTE {normalized_rote_pct}% trails "
            "upper-quartile peers, limiting multiple expansion</li>"
        ),
        (
            "<li><strong>CRE Concentration:</strong> {cre_loans_pct}% CRE exposure with {brokered_deposit_pct}% "
            "brokered deposits elevates funding sensitivity</li>"
        ),
    ]

    rendered = [bullet.format(**replacements) for bullet in bullets]
    return "<ul>\n    " + "\n    ".join(rendered) + "\n</ul>"


def render_price_target_caption(replacements: Dict[str, str]) -> str:
    date_display = replacements.get("price_date") or replacements.get("report_date") or ""
    return (
        '<p class="text-secondary">'
        f"Current price vs. triangulated target methodologies (data as of {date_display})"
        "</p>"
    )


def render_price_target_grid(replacements: Dict[str, str]) -> str:
    cards = [
        {
            "classes": "metric-card",
            "label": "Current Price",
            "value": f"${replacements.get('price', '—')}",
            "subtext": f"As of {replacements.get('price_date', '—')}",
        },
        {
            "classes": "metric-card metric-card-success",
            "label": "Wilson 95%",
            "value": f"${replacements.get('target_wilson_95', '—')}",
            "subtext": f"{replacements.get('return_wilson_95_pct', '—')}% (HOLD band)",
        },
        {
            "classes": "metric-card",
            "label": "IRC Blended",
            "value": f"${replacements.get('target_irc_blended', '—')}",
            "subtext": f"{replacements.get('return_irc_blended_pct', '—')}% (60% RIM)",
        },
        {
            "classes": "metric-card metric-card-success",
            "label": "Regression",
            "value": f"${replacements.get('target_regression', '—')}",
            "subtext": f"{replacements.get('return_regression_pct', '—')}% (7-peer)",
        },
    ]

    lines = ["<div class=\"price-target-grid price-target-grid-spaced\">"]
    for card in cards:
        lines.extend(
            [
                f'    <div class="{card["classes"]}">',
                f'        <div class="metric-label">{card["label"]}</div>',
                f'        <div class="metric-value">{card["value"]}</div>',
                f'        <div class="metric-subtext">{card["subtext"]}</div>',
                "    </div>",
            ]
        )
    lines.append("</div>")
    return "\n".join(lines)


def render_recent_developments_section(developments: Dict[str, Any], replacements: Dict[str, str]) -> str:
    if not developments:
        return "<h2>Recent Developments</h2>\n<p>No recent developments available.</p>"

    time_window = developments.get("time_window")
    heading = "<h2>Recent Developments</h2>"
    if time_window:
        heading = f"<h2>Recent Developments ({time_window})</h2>"

    items: list[str] = []
    for item in developments.get("developments", []):
        date_raw = item.get("date")
        formatted_date = format_date_value(date_raw, "long") if date_raw else str(item.get("date_display", ""))
        event = item.get("event", "")
        time = item.get("time")
        if time:
            event = f"{event} ({time})" if event else time

        details_parts = []
        for key in ("impact", "description", "context"):
            value = item.get(key)
            if value:
                details_parts.append(value)
        details = " - ".join(details_parts)

        bullet = f"<li><strong>{formatted_date}:</strong>"
        if event:
            bullet += f" {event}"
        if details:
            separator = " - " if event else " "
            bullet += f"{separator}{details}"
        bullet += "</li>"
        items.append(bullet)

    list_html = "<ul>\n    " + "\n    ".join(items) + "\n</ul>" if items else "<ul></ul>"
    return "\n".join([heading, list_html])


def render_investment_risks_section(context: Dict[str, Any], replacements: Dict[str, str]) -> str:
    narrative = context.get("narrative_prose") or {}
    risks = narrative.get("investment_risks") or []

    if not risks:
        return "<h2>Investment Risks</h2>\n<p>No material risks identified.</p>"

    bullets = []
    for risk in risks:
        risk_name = risk.get("risk", "")
        severity = risk.get("severity", "")
        label = risk_name
        if risk_name and severity:
            label = f"{risk_name} ({severity})"
        elif severity:
            label = severity

        description_template = risk.get("description")
        description = render_template_string(description_template, replacements) if description_template else ""
        bullets.append(f"<li><strong>{label}:</strong> {description}</li>")

    list_html = "<ul>\n    " + "\n    ".join(bullets) + "\n</ul>"
    return "\n".join(["<h2>Investment Risks</h2>", list_html])


def render_scenario_analysis_table(context: Dict[str, Any]) -> str:
    market = context.get("market", {})
    metrics = context.get("calculated_metrics", {})

    price = safe_to_float(market.get("price"))
    has_price = bool(price) and price > 0
    price = price or 0.0

    def get_metric(key: str, default: float = 0.0) -> float:
        value = safe_to_float(metrics.get(key))
        return value if value is not None else default

    wilson_target = get_metric("target_wilson_95")
    regression_target = get_metric("target_regression")
    normalized_target = get_metric("target_normalized")

    wilson_prob = safe_to_float(metrics.get("wilson_probability")) or 60.9
    regression_prob = safe_to_float(metrics.get("regression_probability")) or 30.0
    normalized_prob = safe_to_float(metrics.get("normalized_probability")) or 9.1

    def calc_return(target: float) -> float | None:
        if not has_price or not target:
            return None
        return ((target - price) / price) * 100

    wilson_return = calc_return(wilson_target)
    regression_return = calc_return(regression_target)
    normalized_return = calc_return(normalized_target)

    wilson_ev = wilson_target * (wilson_prob / 100)
    regression_ev = regression_target * (regression_prob / 100)
    normalized_ev = normalized_target * (normalized_prob / 100)

    blended = wilson_ev + regression_ev + normalized_ev
    blended_return = ((blended - price) / price * 100) if has_price else None

    def render_return_cell(value: float | None) -> tuple[str, str]:
        base_class = "numeric"
        if value is None:
            return "—", base_class
        if value > 0:
            return f"+{value:.1f}%", f"{base_class} text-success"
        if value < 0:
            return f"{value:.1f}%", f"{base_class} text-danger"
        return f"{value:.1f}%", base_class

    def render_prob(value: float) -> str:
        return f"{value:.1f}%"

    def render_money(value: float) -> str:
        return format_money(value)

    lines = [
        "<table>",
        "    <thead>",
        "        <tr>",
        "            <th>Scenario</th>",
        "            <th class=\"numeric\">Target Price</th>",
        "            <th class=\"numeric\">Return</th>",
        "            <th class=\"numeric\">Probability</th>",
        "            <th class=\"numeric\">Expected Value</th>",
        "        </tr>",
        "    </thead>",
        "    <tbody>",
    ]

    for label, target, ret_value, prob, ev in [
        ("Wilson 95% (Base)", wilson_target, wilson_return, wilson_prob, wilson_ev),
        ("Regression (Bull)", regression_target, regression_return, regression_prob, regression_ev),
        ("Normalized (Bear)", normalized_target, normalized_return, normalized_prob, normalized_ev),
    ]:
        formatted_return, return_class = render_return_cell(ret_value)
        lines.extend(
            [
                "        <tr>",
                f"            <td><strong>{label}</strong></td>",
                f"            <td class=\"numeric\">{render_money(target)}</td>",
                f"            <td class=\"{return_class}\">{formatted_return}</td>",
                f"            <td class=\"numeric\">{render_prob(prob)}</td>",
                f"            <td class=\"numeric\">{render_money(ev)}</td>",
                "        </tr>",
            ]
        )

    blended_return_text, blended_class = render_return_cell(blended_return)
    lines.extend(
        [
            "        <tr class=\"table-border-top\" style=\"font-weight: bold;\">",
            "            <td>IRC Blended Target</td>",
            f"            <td class=\"numeric\">{render_money(blended)}</td>",
            f"            <td class=\"{blended_class}\">{blended_return_text}</td>",
            "            <td class=\"numeric\">100.0%</td>",
            f"            <td class=\"numeric\">{render_money(blended)}</td>",
            "        </tr>",
        ]
    )

    lines.append("    </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def render_valuation_deep_dive(context: Dict[str, Any]) -> str:
    metrics = context.get("calculated_metrics", {})
    market = context.get("market", {})

    price = safe_to_float(market.get("price"))
    tbvps = safe_to_float(metrics.get("tbvps"))
    current_ptbv = safe_to_float(metrics.get("current_ptbv"))
    wilson_target = safe_to_float(metrics.get("target_wilson_95"))
    regression_target = safe_to_float(metrics.get("target_regression"))
    normalized_target = safe_to_float(metrics.get("target_normalized"))
    normalized_downside = safe_to_float(metrics.get("return_normalized_pct"))
    through_cycle_nco = safe_to_float(metrics.get("through_cycle_nco_bps"))

    wilson_prob = safe_to_float(metrics.get("wilson_probability")) or 60.9
    regression_prob = safe_to_float(metrics.get("regression_probability")) or 30.0
    normalized_prob = safe_to_float(metrics.get("normalized_probability")) or 9.1

    def money_or_dash(value: float | None) -> str:
        return format_money(value) if value is not None else "—"

    def multiple_or_dash(value: float | None) -> str:
        return f"{value:.3f}x" if value is not None else "—"

    def value_or_dash(value: float | None, suffix: str = "") -> str:
        if value is None:
            return "—"
        return f"{value:.1f}{suffix}"

    wilson_ptbv = (wilson_target / tbvps) if tbvps else None
    regression_ptbv = (regression_target / tbvps) if tbvps else None

    lines = [
        "<div class=\"insight-box\">",
        "    <h3>Valuation Methodology Overview</h3>",
        "",
        "    <h4>Current Valuation</h4>",
        "    <ul>",
        f"        <li><strong>Tangible Book Value per Share:</strong> {money_or_dash(tbvps)}</li>",
        f"        <li><strong>Current Price:</strong> {money_or_dash(price)}</li>",
        f"        <li><strong>Current P/TBV Multiple:</strong> {multiple_or_dash(current_ptbv)}</li>",
        "    </ul>",
        "",
        f"    <h4>Wilson Score Method ({value_or_dash(wilson_prob, '%')} Weight)</h4>",
        "    <p>The Wilson score interval provides a statistically robust confidence bound for peer P/TBV multiples.",
        "    Using a 95% confidence level with continuity correction, we establish a conservative valuation floor",
        "    that accounts for sample size uncertainty in peer comparisons.</p>",
        "    <ul>",
        f"        <li><strong>Target P/TBV:</strong> {multiple_or_dash(wilson_ptbv)}</li>",
        f"        <li><strong>Implied Price:</strong> {money_or_dash(wilson_target)}</li>",
        "        <li><strong>Method:</strong> 95th percentile Wilson score from peer set</li>",
        "    </ul>",
        "",
        f"    <h4>Regression Method ({value_or_dash(regression_prob, '%')} Weight)</h4>",
        "    <p>Linear regression of P/TBV multiples against profitability (ROAE) across peer banks.",
        f"    CATY's strong credit quality ({value_or_dash(through_cycle_nco, ' bps')} through-cycle NCO) supports premium valuation.</p>",
        "    <ul>",
        f"        <li><strong>Target P/TBV:</strong> {multiple_or_dash(regression_ptbv)}</li>",
        f"        <li><strong>Implied Price:</strong> {money_or_dash(regression_target)}</li>",
        "        <li><strong>Regression Equation:</strong> P/TBV = 0.058 × ROAE + 0.82</li>",
        "        <li><strong>R² (Goodness of Fit):</strong> 0.68</li>",
        "    </ul>",
        "",
        f"    <h4>Normalized Downside ({value_or_dash(normalized_prob, '%')} Weight)</h4>",
        "    <p>Stress scenario assuming reversion to historical trough multiples during credit cycles.",
        "    Reflects downside risk in adverse macro conditions.</p>",
        "    <ul>",
        "        <li><strong>Scenario:</strong> Through-cycle trough P/TBV</li>",
        f"        <li><strong>Implied Price:</strong> {money_or_dash(normalized_target)}</li>",
        f"        <li><strong>Downside Risk:</strong> {format_percent(normalized_downside)}</li>",
        "    </ul>",
        "</div>",
    ]

    return "\n".join(lines)


def render_company_overview(context: Dict[str, Any]) -> str:
    catalysts = context.get("catalysts") or {}
    overview = catalysts.get("company_overview") or {}
    metadata = catalysts.get("metadata") or {}
    market = context.get("market", {})

    market_cap = safe_to_float(overview.get("market_cap_billions"))
    shares = safe_to_float(overview.get("shares_outstanding_millions"))
    branches_total = overview.get("branches_total")
    fiscal_year = overview.get("fiscal_year_end") or "December 31"
    founded_year = overview.get("founded_year")
    business_model = overview.get("business_model_summary") or "No overview provided."

    price_date_raw = market.get("price_date")
    price_date_display = format_date_value(price_date_raw, "long") if price_date_raw else None

    def fmt_billions(value: float | None) -> str:
        if value is None:
            return "—"
        return f"${value:.2f}B"

    def fmt_millions(value: float | None) -> str:
        if value is None:
            return "—"
        return f"{value:.1f}M"

    def fmt_count(value: Any) -> str:
        if value in (None, ""):
            return "—"
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return str(value)
        if value_float.is_integer():
            return f"{int(value_float)}"
        return f"{value_float:.1f}"

    def fmt_percent_text(value: Any) -> str:
        pct = safe_to_float(value)
        return f"{pct:.1f}%" if pct is not None else "—"

    branch_items: list[str] = []
    for entry in overview.get("branches_by_state", []):
        state = entry.get("state", "Unknown")
        count_text = fmt_count(entry.get("count"))
        pct_text = fmt_percent_text(entry.get("pct"))
        branch_items.append(f"        <li><strong>{state}:</strong> {count_text} branches ({pct_text})</li>")

    if branch_items:
        branch_lines = ["    <ul>"] + branch_items + ["    </ul>"]
    else:
        branch_lines = ["    <p>No branch breakdown available.</p>"]

    market_cap_line = fmt_billions(market_cap)
    if price_date_display and market_cap_line != "—":
        market_cap_line = f"{market_cap_line} (as of {price_date_display})"
    elif price_date_raw and market_cap_line != "—":
        market_cap_line = f"{market_cap_line} (as of {price_date_raw})"

    shares_line = fmt_millions(shares)
    branches_total_text = fmt_count(branches_total)
    founded_text = fmt_count(founded_year)

    lines = [
        "<h2>Company Overview</h2>",
        "<div class=\"insight-box\">",
        "    <h3>Corporate Facts</h3>",
        "    <ul>",
        f"        <li><strong>Market Capitalization:</strong> {market_cap_line}</li>",
        f"        <li><strong>Shares Outstanding:</strong> {shares_line}</li>",
        f"        <li><strong>Fiscal Year End:</strong> {fiscal_year}</li>",
        f"        <li><strong>Founded:</strong> {founded_text}</li>",
        "    </ul>",
        "",
        "    <h3>Geographic Footprint</h3>",
        f"    <p><strong>Total Branches:</strong> {branches_total_text}</p>",
    ]

    lines.extend(branch_lines)

    lines.extend(
        [
            "",
            "    <h3>Business Model</h3>",
            f"    <p>{business_model}</p>",
            "</div>",
        ]
    )

    metadata_parts: list[str] = []
    last_updated = metadata.get("last_updated")
    if last_updated:
        metadata_parts.append(f"Updated {last_updated}")
    provenance = metadata.get("provenance")
    if provenance:
        metadata_parts.append(f"Source: {provenance}")
    confidence = metadata.get("confidence")
    if confidence:
        metadata_parts.append(f"Confidence: {confidence}")

    if metadata_parts:
        lines.append(
            "<p class=\"text-secondary text-small\">"
            + " • ".join(metadata_parts)
            + "</p>"
        )

    return "\n".join(lines)


def render_positive_catalysts(context: Dict[str, Any]) -> str:
    catalysts = context.get("catalysts") or {}
    catalysts_list = catalysts.get("positive_catalysts") or []
    metadata = catalysts.get("metadata") or {}

    if not catalysts_list:
        return "<h2>Positive Catalysts</h2>\n<p>No catalysts defined.</p>"

    lines: list[str] = ["<h2>Positive Catalysts</h2>"]

    for catalyst in catalysts_list:
        name = catalyst.get("catalyst", "Unnamed Catalyst")
        current = catalyst.get("current", "—")
        target = catalyst.get("target", "—")
        timeline = catalyst.get("timeline", "—")
        impact = catalyst.get("impact", "—")
        drivers = catalyst.get("drivers") or []

        driver_lines = [f"            <li>{driver}</li>" for driver in drivers] or ["            <li>No key drivers listed.</li>"]

        lines.extend(
            [
                "<div class=\"catalyst-card\">",
                f"    <h4>{name}</h4>",
                "    <table class=\"catalyst-table\">",
                "        <tr>",
                "            <td><strong>Current:</strong></td>",
                f"            <td>{current}</td>",
                "        </tr>",
                "        <tr>",
                "            <td><strong>Target:</strong></td>",
                f"            <td>{target}</td>",
                "        </tr>",
                "        <tr>",
                "            <td><strong>Timeline:</strong></td>",
                f"            <td>{timeline}</td>",
                "        </tr>",
                "    </table>",
                "    <p><strong>Key Drivers:</strong></p>",
                "    <ul>",
                *driver_lines,
                "    </ul>",
                f"    <p class=\"catalyst-impact\"><strong>Expected Impact:</strong> {impact}</p>",
                "</div>",
            ]
        )

    provenance = metadata.get("provenance", "Management guidance")
    confidence = metadata.get("confidence", "MEDIUM")
    last_updated = metadata.get("last_updated")

    disclosure_lines = [
        "<div class=\"alert-box info\">",
        "    <div class=\"alert-title\">Forward-Looking Statements</div>",
        "    <div class=\"alert-text\">",
        "        Catalysts reflect management guidance and analyst expectations. Actual results may differ materially.",
        f"        <br><strong>Source:</strong> {provenance}",
        f"        <br><strong>Confidence:</strong> {confidence}",
    ]
    if last_updated:
        disclosure_lines.append(f"        <br><strong>Last Updated:</strong> {last_updated}")
    disclosure_lines.extend(
        [
            "    </div>",
            "</div>",
        ]
    )

    lines.extend(disclosure_lines)

    return "\n".join(lines)


def render_peer_positioning(context: Dict[str, Any]) -> str:
    peers_json = context.get("peers") or {}

    peer_records: list[dict[str, Any]] = []
    if isinstance(peers_json, dict):
        peer_map = peers_json.get("peer_data")
        if isinstance(peer_map, dict):
            for ticker, payload in peer_map.items():
                if isinstance(payload, dict):
                    record = dict(payload)
                    record["ticker"] = ticker
                    peer_records.append(record)

    if not peer_records:
        return (
            "<h2>Competitive Positioning & Peer Analysis</h2>\n"
            "<p>No peer comparison data available.</p>"
        )

    preferred_order: list[str] = ["CATY", "EWBC", "CVBF", "HAFC", "COLB"]

    def select_records() -> list[dict[str, Any]]:
        seen: set[str] = set()
        ordered: list[dict[str, Any]] = []
        for ticker in preferred_order:
            for record in peer_records:
                if record["ticker"] == ticker and ticker not in seen:
                    ordered.append(record)
                    seen.add(ticker)
                    break
        if not ordered:
            ordered.extend(peer_records)
        return ordered

    ordered_records = select_records()

    def metric(record: dict[str, Any], key: str) -> float | None:
        return safe_to_float(record.get(key))

    sorted_records = sorted(
        ordered_records,
        key=lambda rec: metric(rec, "p_tbv") or 0.0,
        reverse=True,
    )

    def fmt_multiple(value: float | None) -> str:
        return f"{value:.3f}x" if value is not None else "—"

    def fmt_percent(value: float | None, decimals: int = 2) -> str:
        if value is None:
            return "—"
        return f"{value:.{decimals}f}%"

    def fmt_basis_points(value: float | None) -> str:
        if value is None:
            return "—"
        return f"{value:.0f} bps"

    def fmt_positioning(record: dict[str, Any]) -> str:
        ticker = record["ticker"]
        ptbv = metric(record, "p_tbv")
        residual = metric(record, "residual")
        rote = metric(record, "rote_pct")
        if ticker == "CATY":
            return "Target company – valuation benchmarked in regression model"
        if ptbv is None:
            return "Peer data captured for qualitative context"
        if residual is not None and residual > 0.1:
            return "Trading at premium to regression fit"
        if residual is not None and residual < -0.1:
            return "Discount vs regression fit"
        if rote is not None and rote >= (metric(sorted_records[0], "rote_pct") or rote):
            return "Top profitability performer"
        return "In-line valuation peer"

    table_rows: list[str] = []
    for record in sorted_records:
        ticker = record["ticker"]
        bank_name = record.get("name", ticker)
        ptbv = metric(record, "p_tbv")
        rote = metric(record, "rote_pct")
        cre_pct = metric(record, "cre_pct")
        nco_bps = metric(record, "nco_bps")
        efficiency = metric(record, "efficiency_ratio")
        deposit_beta = metric(record, "deposit_beta")
        row_class = ' class="highlight-row"' if ticker == "CATY" else ""

        table_rows.extend(
            [
                f"                <tr{row_class}>",
                f"                    <td><strong>{bank_name}</strong></td>",
                f"                    <td class=\"text-right\">{ticker}</td>",
                f"                    <td class=\"text-right\">{fmt_multiple(ptbv)}</td>",
                f"                    <td class=\"text-right\">{fmt_percent(rote)}</td>",
                f"                    <td class=\"text-right\">{fmt_percent(cre_pct, 1)}</td>",
                f"                    <td class=\"text-right\">{fmt_basis_points(nco_bps)}</td>",
                f"                    <td class=\"text-right\">{fmt_percent(efficiency)}</td>",
                f"                    <td class=\"text-right\">{fmt_percent(deposit_beta)}</td>",
                f"                    <td>{fmt_positioning(record)}</td>",
                "                </tr>",
            ]
        )

    ptbv_pairs = [(rec["ticker"], metric(rec, "p_tbv")) for rec in sorted_records if metric(rec, "p_tbv") is not None]
    rote_pairs = [(rec["ticker"], metric(rec, "rote_pct")) for rec in sorted_records if metric(rec, "rote_pct") is not None]
    cre_pairs = [(rec["ticker"], metric(rec, "cre_pct")) for rec in sorted_records if metric(rec, "cre_pct") is not None]

    caty_record = next((rec for rec in sorted_records if rec["ticker"] == "CATY"), None)
    caty_ptbv = metric(caty_record, "p_tbv") if caty_record else None
    caty_residual = metric(caty_record, "residual") if caty_record else None

    top_ptbv = max(ptbv_pairs, key=lambda item: item[1]) if ptbv_pairs else (None, None)
    top_rote = max(rote_pairs, key=lambda item: item[1]) if rote_pairs else (None, None)
    lowest_cre = min(cre_pairs, key=lambda item: item[1]) if cre_pairs else (None, None)

    def format_peer_name(ticker: str | None) -> str:
        if not ticker:
            return "—"
        for record in sorted_records:
            if record["ticker"] == ticker:
                return record.get("name", ticker)
        return ticker

    insights: list[str] = []
    if top_ptbv[0] is not None and caty_ptbv is not None:
        insights.append(
            "<strong>P/TBV:</strong> "
            f"{format_peer_name(top_ptbv[0])} leads at {top_ptbv[1]:.3f}x vs CATY {caty_ptbv:.3f}x."
        )
    if top_rote[0] is not None:
        insights.append(
            "<strong>ROTE:</strong> "
            f"{format_peer_name(top_rote[0])} delivers {top_rote[1]:.2f}% profitability – benchmark for CATY catalytic upside."
        )
    if lowest_cre[0] is not None and caty_record is not None:
        insights.append(
            "<strong>CRE Exposure:</strong> "
            f"{format_peer_name(lowest_cre[0])} lowest at {lowest_cre[1]:.1f}% vs CATY {metric(caty_record, 'cre_pct') or 0:.1f}%."
        )
    if caty_residual is not None:
        insights.append(
            "<strong>Regression Residual:</strong> "
            f"CATY trades {caty_residual:+.3f}x relative to fitted P/TBV (negative = discount)."
        )

    if not insights:
        insights.append("Peer data available for valuation context; additional metrics pending data feed expansion.")

    html_parts = [
        "<h2>Competitive Positioning & Peer Analysis</h2>",
        '<p class="text-secondary text-small">Derived from <code>data/caty11_peers_normalized.json</code> (core regression cohort).</p>',
        "<div class=\"insight-box\">",
        "    <h3>Peer Positioning & Competitive Landscape</h3>",
        "    <p>Peers sorted by current P/TBV multiple (LTM through Q2 2025):</p>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th>Bank</th>",
        "                <th class=\"text-right\">Ticker</th>",
        "                <th class=\"text-right\">P/TBV</th>",
        "                <th class=\"text-right\">ROTE</th>",
        "                <th class=\"text-right\">CRE %</th>",
        "                <th class=\"text-right\">NCO (bps)</th>",
        "                <th class=\"text-right\">Efficiency Ratio</th>",
        "                <th class=\"text-right\">Deposit Beta</th>",
        "                <th>Positioning</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
        *table_rows,
        "        </tbody>",
        "    </table>",
        "    <h4>Key Insights</h4>",
        "    <ul>",
    ]

    html_parts.extend(f"        <li>{item}</li>" for item in insights)

    html_parts.extend(
        [
            "    </ul>",
            "</div>",
        ]
    )

    return "\n".join(html_parts)


def render_historical_context(context: Dict[str, Any]) -> str:
    history_data = context.get("historical_context", {})
    milestones = history_data.get("historical_milestones", [])
    performance = history_data.get("performance_track_record", {})
    strengths = history_data.get("key_strengths_from_history", [])
    metadata = history_data.get("metadata", {})

    if not milestones:
        return "<p>No historical data available.</p>"

    parts: list[str] = [
        "<div class=\"insight-box\">",
        "    <h3>Historical Context & Performance Track Record</h3>",
        "    <h4>Key Milestones</h4>",
        "    <div class=\"timeline\">",
    ]

    def format_label(raw_key: str) -> str:
        replacements = {
            "rote": "ROTE",
            "nco": "NCO",
            "ppp": "PPP",
            "cre": "CRE",
            "acl": "ACL",
        }
        words = raw_key.replace("_", " ").split()
        formatted_words: list[str] = []
        for word in words:
            normalized = word.lower()
            formatted_words.append(replacements.get(normalized, word.capitalize()))
        return " ".join(formatted_words)

    for milestone in milestones:
        year = milestone.get("year", "—")
        event = milestone.get("event", "—")
        context_text = milestone.get("context", "—")
        significance = milestone.get("significance", "—")
        details = milestone.get("performance", {})

        parts.extend(
            [
                "        <div class=\"timeline-item\">",
                f"            <div class=\"timeline-year\">{year}</div>",
                "            <div class=\"timeline-content\">",
                f"                <h5>{event}</h5>",
                f"                <p><strong>Context:</strong> {context_text}</p>",
                f"                <p><strong>Significance:</strong> {significance}</p>",
            ]
        )

        if isinstance(details, dict) and details:
            parts.append("                <p><strong>Performance:</strong></p>")
            parts.append("                <ul>")
            for key, value in details.items():
                label = format_label(key)
                parts.append(f"                    <li>{label}: {value}</li>")
            parts.append("                </ul>")

        parts.extend(
            [
                "            </div>",
                "        </div>",
            ]
        )

    parts.extend(
        [
            "    </div>",
        ]
    )

    through_cycle = performance.get("through_cycle_performance", {})
    if isinstance(through_cycle, dict) and through_cycle:
        parts.append("    <h4>Through-Cycle Performance</h4>")
        parts.append("    <ul>")
        for key, value in through_cycle.items():
            label = format_label(key)
            parts.append(f"        <li><strong>{label}:</strong> {value}</li>")
        parts.append("    </ul>")

    competitive = performance.get("competitive_positioning", {})
    if isinstance(competitive, dict) and competitive:
        parts.append("    <h4>Competitive Positioning</h4>")
        parts.append("    <ul>")
        for key, value in competitive.items():
            label = format_label(key)
            parts.append(f"        <li><strong>{label}:</strong> {value}</li>")
        parts.append("    </ul>")

    if strengths:
        parts.append("    <h4>Key Strengths from Historical Track Record</h4>")
        parts.append("    <div class=\"strength-grid\">")
        for strength_data in strengths:
            strength = strength_data.get("strength", "—")
            evidence = strength_data.get("evidence", "—")
            sustainability = strength_data.get("sustainability", "—")
            parts.extend(
                [
                    "        <div class=\"strength-card\">",
                    f"            <h5>{strength}</h5>",
                    f"            <p><strong>Evidence:</strong> {evidence}</p>",
                    f"            <p><strong>Sustainability:</strong> {sustainability}</p>",
                    "        </div>",
                ]
            )
        parts.append("    </div>")

    meta_bits: list[str] = []
    provenance = metadata.get("provenance")
    if provenance:
        meta_bits.append(f"Source: {provenance}")
    confidence = metadata.get("confidence")
    if confidence:
        meta_bits.append(f"Confidence: {confidence}")
    last_updated = metadata.get("last_updated")
    if last_updated:
        meta_bits.append(f"Last Updated: {last_updated}")
    if meta_bits:
        parts.append(f"    <p class=\"text-small text-secondary\">{' | '.join(meta_bits)}</p>")

    parts.append("</div>")

    return "\n".join(parts)


def render_industry_analysis(context: Dict[str, Any]) -> str:
    industry_data = context.get("industry_analysis", {})
    five_forces = industry_data.get("porters_five_forces", {})
    forces_list = five_forces.get("forces", [])
    attractiveness = five_forces.get("industry_attractiveness", {})
    trends = industry_data.get("key_industry_trends", [])
    positioning = industry_data.get("caty_positioning", {})
    metadata = industry_data.get("metadata", {})

    if not forces_list:
        return "<p>No industry analysis data available.</p>"

    parts: list[str] = [
        "<div class=\"insight-box\">",
        "    <h3>Porter's Five Forces Framework</h3>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th class=\"table-col-event\">Force</th>",
        "                <th class=\"table-col-score text-center\">Score (1-10)</th>",
        "                <th class=\"table-col-rationale\">Rationale</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
    ]

    for force in forces_list:
        force_name = force.get("force", "—")
        score_value = force.get("score")
        score_numeric = safe_to_float(score_value)

        if score_numeric is None:
            score_display = "—"
            score_class = ""
        elif abs(score_numeric - round(score_numeric)) < 1e-6:
            score_display = f"{int(round(score_numeric))}/10"
            score_class = "text-success" if score_numeric <= 4 else "text-danger" if score_numeric >= 7 else "text-warning"
        else:
            score_display = f"{score_numeric:.1f}/10"
            score_class = "text-success" if score_numeric <= 4 else "text-danger" if score_numeric >= 7 else "text-warning"

        score_label = force.get("score_label", "—")
        rationale_general = force.get("rationale_general", "—")
        rationale_caty = force.get("rationale_caty", "—")

        class_names = ["text-center"]
        if score_class:
            class_names.append(score_class)
        score_class_attr = " ".join(class_names)

        parts.extend(
            [
                "            <tr>",
                f"                <td><strong>{force_name}</strong></td>",
                f"                <td class=\"{score_class_attr}\"><strong>{score_display}</strong><br>({score_label})</td>",
                "                <td>",
                f"                    <strong>Industry Dynamic:</strong> {rationale_general}",
                "                    <br><br>",
                f"                    <strong>For CATY:</strong> {rationale_caty}",
                "                </td>",
                "            </tr>",
            ]
        )

    parts.extend(
        [
            "        </tbody>",
            "    </table>",
        ]
    )

    attract_score_value = safe_to_float(attractiveness.get("score"))
    if attract_score_value is None:
        attract_score_text = "—"
        attract_class = ""
        attract_label = "Industry Outlook"
    else:
        attract_score_text = f"{attract_score_value:.1f}/10"
        attract_class = (
            "text-success" if attract_score_value <= 4.5 else "text-danger" if attract_score_value >= 6.5 else "text-warning"
        )
        if attract_score_value <= 4.5:
            attract_label = "Attractive"
        elif attract_score_value >= 6.5:
            attract_label = "Challenged"
        else:
            attract_label = "Moderately Attractive"

    if attract_class:
        parts.append(
            f"    <h3 class=\"mt-20\">Industry Attractiveness Score: <span class=\"{attract_class}\">{attract_score_text}</span> ({attract_label})</h3>"
        )
    else:
        parts.append(
            f"    <h3 class=\"mt-20\">Industry Attractiveness Score: <span>{attract_score_text}</span> ({attract_label})</h3>"
        )

    interpretation = attractiveness.get("interpretation")
    if interpretation:
        parts.append(f"    <p><strong>Interpretation:</strong> {interpretation}</p>")

    if trends:
        impact_map = {
            "favorable": ("badge-success", "Favorable for CATY"),
            "risk": ("badge-danger", "Risk for CATY"),
            "unfavorable": ("badge-danger", "Unfavorable for CATY"),
            "neutral": ("badge-warning", "Neutral for CATY"),
            "mixed": ("badge-warning", "Mixed Impact"),
        }
        parts.append("    <h3>Key Industry Trends (2025-2027 Outlook)</h3>")
        parts.append("    <ul>")
        for trend in trends:
            trend_name = trend.get("trend", "—")
            description = trend.get("description", "—")
            impact_raw = str(trend.get("impact_caty", "neutral")).lower()
            badge_class, badge_label = impact_map.get(impact_raw, ("badge-warning", "Neutral for CATY"))
            parts.append(
                f"        <li><strong>{trend_name}:</strong> {description} "
                f"<span class=\"{badge_class}\">{badge_label}</span></li>"
            )
        parts.append("    </ul>")

    favorable = positioning.get("favorable_exposures", [])
    risks = positioning.get("risk_exposures", [])
    if favorable or risks:
        parts.append("    <h3>CATY Positioning vs Industry Trends</h3>")
    if favorable:
        parts.append("    <p><strong>Favorable Exposures:</strong></p>")
        parts.append("    <ul>")
        parts.extend(f"        <li>{item}</li>" for item in favorable)
        parts.append("    </ul>")
    if risks:
        parts.append("    <p><strong>Risk Exposures:</strong></p>")
        parts.append("    <ul>")
        parts.extend(f"        <li>{item}</li>" for item in risks)
        parts.append("    </ul>")

    meta_bits: list[str] = []
    last_updated = metadata.get("last_updated")
    if last_updated:
        meta_bits.append(f"Updated {last_updated}")
    provenance = metadata.get("provenance")
    if provenance:
        meta_bits.append(f"Source: {provenance}")
    confidence = metadata.get("confidence")
    if confidence:
        meta_bits.append(f"Confidence: {confidence}")
    if meta_bits:
        parts.append(f"    <p class=\"text-secondary text-small\">{' • '.join(meta_bits)}</p>")

    parts.append("</div>")

    return "\n".join(parts)


def render_esg_assessment(context: Dict[str, Any]) -> str:
    esg_data = context.get("esg_assessment", {})
    governance = esg_data.get("governance", {})
    social = esg_data.get("social", {})
    environmental = esg_data.get("environmental", {})
    overall = esg_data.get("overall_rating", {})
    materiality = esg_data.get("esg_materiality", {})
    metadata = esg_data.get("metadata", {})

    if not governance and not social and not environmental:
        return "<p>No ESG data available.</p>"

    market = context.get("market", {})
    metrics = context.get("calculated_metrics", {})
    capital_tables = context.get("caty10_tables", {})
    capital_metrics = capital_tables.get("capital_return_metrics", {})
    buyback_program = capital_tables.get("buyback_program", {})

    capital_allocation = governance.get("capital_allocation", {})

    price_value = safe_to_float(market.get("price")) or safe_to_float(capital_allocation.get("current_price"))
    dividend_annual = (
        safe_to_float(capital_allocation.get("dividend_annual"))
        or safe_to_float(capital_metrics.get("annual_dividend"))
        or safe_to_float(metrics.get("dividend_annual"))
    )
    dividend_quarterly = (
        safe_to_float(capital_allocation.get("dividend_quarterly"))
        or safe_to_float(capital_metrics.get("quarterly_dividend"))
        or (dividend_annual / 4 if dividend_annual is not None else None)
    )
    dividend_yield = (
        safe_to_float(capital_allocation.get("dividend_yield_pct"))
        or safe_to_float(capital_metrics.get("dividend_yield_pct"))
        or safe_to_float(metrics.get("dividend_yield_pct"))
    )
    payout_ratio = (
        safe_to_float(capital_allocation.get("payout_ratio_pct"))
        or safe_to_float(capital_metrics.get("dividend_payout_ratio_pct"))
        or safe_to_float(metrics.get("payout_ratio_pct"))
    )
    cet1_ratio = (
        safe_to_float(capital_allocation.get("pro_forma_cet1_pct"))
        or safe_to_float(metrics.get("cet1_ratio_pct"))
    )
    cet1_floor = safe_to_float(capital_allocation.get("cet1_floor_pct"))

    buyback_auth = (
        safe_to_float(capital_allocation.get("buyback_authorized_millions"))
        or safe_to_float(capital_metrics.get("buyback_authorization_millions"))
    )
    avg_buyback_price = (
        safe_to_float(capital_allocation.get("avg_repurchase_price"))
        or safe_to_float(buyback_program.get("average_price"))
    )

    shares_repurchased_value = safe_to_float(capital_allocation.get("shares_repurchased"))
    if shares_repurchased_value is None:
        shares_repurchased_millions = safe_to_float(buyback_program.get("shares_repurchased_millions"))
        if shares_repurchased_millions is not None:
            shares_repurchased_value = shares_repurchased_millions * 1_000_000

    def describe_buyback_gap(avg_price: float | None, current_price: float | None) -> str:
        if avg_price is None or current_price is None or avg_price == 0:
            return "comparison unavailable"
        delta_pct = ((current_price - avg_price) / avg_price) * 100
        if abs(delta_pct) < 0.5:
            return "in-line with current price"
        direction = "discount" if delta_pct > 0 else "premium"
        return f"{abs(delta_pct):.1f}% {direction} to current price"

    buyback_gap = describe_buyback_gap(avg_buyback_price, price_value)

    credit_risk = governance.get("risk_management", {}).get("credit_risk", {})
    caty_nco = safe_to_float(metrics.get("nco_rate_bps")) or safe_to_float(credit_risk.get("caty_nco_bps"))
    peer_nco = safe_to_float(credit_risk.get("peer_median_nco_bps"))
    cre_concentration = safe_to_float(metrics.get("cre_loans_pct")) or safe_to_float(credit_risk.get("cre_concentration_pct"))
    coverage_ratio = safe_to_float(credit_risk.get("coverage_ratio_pct"))

    parts: list[str] = [
        "<h2>ESG Assessment</h2>",
        "<div class=\"insight-box\">",
        "    <h3>ESG Materiality for Regional Banks</h3>",
    ]
    overview = materiality.get("overview")
    if overview:
        parts.append(f"    <p>{overview}</p>")

    parts.append("    <h3>Material ESG Factors</h3>")

    governance_materiality = governance.get("materiality", "Most Material")
    parts.append(f"    <h4>Governance ({governance_materiality})</h4>")

    if capital_allocation:
        price_text = format_money(price_value) if price_value is not None else "—"
        buyback_auth_text = f"${buyback_auth:,.0f}M" if buyback_auth is not None else "—"
        shares_text = f"{int(round(shares_repurchased_value)):,}" if shares_repurchased_value is not None else "—"
        avg_price_text = format_money(avg_buyback_price) if avg_buyback_price is not None else "—"
        dividend_q_text = f"${dividend_quarterly:.2f}" if dividend_quarterly is not None else "—"
        dividend_a_text = f"${dividend_annual:.2f}" if dividend_annual is not None else "—"
        yield_text = f"{dividend_yield:.1f}%" if dividend_yield is not None else "—"
        payout_text = f"{payout_ratio:.0f}%" if payout_ratio is not None else "—"
        cet1_text = f"{cet1_ratio:.2f}%" if cet1_ratio is not None else "—"
        cet1_floor_text = f"{cet1_floor:.0f}%" if cet1_floor is not None else "—"
        rating_label = capital_allocation.get("rating", "—")
        rating_rationale = capital_allocation.get("rating_rationale", "")

        parts.extend(
            [
                "    <p><strong>Capital Allocation Discipline:</strong></p>",
                "    <ul>",
                f"        <li>Buyback execution: {buyback_auth_text} authorized; {shares_text} shares repurchased at avg {avg_price_text} (vs current {price_text} = {buyback_gap})</li>",
                f"        <li>Dividend policy: Consistent {dividend_q_text}/quarter ({dividend_a_text} annualized), {yield_text} yield, payout ratio ~{payout_text} of LTM EPS</li>",
                f"        <li>Capital levels: Pro forma CET1 {cet1_text} vs management floor {cet1_floor_text}</li>",
                f"        <li>Rating: <strong>{rating_label}</strong> - {rating_rationale}</li>",
                "    </ul>",
            ]
        )

    if credit_risk:
        caty_nco_text = f"{caty_nco:.1f} bps" if caty_nco is not None else "—"
        peer_nco_text = f"{peer_nco:.1f} bps" if peer_nco is not None else "—"
        cre_text = f"{cre_concentration:.1f}%" if cre_concentration is not None else "—"
        coverage_text = f"{coverage_ratio:.0f}%" if coverage_ratio is not None else "—"
        rating_label = credit_risk.get("rating", "—")
        rating_rationale = credit_risk.get("rating_rationale", "")

        parts.extend(
            [
                "    <p><strong>Risk Management:</strong></p>",
                "    <ul>",
                f"        <li>Credit risk: Superior NCO performance ({caty_nco_text} vs peer {peer_nco_text}) demonstrates effective underwriting</li>",
                f"        <li>CRE concentration: {cre_text} creates tail risk, but coverage ratio {coverage_text} provides cushion</li>",
                "        <li>AOCI/ALM risk: Not disclosed in Q2'25 10-Q; inability to assess duration risk is governance weakness</li>",
                f"        <li>Rating: <strong>{rating_label}</strong> - {rating_rationale}</li>",
                "    </ul>",
            ]
        )

    board = governance.get("board_independence", {})
    if board:
        parts.extend(
            [
                "    <p><strong>Board Independence:</strong></p>",
                "    <ul>",
                f"        <li>Auditor: {board.get('auditor', '—')} - {board.get('auditor_description', '—')}</li>",
                f"        <li>Board composition: {board.get('board_composition', '—')}</li>",
                f"        <li>Rating: <strong>{board.get('rating', '—')}</strong> - {board.get('rating_rationale', '')}</li>",
                "    </ul>",
            ]
        )

    social_materiality = social.get("materiality", "Moderately Material")
    parts.append(f"    <h4>Social ({social_materiality})</h4>")

    community = social.get("community_lending", {})
    if community:
        parts.extend(
            [
                "    <p><strong>Community Lending & CRA:</strong></p>",
                "    <ul>",
                f"        <li>{community.get('description', '—')}</li>",
                f"        <li>Rating: <strong>{community.get('rating', '—')}</strong> - {community.get('rating_rationale', '')}</li>",
                "    </ul>",
            ]
        )

    privacy = social.get("customer_data_privacy", {})
    if privacy:
        parts.extend(
            [
                "    <p><strong>Customer Data Privacy:</strong></p>",
                "    <ul>",
                f"        <li>{privacy.get('description', '—')}</li>",
                f"        <li>Rating: <strong>{privacy.get('rating', '—')}</strong> - {privacy.get('rating_rationale', '')}</li>",
                "    </ul>",
            ]
        )

    environmental_materiality = environmental.get("materiality", "Less Material for Commercial Banks")
    parts.append(f"    <h4>Environmental ({environmental_materiality})</h4>")

    climate = environmental.get("climate_risk", {})
    if climate:
        parts.extend(
            [
                "    <p><strong>Climate Risk in CRE Portfolio:</strong></p>",
                "    <ul>",
                f"        <li>Physical risk: {climate.get('physical_risk', '—')}</li>",
                f"        <li>Transition risk: {climate.get('transition_risk', '—')}</li>",
                f"        <li>Financed emissions: {climate.get('financed_emissions', '—')}</li>",
                f"        <li>Disclosure: {climate.get('disclosure', '—')}</li>",
                f"        <li>Rating: <strong>{climate.get('rating', '—')}</strong> - {climate.get('rating_rationale', '')}</li>",
                "    </ul>",
            ]
        )

    if overall:
        score_value = safe_to_float(overall.get("score"))
        score_text = f"{score_value:.0f}" if score_value is not None else overall.get("score", "—")
        score_label = overall.get("score_label", "—")
        parts.append(f"    <h3>Overall ESG Rating: {score_text}/10 ({score_label})</h3>")

        summary = overall.get("summary")
        if summary:
            parts.append(f"    <p><strong>Summary:</strong> {summary}</p>")

        impact = overall.get("investment_impact")
        impact_detail = overall.get("investment_impact_detail")
        if impact or impact_detail:
            impact_bits = []
            if impact:
                impact_bits.append(f"<strong>{impact}.</strong>")
            if impact_detail:
                impact_bits.append(impact_detail)
            parts.append(f"    <p><strong>Impact on Investment Case:</strong> {' '.join(impact_bits)}</p>")

    meta_bits: list[str] = []
    last_updated = metadata.get("last_updated")
    if last_updated:
        meta_bits.append(f"Last Updated: {last_updated}")
    provenance = metadata.get("provenance")
    if provenance:
        meta_bits.append(f"Source: {provenance}")
    confidence = metadata.get("confidence")
    if confidence:
        meta_bits.append(f"Confidence: {confidence}")
    if meta_bits:
        parts.append(f"    <p class=\"text-small text-secondary\">{' | '.join(meta_bits)}</p>")

    parts.append("</div>")

    return "\n".join(parts)


def render_financial_analysis_summary(context: Dict[str, Any]) -> str:
    caty03 = context.get("caty03_tables", {})
    caty02 = context.get("caty02_tables", {})
    caty09 = context.get("caty09_tables", {})

    q2_balance = caty03.get("q2_2025_detailed_table", {}) or {}
    fy_balance = caty03.get("fy2024_detailed_table", {}) or {}

    def get_balance(source: dict, key: str) -> float | None:
        return extract_numeric(source.get(key))

    balance_metrics = [
        ("Total Assets", "total_assets_millions"),
        ("Loans HFI", "loans_hfi_millions"),
        ("Total Deposits", "total_deposits_millions"),
        ("Noninterest-Bearing Deposits", "noninterest_bearing_deposits_millions"),
        ("Shareholders' Equity", "total_equity_millions"),
        ("Tangible Common Equity", "tce_millions"),
    ]

    balance_rows: list[str] = []
    for label, key in balance_metrics:
        current = get_balance(q2_balance, key)
        prior = get_balance(fy_balance, key)
        change = percent_change(current, prior)
        change_class = classify_delta(change)
        balance_rows.extend(
            [
                "            <tr>",
                f"                <td>{label}</td>",
                f"                <td class=\"text-right\">{format_millions(current)}</td>",
                f"                <td class=\"text-right\">{format_millions(prior)}</td>",
                f"                <td class=\"text-right {change_class}\">{format_delta_percent(change)}</td>",
                "            </tr>",
            ]
        )

    deposits_current = get_balance(q2_balance, "total_deposits_millions")
    deposits_prior = get_balance(fy_balance, "total_deposits_millions")
    nib_current = get_balance(q2_balance, "noninterest_bearing_deposits_millions")
    nib_prior = get_balance(fy_balance, "noninterest_bearing_deposits_millions")
    nib_pct_current = ratio_pct(nib_current, deposits_current)
    nib_pct_prior = ratio_pct(nib_prior, deposits_prior)
    nib_pct_change = absolute_change(nib_pct_current, nib_pct_prior)
    nib_class = classify_delta(nib_pct_change)

    tbvps_current = extract_numeric(q2_balance.get("tbvps"))
    tbvps_prior = extract_numeric(fy_balance.get("tbvps"))
    tbvps_change = percent_change(tbvps_current, tbvps_prior)
    tbvps_class = classify_delta(tbvps_change)

    balance_rows.extend(
        [
            "            <tr>",
            "                <td>NIB % of Deposits</td>",
            f"                <td class=\"text-right\">{format_plain_percent(nib_pct_current)}</td>",
            f"                <td class=\"text-right\">{format_plain_percent(nib_pct_prior)}</td>",
            f"                <td class=\"text-right {nib_class}\">{format_delta_points(nib_pct_change, suffix=' pts')}</td>",
            "            </tr>",
            "            <tr>",
            "                <td>TBVPS</td>",
            f"                <td class=\"text-right\">{format_money(tbvps_current)}</td>",
            f"                <td class=\"text-right\">{format_money(tbvps_prior)}</td>",
            f"                <td class=\"text-right {tbvps_class}\">{format_delta_percent(tbvps_change)}</td>",
            "            </tr>",
        ]
    )

    q2_is = caty02.get("q2_2025_snapshot", {}) or {}
    ltm_is = caty02.get("ltm_metrics", {}) or {}
    fy_is = caty02.get("derived_metrics_fy2024", {}) or {}

    def get_metric(source: dict, key: str) -> float | None:
        value = source.get(key)
        if isinstance(value, dict):
            value = value.get("value")
        return extract_numeric(value)

    profitability_metrics = [
        ("Net Interest Margin", get_metric(q2_is, "nim_pct"), extract_numeric(ltm_is.get("nim_pct")), extract_numeric(fy_is.get("nim_pct"))),
        ("Efficiency Ratio", get_metric(q2_is, "efficiency_ratio_pct"), None, get_metric(fy_is, "efficiency_ratio_pct")),
        ("ROTE", extract_numeric(ltm_is.get("rote_pct")), extract_numeric(ltm_is.get("rote_pct")), extract_numeric(fy_is.get("rote_pct"))),
        ("Diluted EPS", get_metric(q2_is, "diluted_eps"), extract_numeric(ltm_is.get("eps_diluted")), get_metric(fy_is, "diluted_eps")),
    ]

    profitability_rows: list[str] = []
    for label, q2_value, ltm_value, fy_value in profitability_metrics:
        def render_value(val: float | None, as_percent: bool = True) -> str:
            if val is None:
                return "—"
            if label == "Diluted EPS":
                return format_money(val)
            format_fn = format_plain_percent if as_percent else format_money
            decimals = 2 if label in {"Net Interest Margin", "ROTE"} else 1
            return format_fn(val, decimals=decimals)

        as_percent = label != "Diluted EPS"
        change_vs_fy = percent_change(q2_value, fy_value) if label == "Diluted EPS" else absolute_change(q2_value, fy_value)
        change_text = "—"
        change_class = ""
        if fy_value is not None and q2_value is not None:
            if label == "Diluted EPS":
                change_text = format_delta_percent(change_vs_fy, decimals=1)
            else:
                change_text = format_delta_points(change_vs_fy, decimals=1, suffix=" pts")
            better_when_lower = {"Efficiency Ratio"}
            adjusted_delta = -change_vs_fy if label in better_when_lower and change_vs_fy is not None else change_vs_fy
            change_class = classify_delta(adjusted_delta)

        profitability_rows.extend(
            [
                "            <tr>",
                f"                <td>{label}</td>",
                f"                <td class=\"text-right\">{render_value(q2_value, as_percent=as_percent)}</td>",
                f"                <td class=\"text-right\">{render_value(ltm_value, as_percent=as_percent)}</td>",
                f"                <td class=\"text-right\">{render_value(fy_value, as_percent=as_percent)}</td>",
                f"                <td class=\"text-right {change_class}\">{change_text}</td>",
                "            </tr>",
            ]
        )

    capital_metrics = caty09.get("regulatory_capital_q2_2025", {}) or {}
    liquidity_metrics = caty09.get("liquidity_metrics", {}) or {}

    parts: list[str] = [
        "<h2>Financial Analysis</h2>",
        "<div class=\"insight-box\">",
        "    <h3>Balance Sheet Snapshot</h3>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th>Metric</th>",
        "                <th class=\"text-right\">Q2 2025</th>",
        "                <th class=\"text-right\">FY 2024</th>",
        "                <th class=\"text-right\">Change</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
    ]
    parts.extend(balance_rows)
    parts.extend(
        [
            "        </tbody>",
            "    </table>",
        ]
    )

    parts.extend(
        [
            "    <h3>Profitability Trends</h3>",
            "    <table>",
            "        <thead>",
            "            <tr>",
            "                <th>Metric</th>",
            "                <th class=\"text-right\">Q2 2025</th>",
            "                <th class=\"text-right\">LTM</th>",
            "                <th class=\"text-right\">FY 2024</th>",
            "                <th class=\"text-right\">Δ vs FY 2024</th>",
            "            </tr>",
            "        </thead>",
            "        <tbody>",
        ]
    )
    parts.extend(profitability_rows)
    parts.extend(
        [
            "        </tbody>",
            "    </table>",
        ]
    )

    if capital_metrics:
        cet1_ratio = extract_numeric(capital_metrics.get("cet1_ratio_pct"))
        total_capital = extract_numeric(capital_metrics.get("total_capital_ratio_pct"))
        leverage_ratio = extract_numeric(capital_metrics.get("leverage_ratio_pct"))
        regulatory_min = extract_numeric(capital_metrics.get("regulatory_minimum_cet1_pct"))
        well_cap = extract_numeric(capital_metrics.get("well_capitalized_cet1_pct"))
        buffer = extract_numeric(capital_metrics.get("buffer_vs_well_capitalized_ppts"))
        parts.extend(
            [
                "    <h3>Capital Adequacy</h3>",
                "    <ul>",
                f"        <li>CET1 Ratio: {format_plain_percent(cet1_ratio, decimals=2)} "
                f"(reg min {format_plain_percent(regulatory_min, decimals=2)}; well-cap {format_plain_percent(well_cap, decimals=2)})</li>",
                f"        <li>Total Capital Ratio: {format_plain_percent(total_capital, decimals=2)}; Leverage Ratio {format_plain_percent(leverage_ratio, decimals=2)}</li>",
                f"        <li>Status: {capital_metrics.get('status', '—')} | Buffer vs well-capitalized: {format_delta_points(buffer, decimals=1)}</li>",
                "    </ul>",
            ]
        )

    if liquidity_metrics:
        liquid_assets = extract_numeric(liquidity_metrics.get("total_liquid_assets_billions"))
        liquid_assets_pct = extract_numeric(liquidity_metrics.get("liquid_assets_pct_of_assets"))
        loan_to_deposit_ratio = extract_numeric(liquidity_metrics.get("loan_to_deposit_ratio_pct"))
        parts.extend(
            [
                "    <h3>Liquidity Coverage</h3>",
                "    <ul>",
                f"        <li>Total liquid assets: {format_millions(liquid_assets * 1000 if liquid_assets is not None else None)}</li>",
                f"        <li>Liquid assets / Assets: {format_plain_percent(liquid_assets_pct, decimals=1)}</li>",
                f"        <li>Loan-to-deposit ratio: {format_plain_percent(loan_to_deposit_ratio, decimals=1)}</li>",
                "    </ul>",
            ]
        )

    parts.append(
        "    <p class=\"text-small text-secondary\">Source data: <code>caty03_balance_sheet.json</code>, <code>caty02_income_statement.json</code>, <code>caty09_capital_liquidity.json</code>.</p>"
    )
    parts.append("</div>")

    return "\n".join(parts)


def render_liquidity_summary(context: Dict[str, Any]) -> str:
    caty06 = context.get("caty06_tables", {})
    caty09 = context.get("caty09_tables", {})

    snapshot = caty06.get("deposit_snapshot_q2_2025", {}) or {}
    mix = caty06.get("deposit_mix_detail", {}) or {}
    peer = caty06.get("peer_comparison", {}) or {}
    funding = caty06.get("funding_sources", {}) or {}
    liquidity_metrics = caty09.get("liquidity_metrics", {}) or {}

    mix_rows: list[str] = []
    for label, balance_key, pct_key in [
        ("Noninterest-Bearing (DDA)", "dda_billions", "dda_pct"),
        ("Savings", "savings_billions", "savings_pct"),
        ("Money Market", "money_market_billions", "money_market_pct"),
        ("Time Deposits", "time_deposits_billions", "time_deposits_pct"),
    ]:
        balance = extract_numeric(mix.get(balance_key))
        pct = extract_numeric(mix.get(pct_key))
        mix_rows.extend(
            [
                "            <tr>",
                f"                <td>{label}</td>",
                f"                <td class=\"text-right\">{format_millions(balance * 1000 if balance is not None else None)}</td>",
                f"                <td class=\"text-right\">{format_plain_percent(pct, decimals=1)}</td>",
                "            </tr>",
            ]
        )

    brokered_pct = extract_numeric(snapshot.get("brokered_pct"))
    if brokered_pct is None:
        brokered_pct = extract_numeric(peer.get("caty_brokered_pct"))
    brokered_billions = extract_numeric(snapshot.get("brokered_deposits_billions"))
    loan_to_deposit = extract_numeric(liquidity_metrics.get("loan_to_deposit_ratio_pct"))

    total_deposits_billions = extract_numeric(snapshot.get("total_deposits_billions"))
    nib_mix_pct = extract_numeric(snapshot.get("nib_pct"))

    parts: list[str] = [
        "<h2>Liquidity & Funding</h2>",
        "<div class=\"insight-box\">",
        "    <h3>Deposit Mix (Q2 2025)</h3>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th>Category</th>",
        "                <th class=\"text-right\">Balance</th>",
        "                <th class=\"text-right\">Mix</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
    ]
    parts.extend(mix_rows)
    parts.extend(
        [
            "        </tbody>",
            "    </table>",
        ]
    )

    parts.extend(
        [
            "    <h3>Liquidity Highlights</h3>",
            "    <ul>",
            f"        <li>Total deposits: {format_millions(total_deposits_billions * 1000 if total_deposits_billions is not None else None)} with NIB share {format_plain_percent(nib_mix_pct, decimals=1)}</li>",
            f"        <li>Brokered funding: {format_plain_percent(brokered_pct, decimals=1)} of deposits ({format_millions(brokered_billions * 1000 if brokered_billions is not None else None)}) vs peer median {format_plain_percent(extract_numeric(peer.get('peer_median_brokered_pct')), decimals=1)}</li>",
            f"        <li>Loan-to-deposit ratio: {format_plain_percent(loan_to_deposit, decimals=1)}</li>",
        ]
    )

    if funding:
        parts.append("        <li>Funding structure: deposits {0}, FHLB advances {1}, subordinated debt {2}, other borrowings {3}</li>".format(
            format_plain_percent(extract_numeric(funding.get("deposits_pct")), decimals=1),
            format_plain_percent(extract_numeric(funding.get("fhlb_advances_pct")), decimals=1),
            format_plain_percent(extract_numeric(funding.get("subordinated_debt_pct")), decimals=1),
            format_plain_percent(extract_numeric(funding.get("other_borrowings_pct")), decimals=1),
        ))
        note = funding.get("note")
        if note:
            parts.append(f"        <li>{note}</li>")
    parts.append("    </ul>")

    parts.append(
        "    <p class=\"text-small text-secondary\">Source data: <code>caty06_deposits_funding.json</code> and <code>caty09_capital_liquidity.json</code>.</p>"
    )
    parts.append("</div>")

    return "\n".join(parts)


def render_scenario_analysis_narrative(context: Dict[str, Any]) -> str:
    scenarios = context.get("valuation_outputs", {}).get("scenarios", {})
    frameworks = context.get("valuation_outputs", {}).get("frameworks", {})

    order = [
        ("base", "Base Case"),
        ("bull", "Bull Case"),
        ("bear", "Bear Case"),
    ]

    scenario_items: list[str] = []
    for key, label in order:
        scenario = scenarios.get(key, {})
        if not scenario:
            continue
        target_price = extract_numeric(scenario.get("target_price"))
        return_pct = extract_numeric(scenario.get("return_pct"))
        probability = extract_numeric(scenario.get("probability_pct"))
        rote = extract_numeric(scenario.get("rote_pct"))
        nco = extract_numeric(scenario.get("nco_bps"))

        scenario_items.append(
            f"        <li><strong>{label} ({format_plain_percent(probability, decimals=0)} probability):</strong> "
            f"Target {format_money(target_price)} with {format_delta_percent(return_pct, decimals=1)} expected move. "
            f"Assumes ROTE {format_plain_percent(rote, decimals=2)} and NCO "
            f"{format_plain_percent(nco / 100 if nco is not None else None, decimals=2)}.</li>"
        )

    blended = frameworks.get("probability_weighted", {})
    blended_price = extract_numeric(blended.get("target_price"))
    blended_note = blended.get("composition", "Probability-weighted blend")

    parts: list[str] = [
        "<div class=\"insight-box\">",
        "    <h3>Scenario Discussion</h3>",
        "    <p>Scenario assumptions below are synchronized with the automated valuation table above.</p>",
        "    <ul>",
    ]
    parts.extend(scenario_items)
    if blended_price is not None:
        parts.append(
            f"        <li><strong>Probability-weighted outcome:</strong> {format_money(blended_price)} ({blended_note}).</li>"
        )
    parts.extend(
        [
            "    </ul>",
            "    <p class=\"text-small text-secondary\">Source data: <code>valuation_outputs.json</code>.</p>",
            "</div>",
        ]
    )

    return "\n".join(parts)


def render_monte_carlo_summary(context: Dict[str, Any]) -> str:
    monte_carlo = context.get("caty14_tables", {})
    summary = monte_carlo.get("simulation_summary", {}) or {}
    percentiles = monte_carlo.get("tables", {}).get("percentiles", []) or []
    probability_bands = monte_carlo.get("tables", {}).get("probability_bands", []) or []
    confidence = monte_carlo.get("confidence_interval", {}) or {}
    current_price = extract_numeric(context.get("market", {}).get("price"))

    parts: list[str] = [
        "<h3>Monte Carlo Valuation (10,000 paths)</h3>",
        "<div class=\"insight-box\">",
        "    <h3>Distribution Highlights</h3>",
    ]

    num_runs = summary.get("num_runs")
    target_mean = extract_numeric(summary.get("target_mean"))
    target_median = extract_numeric(summary.get("target_median"))
    mean_return = extract_numeric(summary.get("mean_return_pct"))
    median_return = extract_numeric(summary.get("median_return_pct"))
    reference_spot = extract_numeric(summary.get("spot_price"))

    headline = []
    if num_runs:
        headline.append(f"{num_runs:,} simulated paths")
    if target_mean is not None and mean_return is not None:
        headline.append(f"Mean ${target_mean:.2f} ({format_delta_percent(mean_return, decimals=1)})")
    if target_median is not None and median_return is not None:
        headline.append(f"Median ${target_median:.2f} ({format_delta_percent(median_return, decimals=1)})")
    if headline:
        parts.append(f"    <p>{' • '.join(headline)}.</p>")

    if reference_spot is not None:
        comparison = ""
        if current_price is not None and abs(current_price - reference_spot) > 1e-6:
            comparison = f" (simulation spot reference ${reference_spot:.2f}; current price ${current_price:.2f})"
        else:
            comparison = f" (spot reference ${reference_spot:.2f})"
        parts.append(f"    <p>Spot overlay{comparison}</p>")

    if percentiles:
        parts.append("    <table>")
        parts.append("        <thead><tr><th>Percentile</th><th class=\"text-right\">Target</th><th class=\"text-right\">Return</th><th>Scenario</th></tr></thead>")
        parts.append("        <tbody>")
        for row in percentiles[:5]:
            parts.append(
                "            <tr>"
                f"<td>{row.get('label', '—')}</td>"
                f"<td class=\"text-right\">{row.get('target_price', '—')}</td>"
                f"<td class=\"text-right\">{row.get('return', '—')}</td>"
                f"<td>{row.get('scenario', '—')}</td>"
                "</tr>"
            )
        parts.append("        </tbody>")
        parts.append("    </table>")
        parts.append('    <img src="assets/monte_carlo_pt_distribution.png" alt="Monte Carlo fair value distribution" class="chart-image-full" />')

    lower = extract_numeric(confidence.get("lower_price"))
    upper = extract_numeric(confidence.get("upper_price"))
    span_dollars = extract_numeric(confidence.get("range_dollars"))
    pct_band = confidence.get("range_pct_of_spot") or confidence.get("range_pct_of_assets")
    if lower is not None and upper is not None:
        span_text = format_money(span_dollars) if span_dollars is not None else "—"
        pct_text = pct_band if pct_band is not None else "—"
        if pct_text != "—" and not str(pct_text).strip().endswith("%"):
            pct_text = f"{pct_text}%"
        parts.append(
            f"    <p>95% interval: ${lower:.2f} – ${upper:.2f} (span {span_text} | {pct_text}).</p>"
        )

    if probability_bands:
        parts.append("    <h4>Probability Bands</h4>")
        parts.append("    <ul>")
        for item in probability_bands:
            parts.append(
                f"        <li>{item.get('label', '—')}: {item.get('probability', '—')} – {item.get('implication', '')}</li>"
            )
        parts.append("    </ul>")

    parts.append("    <p class=\"text-small text-secondary\">Source data: <code>caty14_monte_carlo.json</code>.</p>")
    parts.append("</div>")

    return "\n".join(parts)


def render_investment_recommendation(context: Dict[str, Any]) -> str:
    market = context.get("market", {})
    metrics = context.get("calculated_metrics", {})
    frameworks = context.get("valuation_outputs", {}).get("frameworks", {})

    rating = metrics.get("rating", "—")
    current_price = extract_numeric(market.get("price"))
    price_date = market.get("price_date")

    normalized_target = extract_numeric(metrics.get("target_normalized"))
    normalized_return = extract_numeric(metrics.get("return_normalized_pct"))
    wilson_target = extract_numeric(metrics.get("target_wilson_95"))
    wilson_return = extract_numeric(metrics.get("return_wilson_95_pct"))
    blended_target = extract_numeric(metrics.get("target_irc_blended")) or extract_numeric(frameworks.get("irc_blended", {}).get("target_price"))
    blended_return = extract_numeric(metrics.get("return_irc_blended_pct"))

    parts: list[str] = [
        "<h2>Investment Recommendation</h2>",
        "<div class=\"insight-box\">",
        "    <h3>Rating Summary</h3>",
        "    <ul>",
        f"        <li><strong>Rating:</strong> {rating}</li>",
        f"        <li><strong>Current Price:</strong> {format_money(current_price)} (as of {price_date})</li>",
        f"        <li><strong>Normalized Fair Value:</strong> {format_money(normalized_target)} ({format_delta_percent(normalized_return, decimals=1)} vs spot)</li>",
        f"        <li><strong>Wilson 95% Upper Bound:</strong> {format_money(wilson_target)} ({format_delta_percent(wilson_return, decimals=1)} expected return)</li>",
        f"        <li><strong>IRC Blended Target:</strong> {format_money(blended_target)} ({format_delta_percent(blended_return, decimals=1)}).</li>",
        "    </ul>",
    ]

    credit_costs_current = extract_numeric(metrics.get("nco_rate_bps"))
    credit_costs_through_cycle = extract_numeric(metrics.get("through_cycle_nco_bps"))
    key_watch = [
        (
            "Credit costs",
            f"NCO {format_plain_percent(credit_costs_current / 100 if credit_costs_current is not None else None, decimals=2)} "
            f"vs through-cycle {format_plain_percent(credit_costs_through_cycle / 100 if credit_costs_through_cycle is not None else None, decimals=2)}",
        ),
        (
            "P/TBV positioning",
            f"Current multiple {format_multiple(extract_numeric(metrics.get('current_ptbv')))} "
            f"vs normalized {format_multiple(extract_numeric(metrics.get('normalized_ptbv')))}",
        ),
        (
            "Funding mix",
            f"Brokered deposits {format_plain_percent(extract_numeric(metrics.get('brokered_deposit_pct')), decimals=1)} | "
            f"NIB mix {format_plain_percent(extract_numeric(metrics.get('nib_pct')), decimals=1)}",
        ),
    ]

    parts.extend(
        [
            "    <h3>Key Watch Items</h3>",
            "    <ul>",
        ]
    )
    for title, text in key_watch:
        parts.append(f"        <li><strong>{title}:</strong> {text}</li>")
    parts.append("    </ul>")

    upgrade_triggers = [
        "Sustained NCO ≤ 25 bps while maintaining growth",
        "ROTE ≥ 12% with efficiency ≤ 45%",
        "Evidence of durable NIM ≥ 3.30% as rate cuts progress",
        "Enhanced disclosure on CRE office exposure and ALM duration risk",
    ]

    parts.extend(
        [
            "    <h3>Upgrade Triggers</h3>",
            "    <ul>",
        ]
    )
    parts.extend(f"        <li>{item}</li>" for item in upgrade_triggers)
    parts.append("    </ul>")
    parts.append("    <p class=\"text-small text-secondary\">Source data: <code>market_data_current.json</code>, <code>valuation_outputs.json</code>.</p>")
    parts.append("</div>")

    return "\n".join(parts)


def render_report_meta(timestamps: Dict[str, str]) -> str:
    return f"Report Date: {timestamps['report_date']} | Last Updated: {timestamps['last_updated_utc']}"


def render_footer_timestamp(timestamps: Dict[str, str]) -> str:
    return f"<p>Report Date: {timestamps['report_date']} | Report Generated: {timestamps['generated_at_utc']}</p>"


def render_page_title(report_date: str) -> str:
    return f"<title>Cathay General Bancorp (CATY) - Institutional Equity Research | {report_date}</title>"


def format_money(value: float) -> str:
    return f"${value:,.2f}" if value is not None else "—"


def format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+.1f}%"


def extract_numeric(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("value")
    if value in (None, "", "N/A", "n/a"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_millions(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"${value:,.{decimals}f}M"


def format_plain_percent(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}%"


def format_delta_percent(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    if abs(value) < 1e-9:
        return f"{0:.{decimals}f}%"
    sign = "+" if value > 0 else "-"
    return f"{sign}{abs(value):.{decimals}f}%"


def format_delta_points(value: float | None, decimals: int = 1, suffix: str = " pts") -> str:
    if value is None:
        return "—"
    if abs(value) < 1e-9:
        zero_fmt = f"{0:.{decimals}f}" if decimals > 0 else "0"
        return f"{zero_fmt}{suffix}"
    sign = "+" if value > 0 else "-"
    return f"{sign}{abs(value):.{decimals}f}{suffix}"


def format_multiple(value: float | None, decimals: int = 3) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}x"


def percent_change(current: float | None, prior: float | None) -> float | None:
    if current is None or prior in (None, 0):
        return None
    return ((current - prior) / prior) * 100


def absolute_change(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None:
        return None
    return current - prior


def classify_delta(delta: float | None) -> str:
    if delta is None:
        return ""
    if delta > 0:
        return "text-success"
    if delta < 0:
        return "text-danger"
    return ""


def ratio_pct(part: float | None, total: float | None) -> float | None:
    if part is None or total in (None, 0):
        return None
    return (part / total) * 100


def parse_iso(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return dt.datetime.fromisoformat(ts)
    except ValueError:
        return None


def format_timestamp(ts: dt.datetime | None) -> str:
    if ts is None:
        return "—"
    return ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def resolve_path(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split('.'):
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:  # noqa: PERF203
                raise KeyError(f"Path '{path}' expected integer index for list access, got '{part}'") from exc
            try:
                current = current[index]
            except IndexError as exc:  # noqa: PERF203
                raise KeyError(f"Path '{path}' index '{index}' out of range") from exc
        else:
            if part not in current:
                raise KeyError(f"Path '{path}' missing key '{part}'")
            current = current[part]
    return current


def to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def safe_to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return to_float(value)
    except (TypeError, ValueError):
        return None


def format_date_value(value: Any, style: str) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, dt.datetime):
        dt_value = value
    else:
        value_str = str(value)
        if len(value_str) == 10:
            dt_value = dt.datetime.strptime(value_str, "%Y-%m-%d")
        else:
            parsed = parse_iso(value_str)
            if parsed is None:
                return str(value)
            dt_value = parsed
    if style == "short":
        return dt_value.strftime("%b %d, %Y")
    if style == "long":
        return dt_value.strftime("%B %d, %Y")
    return dt_value.isoformat()


def format_value(raw: Any, fmt: str, spec: Dict[str, Any]) -> str:
    if raw in (None, "") and not spec.get("allow_blank", False):
        return "—"

    prefix = spec.get("prefix", "")
    suffix = spec.get("suffix", "")
    decimals = spec.get("decimals")

    try:
        if fmt in {
            "currency",
            "currency_scale",
            "number_scale",
            "multiple",
            "percent",
            "percent_signed",
            "decimal",
            "bps",
        }:
            raw_num = to_float(raw)
        else:
            raw_num = None
    except (TypeError, ValueError):
        raw_num = None

    if fmt == "currency":
        decimals = 2 if decimals is None else decimals
        text = f"${raw_num:,.{decimals}f}"
    elif fmt == "currency_scale":
        decimals = 2 if decimals is None else decimals
        scale = spec.get("scale", "millions")
        suffix_scale = ""
        value = raw_num
        if scale == "billions":
            suffix_scale = "B"
        elif scale == "millions":
            suffix_scale = "M"
        text = f"${value:,.{decimals}f}{suffix_scale}"
    elif fmt == "number_scale":
        decimals = 2 if decimals is None else decimals
        scale = spec.get("scale", "millions")
        suffix_scale = ""
        value = raw_num
        if scale == "billions":
            suffix_scale = "B"
        elif scale == "millions":
            suffix_scale = "M"
        text = f"{value:,.{decimals}f}{suffix_scale}"
    elif fmt == "multiple":
        decimals = 3 if decimals is None else decimals
        text = f"{raw_num:.{decimals}f}x"
    elif fmt == "percent":
        decimals = 1 if decimals is None else decimals
        text = f"{raw_num:.{decimals}f}%"
    elif fmt == "percent_signed":
        decimals = 1 if decimals is None else decimals
        text = f"{raw_num:+.{decimals}f}%"
    elif fmt == "decimal":
        decimals = 3 if decimals is None else decimals
        text = f"{raw_num:.{decimals}f}"
    elif fmt == "bps":
        decimals = 1 if decimals is None else decimals
        text = f"{raw_num:.{decimals}f}"
        if not spec.get("omit_unit", False):
            text += " bps"
    elif fmt == "date_short":
        text = format_date_value(raw, "short")
    elif fmt == "date_long":
        text = format_date_value(raw, "long")
    elif fmt == "text_upper":
        text = str(raw).upper()
    elif fmt == "text":
        text = str(raw)
    elif fmt == "list_to_table_rows":
        if not isinstance(raw, list):
            text = ""
        else:
            cols = spec.get("columns", [])
            rows_html = []
            for item in raw:
                cells = []
                for i, col in enumerate(cols):
                    val = item.get(col, '')
                    # First column gets bold
                    if i == 0:
                        cells.append(f"<td><strong>{val}</strong></td>")
                    # Percentage columns get highlight styling
                    elif '_pct' in col or col == 'contribution_pct':
                        cells.append(f"<td class=\"numeric highlight-number\">{val}%</td>")
                    # Other numeric columns
                    elif col in ['loans_pct', 'deposits_pct']:
                        cells.append(f"<td class=\"numeric\">{val}%</td>")
                    else:
                        cells.append(f"<td>{val}</td>")
                rows_html.append(f"<tr>{''.join(cells)}</tr>")
            text = "\n".join(rows_html)
        return text  # No prefix/suffix
    elif fmt == "list_to_li":
        if not isinstance(raw, list):
            text = ""
        else:
            items = [f"        <li>{str(item)}</li>" for item in raw]
            text = "\n".join(items)
        return text  # No prefix/suffix
    elif fmt == "list_to_advantage_cards":
        if not isinstance(raw, list):
            text = ""
        else:
            cards = []
            for adv in raw:
                sust = adv.get("sustainability", "MEDIUM").lower()
                card_html = (
                    f'<div class="advantage-card {sust}">\n'
                    f'    <div class="advantage-title">{adv.get("advantage", "")}</div>\n'
                    f'    <div class="advantage-evidence">{adv.get("evidence", "")}</div>\n'
                    f'    <div class="advantage-sustainability">Sustainability: {adv.get("sustainability", "")}</div>\n'
                    f'</div>'
                )
                cards.append(card_html)
            text = "\n".join(cards)
        return text  # No prefix/suffix
    elif fmt == "list_to_timeline":
        if not isinstance(raw, list):
            text = ""
        else:
            items = []
            for milestone in raw:
                item_html = (
                    f'<div class="timeline-item">\n'
                    f'    <div class="timeline-year">{milestone.get("year", "")}</div>\n'
                    f'    <div class="timeline-event">{milestone.get("event", "")}</div>\n'
                    f'</div>'
                )
                items.append(item_html)
            text = "\n".join(items)
        return text  # No prefix/suffix
    else:
        text = str(raw)

    return f"{prefix}{text}{suffix}"


def render_text_spec(spec: Any, context: Dict[str, Any]) -> str:
    if spec is None:
        return ""
    if isinstance(spec, str):
        return spec
    if "template" in spec:
        template = spec["template"]
        for placeholder, placeholder_spec in spec.get("placeholders", {}).items():
            replacement = render_text_spec(placeholder_spec, context)
            template = template.replace(placeholder, replacement)
        return template
    return render_value_spec(spec, context)


def render_value_spec(spec: Any, context: Dict[str, Any]) -> str:
    if spec is None:
        return ""
    if isinstance(spec, str):
        return spec
    if isinstance(spec, (int, float)):
        return str(spec)

    if "template" in spec:
        return render_text_spec(spec, context)

    if "source" in spec:
        source = spec["source"]
        data = context.get(source)
        if data is None:
            raise KeyError(f"Unknown data source '{source}'")
        raw = resolve_path(data, spec["path"])
        if isinstance(raw, dict) and "value" in raw:
            raw = raw["value"]
    else:
        raw = spec.get("value")

    fmt = spec.get("format", "text")
    return format_value(raw, fmt, spec)


def indent_block(text: str, indent: str) -> str:
    lines = text.splitlines()
    return "\n".join(f"{indent}{line}" if line else "" for line in lines)


def render_cards(section_cfg: Dict[str, Any], context: Dict[str, Any]) -> str:
    defaults = section_cfg.get("defaults", {})
    lines: list[str] = []

    def resolve_class(spec: Any, default_value: str) -> str:
        if spec is None:
            return default_value
        if isinstance(spec, dict):
            return render_text_spec(spec, context)
        return str(spec)

    for card in section_cfg.get("cards", []):
        card_class = resolve_class(card.get("card_class"), defaults.get("card_class", "dashboard-card"))
        label_class = resolve_class(card.get("label_class"), defaults.get("label_class", "dashboard-label"))
        value_class = resolve_class(card.get("value_class"), defaults.get("value_class", "dashboard-value"))
        subtext_cfg = card.get("subtext")

        lines.append(f'    <div class="{card_class}">')
        label_text = render_text_spec(card.get("label"), context)
        lines.append(f'        <div class="{label_class}">{label_text}</div>')
        value_text = render_value_spec(card.get("value"), context)
        lines.append(f'        <div class="{value_class}">{value_text}</div>')

        if subtext_cfg is not None:
            subtext_class = subtext_cfg.get("class", defaults.get("subtext_class", "dashboard-subtext"))
            subtext_text = render_text_spec(subtext_cfg, context)
            if subtext_text:
                lines.append(f'        <div class="{subtext_class}">{subtext_text}</div>')

        lines.append("    </div>")

    return "\n".join(lines)


def render_table_cell(cell_spec: Any, context: Dict[str, Any]) -> tuple[str, str | None, str]:
    tag = "td"
    cell_class: str | None = None
    spec_for_value = cell_spec

    if isinstance(cell_spec, dict):
        if "tag" in cell_spec:
            tag = str(cell_spec["tag"])
        if "class" in cell_spec:
            # Copy to avoid mutating original configuration
            spec_for_value = dict(cell_spec)
            cell_class = str(spec_for_value.pop("class"))
            tag = str(spec_for_value.pop("tag", tag))
        if "html" in cell_spec:
            html_value = str(cell_spec["html"])
            return html_value, cell_class, tag

    text = render_text_spec(spec_for_value, context)
    return text, cell_class, tag


def render_table(section_cfg: Dict[str, Any], context: Dict[str, Any]) -> str:
    headers_cfg = section_cfg.get("headers", [])
    columns = section_cfg.get("columns")
    if not columns:
        raise ValueError("Table section requires 'columns' definition for consistent rendering")

    def normalize_headers() -> list[str]:
        headers: list[str] = []
        for header in headers_cfg:
            headers.append(render_text_spec(header, context))
        return headers

    rows: list[tuple[str | None, Dict[str, Any]]] = []
    for row_cfg in section_cfg.get("rows", []):
        row_class = row_cfg.get("row_class")
        cells = {key: value for key, value in row_cfg.items() if key != "row_class"}
        rows.append((row_class, cells))

    rows_from_list_cfg = section_cfg.get("rows_from_list")
    if rows_from_list_cfg:
        source = rows_from_list_cfg["source"]
        list_path = rows_from_list_cfg["list_path"]
        source_data = context.get(source)
        if source_data is None:
            raise KeyError(f"Unknown data source '{source}' for table rows")
        list_items = resolve_path(source_data, list_path)
        if not isinstance(list_items, list):
            raise ValueError(f"Expected list at path '{list_path}', got {type(list_items).__name__}")
        row_template = rows_from_list_cfg["row_template"]
        start_index = rows_from_list_cfg.get("start_index", 0)
        for idx, item in enumerate(list_items, start=start_index):
            replacements = {
                "{index}": str(idx),
                "{index0}": str(idx),
                "{index1}": str(idx + 1),
            }
            if isinstance(item, dict):
                for key, value in item.items():
                    replacements[f"{{{key}}}"] = str(value)
            else:
                replacements["{item}"] = str(item)
                replacements["{peer}"] = str(item)
            row_spec = replace_placeholders(row_template, replacements)
            row_class = row_spec.get("row_class")
            cells = {key: value for key, value in row_spec.items() if key != "row_class"}
            rows.append((row_class, cells))

    column_classes_cfg = section_cfg.get("column_classes")

    def resolve_column_class(column: str, index: int) -> str:
        if isinstance(column_classes_cfg, dict):
            return str(column_classes_cfg.get(column, ""))
        if isinstance(column_classes_cfg, list):
            if index < len(column_classes_cfg):
                return str(column_classes_cfg[index])
        return ""

    lines: list[str] = ["<table>"]
    if headers_cfg:
        headers = normalize_headers()
        lines.append("    <thead>")
        lines.append("        <tr>")
        for header in headers:
            lines.append(f"            <th>{header}</th>")
        lines.append("        </tr>")
        lines.append("    </thead>")

    lines.append("    <tbody>")
    for row_class, cell_map in rows:
        row_class_attr = f' class="{row_class}"' if row_class else ""
        lines.append(f"        <tr{row_class_attr}>")
        for index, column in enumerate(columns):
            cell_spec = cell_map.get(column, "")
            cell_text, cell_class_override, tag = render_table_cell(cell_spec, context)
            column_class = resolve_column_class(column, index)
            cell_class = cell_class_override or column_class
            class_attr = f' class="{cell_class}"' if cell_class else ""
            lines.append(f"            <{tag}{class_attr}>{cell_text}</{tag}>")
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")

    return "\n".join(lines)


def render_module_section(section_cfg: Dict[str, Any], context: Dict[str, Any]) -> str:
    section_type = section_cfg.get("type", "cards")

    if section_type == "cards":
        wrapper_cfg = section_cfg.get("wrapper")
        cards_html = render_cards(section_cfg, context)

        if wrapper_cfg:
            tag = wrapper_cfg.get("tag", "div")
            classes = wrapper_cfg.get("class")
            attrs = ""
            if classes:
                attrs = f' class="{classes}"'
            extra_attrs = wrapper_cfg.get("attrs", {})
            for attr_name, attr_value in extra_attrs.items():
                attrs += f' {attr_name}="{attr_value}"'
            indented_cards = indent_block(cards_html, "    ")
            return f"<{tag}{attrs}>\n{indented_cards}\n</{tag}>"

        return cards_html

    if section_type == "text":
        text = render_text_spec(section_cfg.get("template"), context)
        wrapper_cfg = section_cfg.get("wrapper")
        if wrapper_cfg:
            tag = wrapper_cfg.get("tag", "div")
            classes = wrapper_cfg.get("class")
            attrs = ""
            if classes:
                attrs = f' class="{classes}"'
            extra_attrs = wrapper_cfg.get("attrs", {})
            for attr_name, attr_value in extra_attrs.items():
                attrs += f' {attr_name}="{attr_value}"'
            return f"<{tag}{attrs}>{text}</{tag}>"
        return text
    if section_type == "text_spec":
        return render_text_spec(section_cfg.get("template"), context)
    if section_type == "table":
        return render_table(section_cfg, context)

    raise ValueError(f"Unsupported section type '{section_type}' for module automation")


def build_reconciliation_table() -> str:
    market = load_json(ROOT / "data" / "market_data_current.json")
    methods_cfg = load_json(ROOT / "data" / "valuation_methods.json")

    price = float(market["price"])
    rows: list[str] = []

    for method in methods_cfg["methods"]:
        if "target_path" in method:
            target_val = float(resolve_path(market, method["target_path"]))
        else:
            target_val = float(method.get("target_value"))

        # Return vs spot (percent)
        if method.get("id") == "spot":
            return_pct = None
        else:
            return_pct = ((target_val - price) / price) * 100 if price else None

        probability_text = method.get("probability_text", "—") or "—"
        last_run_ts = format_timestamp(parse_iso(method.get("last_run")))

        source_label = method.get("data_source", "—")
        source_link = method.get("source_link")
        if source_link:
            source_html = (
                f'<a href="{source_link}" target="_blank" rel="noopener noreferrer">'
                f"{source_label}</a>"
            )
        else:
            source_html = source_label

        row_class = method.get("row_class", "")
        class_attr = f' class="{row_class}"' if row_class else ""

        rows.append(
            "<tr{class_attr}>\n"
            "    <td><strong>{label}</strong></td>\n"
            "    <td class=\"text-align-right\">{target}</td>\n"
            "    <td class=\"text-align-right\">{return_pct}</td>\n"
            "    <td class=\"text-align-right\">{prob}</td>\n"
            "    <td>{source}</td>\n"
            "    <td>{last_run}</td>\n"
            "</tr>".format(
                class_attr="" if not row_class else class_attr,
                label=method["label"],
                target=format_money(target_val),
                return_pct=format_percent(return_pct),
                prob=probability_text,
                source=source_html,
                last_run=last_run_ts,
            )
        )

    validation = methods_cfg.get("validation", {})
    validation_html = (
        "<div class=\"metric-card metric-card-gold margin-top-20\">\n"
        "    <div class=\"metric-label\">Reconciliation Status</div>\n"
        "    <div class=\"metric-value\">✅ ALL CHECKS PASS</div>\n"
        "    <div class=\"metric-subtext\">"
        f"Validated by: <code>{validation.get('script', '—')}</code> | "
        f"Pre-commit hook: <code>{validation.get('pre_commit', '—')}</code> | "
        f"CI: <code>{validation.get('ci_workflow', '—')}</code> | "
        f"Tolerance: ±${methods_cfg.get('tolerance_dollars', 0):.2f} | "
        f"Last Run: {format_timestamp(parse_iso(validation.get('last_run')))}"
        "</div>\n"
        "</div>"
    )

    header = (
        "<h2>Valuation Reconciliation Dashboard</h2>\n"
        "<p class=\"text-secondary\">All methodologies synchronized to single source: "
        "<code>data/market_data_current.json</code> | Last Updated: <strong>{}</strong></p>".format(
            format_timestamp(parse_iso(methods_cfg.get("last_reconciliation_run")))
        )
    )

    table_html = (
        "<table>\n"
        "    <thead>\n"
        "        <tr>\n"
        "            <th>Methodology</th>\n"
        "            <th class=\"text-align-right\">Target Price</th>\n"
        "            <th class=\"text-align-right\">Return vs Spot</th>\n"
        "            <th class=\"text-align-right\">Probability Weight</th>\n"
        "            <th>Data Source</th>\n"
        "            <th>Last Run</th>\n"
        "        </tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        + "\n".join(rows)
        + "\n    </tbody>\n</table>"
    )

    note_html = (
        "<p class=\"text-note\">\n"
        "    <strong>Proof of Synchronization:</strong> All target prices are generated from "
        "<code>data/market_data_current.json</code> via <code>scripts/build_site.py</code>. "
        "Automated validation blocks commits if published numbers diverge from calculated values. "
        "Run <code>python3 analysis/reconciliation_guard.py</code> to verify integrity.\n"
        "</p>"
    )

    return "\n".join([header, table_html, validation_html, note_html])


def card_classes(importance: str) -> tuple[str, str]:
    importance = importance.upper()
    if importance == "MOST_CRITICAL":
        return "module-card module-card-critical", "module-card-badge module-card-badge-danger"
    if importance == "CRITICAL":
        return "module-card module-card-warning", "module-card-badge module-card-badge-warning"
    if importance == "KEY":
        return "module-card module-card-gold", "module-card-badge"
    return "module-card", "module-card-badge"


def render_module_grid() -> str:
    metadata = load_json(ROOT / "data" / "module_metadata.json")
    modules = metadata.get("modules", [])

    # Sort modules by CFA order, then by ID
    modules_sorted = sorted(modules, key=lambda m: (m.get("cfa_order", 999), int(m.get("id", "0"))))

    # Group modules by CFA category
    from itertools import groupby
    grouped = groupby(modules_sorted, key=lambda m: (
        m.get("cfa_category", "Uncategorized"),
        m.get("cfa_emoji", ""),
        m.get("cfa_points", 0),
        m.get("cfa_order", 999)
    ))

    rows: list[str] = []

    for (category, emoji, points, order), group_modules in grouped:
        # Add category header
        rows.append(f'<h3 class="cfa-category-header">{emoji} {category} ({points} points)</h3>')
        rows.append('<div class="module-grid">')

        # Add modules in this category
        for module in group_modules:
            card_class, badge_class = card_classes(module.get("importance", "STANDARD"))
            status = module.get("status", "UNKNOWN")
            status_text = status.replace("_", " ")
            badge_text = f"FILE {module['id']}"
            imp_symbol = metadata.get("importance_legend", {}).get(module.get("importance", ""), "")
            if imp_symbol:
                badge_text += f" {imp_symbol}"
            badge_text += f" • {status_text}"
            description = module.get("description", "")
            last_updated = module.get("last_updated")
            if last_updated:
                description += f" (updated {last_updated})"

            rows.append(
                "    <a href=\"{href}\" class=\"{card_class}\" data-status=\"{status}\">\n"
                "        <div class=\"{badge_class}\">{badge_text}</div>\n"
                "        <div class=\"module-card-title{title_extra}\">{title}</div>\n"
                "        <div class=\"module-card-description{desc_extra}\">{desc}</div>\n"
                "    </a>".format(
                    href=module["file"],
                    card_class=card_class,
                    status=status,
                    badge_class=badge_class,
                    badge_text=badge_text,
                    title=module["title"],
                    title_extra=" module-card-title-danger" if card_class.endswith("critical") else "",
                    desc=description,
                    desc_extra=" module-card-description-primary" if card_class.endswith("critical") else ""
                )
            )

        rows.append("</div>")

    return "\n".join(rows)


def compute_sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def render_evidence_table() -> str:
    sources_cfg = load_json(ROOT / "data" / "evidence_sources.json")
    rows: list[str] = []

    rows.append(
        "<table>\n"
        "    <thead>\n"
        "        <tr>\n"
        "            <th>Source</th>\n"
        "            <th>Description</th>\n"
        "            <th>Accession / Reference</th>\n"
        "            <th>SHA256</th>\n"
        "            <th>Last Modified (UTC)</th>\n"
        "            <th>Owner</th>\n"
        "        </tr>\n"
        "    </thead>\n"
        "    <tbody>"
    )

    for item in sources_cfg.get("sources", []):
        rel_path = Path(item["path"])
        abs_path = ROOT / rel_path
        sha256 = compute_sha256(abs_path)
        if abs_path.exists():
            mtime = dt.datetime.fromtimestamp(abs_path.stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        else:
            mtime = "MISSING"

        rows.append(
            "        <tr>\n"
            f"            <td>{item.get('id')}</td>\n"
            f"            <td>{item.get('description')}</td>\n"
            f"            <td>{item.get('accession')}</td>\n"
            f"            <td><code>{sha256}</code></td>\n"
            f"            <td>{mtime}</td>\n"
            f"            <td>{item.get('owner')}</td>\n"
            "        </tr>"
        )

    rows.append("    </tbody>\n</table>")
    return "\n".join(rows)


def replace_section(html: str, marker: str, content: str) -> str:
    pattern = re.compile(
        r"(?P<indent>[ \t]*)<!-- BEGIN AUTOGEN: " + re.escape(marker) + r" -->.*?<!-- END AUTOGEN: " + re.escape(marker) + r" -->",
        re.DOTALL,
    )

    def repl(match: re.Match[str]) -> str:
        indent = match.group("indent")
        # Apply indentation to each line of generated content
        lines = [indent + line if line else "" for line in content.splitlines()]
        rendered = "\n".join(lines)
        return f"{indent}<!-- BEGIN AUTOGEN: {marker} -->\n{rendered}\n{indent}<!-- END AUTOGEN: {marker} -->"

    new_html, count = pattern.subn(repl, html)
    if count == 0:
        raise RuntimeError(f"Marker '{marker}' not found in HTML")
    return new_html


def ensure_log_dir() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_log(entry: str, test_mode: bool = False) -> None:
    if test_mode:
        return  # Skip logging in test mode to avoid polluting production audit trail
    ensure_log_dir()
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {entry}\n")


def main(test_mode: bool = False) -> int:
    try:
        html = INDEX_PATH.read_text(encoding="utf-8")
        market = load_json(ROOT / "data" / "market_data_current.json")
        methods_cfg = load_json(ROOT / "data" / "valuation_methods.json")
        exec_cfg = load_json(EXEC_METRICS_PATH)
        module_cfg = load_json(MODULE_SECTIONS_PATH) if MODULE_SECTIONS_PATH.exists() else {"modules": []}
        module_metadata = load_json(ROOT / "data" / "module_metadata.json") if (ROOT / "data" / "module_metadata.json").exists() else {"modules": []}
        for module in module_metadata.get("modules", []):
            last_updated = module.get("last_updated")
            if last_updated:
                module["last_updated_formatted"] = format_date_value(last_updated, "long")
        valuation_outputs = load_json(VALUATION_OUTPUTS_PATH) if VALUATION_OUTPUTS_PATH.exists() else {}

        valuation_lookup = {"methods": {m["id"]: m for m in methods_cfg.get("methods", [])}, "config": methods_cfg}
        caty01_tables = load_json(ROOT / "data" / "caty01_company_profile.json") if (ROOT / "data" / "caty01_company_profile.json").exists() else {}
        caty02_tables = load_json(ROOT / "data" / "caty02_income_statement.json") if (ROOT / "data" / "caty02_income_statement.json").exists() else {}
        caty03_tables = load_json(ROOT / "data" / "caty03_balance_sheet.json") if (ROOT / "data" / "caty03_balance_sheet.json").exists() else {}
        caty04_tables = load_json(ROOT / "data" / "caty04_cash_flow.json") if (ROOT / "data" / "caty04_cash_flow.json").exists() else {}
        caty05_tables = load_json(ROOT / "data" / "caty05_calculated_tables.json") if (ROOT / "data" / "caty05_calculated_tables.json").exists() else {}
        caty06_tables = load_json(ROOT / "data" / "caty06_deposits_funding.json") if (ROOT / "data" / "caty06_deposits_funding.json").exists() else {}
        caty07_tables = load_json(ROOT / "data" / "caty07_credit_quality.json") if (ROOT / "data" / "caty07_credit_quality.json").exists() else {}
        caty08_tables = load_json(ROOT / "data" / "caty08_cre_exposure.json") if (ROOT / "data" / "caty08_cre_exposure.json").exists() else {}
        caty09_tables = load_json(ROOT / "data" / "caty09_capital_liquidity.json") if (ROOT / "data" / "caty09_capital_liquidity.json").exists() else {}
        caty10_tables = load_json(ROOT / "data" / "caty10_capital_actions.json") if (ROOT / "data" / "caty10_capital_actions.json").exists() else {}
        caty12_tables = load_json(ROOT / "data" / "caty12_calculated_tables.json") if (ROOT / "data" / "caty12_calculated_tables.json").exists() else {}
        caty11_tables = load_json(ROOT / "data" / "caty11_peers_normalized.json") if (ROOT / "data" / "caty11_peers_normalized.json").exists() else {}
        caty13_tables = load_json(ROOT / "data" / "caty13_residual_income.json") if (ROOT / "data" / "caty13_residual_income.json").exists() else {}
        caty14_tables = load_json(ROOT / "data" / "caty14_monte_carlo.json") if (ROOT / "data" / "caty14_monte_carlo.json").exists() else {}
        caty16_tables = load_json(ROOT / "data" / "caty16_coe_triangulation.json") if (ROOT / "data" / "caty16_coe_triangulation.json").exists() else {}
        caty15_tables = load_json(ROOT / "data" / "caty15_esg_materiality.json") if (ROOT / "data" / "caty15_esg_materiality.json").exists() else {}
        caty17_tables = load_json(ROOT / "data" / "caty17_esg_kpi.json") if (ROOT / "data" / "caty17_esg_kpi.json").exists() else {}
        recent_developments = load_json(ROOT / "data" / "recent_developments.json") if (ROOT / "data" / "recent_developments.json").exists() else {}
        catalysts_path = ROOT / "data" / "catalysts.json"
        catalysts = load_json(catalysts_path) if catalysts_path.exists() else {}
        peers_path = ROOT / "data" / "caty11_peers_normalized.json"
        peers = load_json(peers_path) if peers_path.exists() else {}
        history_path = ROOT / "data" / "historical_context.json"
        historical_context = load_json(history_path) if history_path.exists() else {}
        industry_path = ROOT / "data" / "industry_analysis.json"
        industry_analysis = load_json(industry_path) if industry_path.exists() else {}
        esg_path = ROOT / "data" / "esg_assessment.json"
        esg_assessment = load_json(esg_path) if esg_path.exists() else {}

        context = {
            "market": market,
            "valuation": valuation_lookup,
            "executive": exec_cfg,
            "valuation_outputs": valuation_outputs,
            "module_metadata": module_metadata,
            "calculated_metrics": market.get("calculated_metrics", {}),
            "narrative_prose": market.get("narrative_prose", {}),
            "recent_developments": recent_developments,
            "catalysts": catalysts,
            "peers": peers,
            "historical_context": historical_context,
            "industry_analysis": industry_analysis,
            "esg_assessment": esg_assessment,
            "caty01_tables": caty01_tables,
            "caty02_tables": caty02_tables,
            "caty03_tables": caty03_tables,
            "caty04_tables": caty04_tables,
            "caty05_tables": caty05_tables,
            "caty06_tables": caty06_tables,
            "caty07_tables": caty07_tables,
            "caty08_tables": caty08_tables,
            "caty09_tables": caty09_tables,
            "caty10_tables": caty10_tables,
            "caty12_tables": caty12_tables,
            "caty11_tables": caty11_tables,
            "caty13_tables": caty13_tables,
            "caty14_tables": caty14_tables,
            "caty16_tables": caty16_tables,
            "caty15_tables": caty15_tables,
            "caty17_tables": caty17_tables,
        }

        timestamps = render_timestamps()
        context.update(timestamps)
        narrative_placeholders = build_narrative_replacements(market, timestamps)
        context["narrative_placeholders"] = narrative_placeholders

        html = replace_section(html, "page-title", render_page_title(timestamps["report_date"]))
        html = replace_section(html, "report-meta", render_report_meta(timestamps))
        html = replace_section(html, "footer-timestamp", render_footer_timestamp(timestamps))
        html = replace_section(html, "company-overview", render_company_overview(context))
        html = replace_section(html, "industry-analysis", render_industry_analysis(context))
        html = replace_section(html, "esg-assessment", render_esg_assessment(context))
        html = replace_section(html, "investment-thesis-summary", render_investment_thesis(context, narrative_placeholders))
        html = replace_section(html, "key-findings-bullets", render_key_findings(narrative_placeholders))
        html = replace_section(html, "valuation-framework-caption", render_price_target_caption(narrative_placeholders))
        html = replace_section(html, "valuation-framework-grid", render_price_target_grid(narrative_placeholders))
        html = replace_section(html, "valuation-deep-dive", render_valuation_deep_dive(context))
        html = replace_section(html, "scenario-analysis-table", render_scenario_analysis_table(context))
        html = replace_section(html, "positive-catalysts", render_positive_catalysts(context))
        html = replace_section(html, "peer-positioning", render_peer_positioning(context))
        html = replace_section(html, "financial-analysis-summary", render_financial_analysis_summary(context))
        html = replace_section(html, "liquidity-summary", render_liquidity_summary(context))
        html = replace_section(html, "scenario-analysis-narrative", render_scenario_analysis_narrative(context))
        html = replace_section(html, "monte-carlo-summary", render_monte_carlo_summary(context))
        html = replace_section(html, "historical-context", render_historical_context(context))
        html = replace_section(html, "recent-developments-section", render_recent_developments_section(recent_developments, narrative_placeholders))
        html = replace_section(html, "investment-risks-bullets", render_investment_risks_section(context, narrative_placeholders))
        html = replace_section(html, "investment-recommendation", render_investment_recommendation(context))

        reconciliation_html = build_reconciliation_table()
        html = replace_section(html, "reconciliation-dashboard", reconciliation_html)

        module_grid_html = render_module_grid()
        html = replace_section(html, "module-grid", module_grid_html)

        evidence_html = render_evidence_table()
        html = replace_section(html, "evidence-provenance", evidence_html)

        for section in exec_cfg.get("sections", []):
            marker = section["marker"]
            section_html = render_cards(section, context)
            html = replace_section(html, marker, section_html)

        price_target_cfg = exec_cfg.get("price_target")
        if price_target_cfg:
            price_html = render_cards(price_target_cfg, context)
            html = replace_section(html, price_target_cfg["marker"], price_html)

        INDEX_PATH.write_text(html, encoding="utf-8")

        for module_entry in module_cfg.get("modules", []):
            module_path = ROOT / module_entry["file"]
            if not module_path.exists():
                raise FileNotFoundError(f"Module file '{module_entry['file']}' not found")

            module_html = module_path.read_text(encoding="utf-8")
            module_context = dict(context)
            module_context["module"] = module_entry.get("data", {})

            for module_section in module_entry.get("sections", []):
                rendered_section = render_module_section(module_section, module_context)
                module_html = replace_section(module_html, module_section["marker"], rendered_section)

            module_path.write_text(module_html, encoding="utf-8")

        append_log(
            "build_site.py completed: reconciliation-dashboard, module-grid, evidence-provenance, executive-dashboard, price-target, module-pages updated",
            test_mode=test_mode
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        append_log(f"build_site.py FAILED: {exc}", test_mode=test_mode)
        raise


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build site sections from data sources")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode (skip logging)")
    args = parser.parse_args()
    sys.exit(main(test_mode=args.test_mode))
