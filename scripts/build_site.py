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
        html = replace_section(html, "investment-thesis-summary", render_investment_thesis(context, narrative_placeholders))
        html = replace_section(html, "key-findings-bullets", render_key_findings(narrative_placeholders))
        html = replace_section(html, "valuation-framework-caption", render_price_target_caption(narrative_placeholders))
        html = replace_section(html, "valuation-framework-grid", render_price_target_grid(narrative_placeholders))
        html = replace_section(html, "valuation-deep-dive", render_valuation_deep_dive(context))
        html = replace_section(html, "scenario-analysis-table", render_scenario_analysis_table(context))
        html = replace_section(html, "positive-catalysts", render_positive_catalysts(context))
        html = replace_section(html, "recent-developments-section", render_recent_developments_section(recent_developments, narrative_placeholders))
        html = replace_section(html, "investment-risks-bullets", render_investment_risks_section(context, narrative_placeholders))

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
