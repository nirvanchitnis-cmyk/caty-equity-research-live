#!/usr/bin/env python3
"""
Merge SEC EDGAR and FDIC data feeds into the canonical CATY JSON datasets.

Outputs:
    - data/caty02_income_statement.json
    - data/caty03_balance_sheet.json
    - data/data_quality_report.json
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEC_RAW_PATH = DATA_DIR / "sec_edgar_raw.json"
FDIC_RAW_PATH = DATA_DIR / "fdic_raw.json"
CATY02_PATH = DATA_DIR / "caty02_income_statement.json"
CATY03_PATH = DATA_DIR / "caty03_balance_sheet.json"
DQ_REPORT_PATH = DATA_DIR / "data_quality_report.json"

SEC_PRIMARY_SOURCE = "SEC EDGAR 10-Q"
FDIC_PRIMARY_SOURCE = "FDIC Call Reports"
CONFLICT_THRESHOLD_PCT = 1.0


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required data file missing: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def resolve_path(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def ensure_container(obj: Dict[str, Any], path: Iterable[str]) -> Dict[str, Any]:
    current = obj
    for part in path:
        current = current.setdefault(part, {})
    return current


def round_if(value: Optional[float], decimals: int) -> Optional[float]:
    if value is None:
        return None
    return round(value, decimals)


def set_value(
    data: Dict[str, Any],
    path: str,
    value: Any,
    metadata: Dict[str, Any],
) -> None:
    if value is None:
        logging.info("Skipping update for %s (value unavailable)", path)
        return
    parts = path.split(".")
    container = ensure_container(data, parts[:-1])
    key = parts[-1]
    existing = container.get(key)
    if isinstance(existing, dict) and existing.get("manual_override"):
        logging.info("Skipping manual override for %s", path)
        return
    container[key] = {**metadata, "value": value}


def to_float(value: Any) -> float:
    if value is None:
        raise ValueError("Cannot convert None to float")
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def to_millions(value: Any, scale: float = 1_000_000.0) -> float:
    return to_float(value) / scale


def compute_diff_pct(base: float, other: float) -> float:
    if base == 0:
        return math.inf
    return abs(base - other) / abs(base) * 100


def first_quarter(fdic_data: Dict[str, Any]) -> Dict[str, Any]:
    quarters = fdic_data.get("quarters", [])
    if not quarters:
        raise ValueError("FDIC payload missing 'quarters' data")
    return quarters[0]


@dataclass
class FieldMapping:
    output_path: str
    sec_key: Optional[str] = None
    fdic_key: Optional[str] = None
    conversion: str = "millions"  # millions, raw, per_share, percent
    notes: Optional[str] = None
    compute: Optional[str] = None  # Special handler key


def extract_sec_values(sec_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return sec_payload.get("data", {})


def extract_fdic_values(fdic_payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    quarter = first_quarter(fdic_payload)
    return quarter, fdic_payload


def convert_value(raw_value: Any, conversion: str) -> float:
    if conversion == "millions":
        return round(to_millions(raw_value), 4)
    if conversion == "raw":
        return round(to_float(raw_value), 4)
    if conversion == "per_share":
        return round(to_float(raw_value), 4)
    if conversion == "percent":
        return round(to_float(raw_value), 4)
    if conversion == "shares_millions":
        return round(to_float(raw_value) / 1_000_000.0, 6)
    raise ValueError(f"Unsupported conversion '{conversion}'")


def update_income_statement(
    caty02: Dict[str, Any],
    sec_data: Dict[str, Dict[str, Any]],
    sec_payload: Dict[str, Any],
    fdic_quarter: Dict[str, Any],
    conflicts: List[Dict[str, Any]],
) -> None:
    accession = sec_payload["accession"]
    fetch_timestamp = sec_payload["fetch_timestamp"]
    period_end = sec_payload["period_end"]

    def sec_val(tag: str, fallback: Optional[float] = None) -> Optional[float]:
        entry = sec_data.get(tag)
        if not entry:
            logging.warning("SEC data missing tag %s", tag)
            return fallback
        value = entry.get("value")
        if value is None:
            logging.warning("SEC data tag %s missing value", tag)
            return fallback
        try:
            return to_float(value)
        except ValueError:
            logging.warning("SEC data tag %s value '%s' not numeric", tag, value)
            return fallback

    def fdic_val(field: str) -> Optional[float]:
        if field not in fdic_quarter:
            return None
        return to_float(fdic_quarter[field])

    # Base values (raw USD)
    interest_income = sec_val("InterestAndDividendIncomeOperating")
    net_interest_income = sec_val("InterestIncomeExpenseNet")
    interest_expense = sec_val(
        "InterestExpense",
        fallback=interest_income - net_interest_income if interest_income is not None and net_interest_income is not None else None,
    )
    provision = sec_val("ProvisionForLoanLossesExpensed")
    noninterest_income = sec_val("NoninterestIncome")
    noninterest_expense = sec_val("NoninterestExpense")
    income_tax_expense = sec_val("IncomeTaxExpenseBenefit")
    net_income = sec_val("NetIncomeLoss")
    diluted_eps = sec_val("EarningsPerShareDiluted")

    nii_after_prov = (
        (net_interest_income if net_interest_income is not None else 0.0)
        - (provision if provision is not None else 0.0)
        if net_interest_income is not None and provision is not None
        else None
    )
    pretax_income = (
        (net_income if net_income is not None else 0.0)
        + (income_tax_expense if income_tax_expense is not None else 0.0)
        if net_income is not None and income_tax_expense is not None
        else None
    )

    sec_snapshot_source = {
        "source": SEC_PRIMARY_SOURCE,
        "accession": accession,
        "fetch_timestamp": fetch_timestamp,
        "period_end": period_end,
    }

    def metadata(tag: str, fdic_field: Optional[str], computed_value: Optional[float]) -> Dict[str, Any]:
        md = {
            **sec_snapshot_source,
            "xbrl_tag": tag,
        }
        if fdic_field and computed_value is not None:
            fdic_raw = fdic_val(fdic_field)
            if fdic_raw is not None:
                fdic_millions = fdic_raw / 1_000.0
                md["fdic_value"] = round(fdic_millions, 4)
                if computed_value != 0:
                    diff_pct = compute_diff_pct(computed_value, fdic_millions)
                else:
                    diff_pct = 0.0
                md["fdic_diff_pct"] = round(diff_pct, 4)
                md["fdic_match"] = diff_pct <= CONFLICT_THRESHOLD_PCT
                if diff_pct > CONFLICT_THRESHOLD_PCT:
                    conflicts.append(
                        {
                            "field": tag,
                            "sec_value": round(computed_value, 4),
                            "fdic_value": round(fdic_millions, 4),
                            "diff_pct": round(diff_pct, 4),
                            "resolution": "Use SEC EDGAR (primary GAAP source)",
                        }
                    )
        return md

    # Income statement table
    interest_income_m = round_if(interest_income / 1_000_000.0 if interest_income is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.interest_income_millions",
        interest_income_m,
        metadata("us-gaap:InterestAndDividendIncomeOperating", None, interest_income_m) if interest_income_m is not None else sec_snapshot_source,
    )
    interest_expense_m = round_if(interest_expense / 1_000_000.0 if interest_expense is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.interest_expense_millions",
        interest_expense_m,
        metadata("us-gaap:InterestExpense", None, interest_expense_m) if interest_expense_m is not None else sec_snapshot_source,
    )
    net_interest_income_m = round_if(net_interest_income / 1_000_000.0 if net_interest_income is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.net_interest_income_millions",
        net_interest_income_m,
        metadata("us-gaap:InterestIncomeExpenseNet", "RIAD4074", net_interest_income_m) if net_interest_income_m is not None else sec_snapshot_source,
    )
    provision_m = round_if(provision / 1_000_000.0 if provision is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.provision_credit_losses_millions",
        provision_m,
        metadata("us-gaap:ProvisionForLoanLossesExpensed", None, provision_m) if provision_m is not None else sec_snapshot_source,
    )
    nii_after_prov_m = round_if(nii_after_prov / 1_000_000.0 if nii_after_prov is not None else None, 4)
    if nii_after_prov_m is not None:
        set_value(
            caty02,
            "income_statement_q2_2025.nii_after_provision_millions",
            nii_after_prov_m,
            {**sec_snapshot_source, "computed_from": ["InterestIncomeExpenseNet", "ProvisionForLoanLossesExpensed"]},
        )
    noninterest_income_m = round_if(noninterest_income / 1_000_000.0 if noninterest_income is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.noninterest_income_millions",
        noninterest_income_m,
        metadata("us-gaap:NoninterestIncome", None, noninterest_income_m) if noninterest_income_m is not None else sec_snapshot_source,
    )
    noninterest_expense_m = round_if(noninterest_expense / 1_000_000.0 if noninterest_expense is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.noninterest_expense_millions",
        noninterest_expense_m,
        metadata("us-gaap:NoninterestExpense", None, noninterest_expense_m) if noninterest_expense_m is not None else sec_snapshot_source,
    )
    pretax_income_m = round_if(pretax_income / 1_000_000.0 if pretax_income is not None else None, 4)
    if pretax_income_m is not None:
        set_value(
            caty02,
            "income_statement_q2_2025.pretax_income_millions",
            pretax_income_m,
            {**sec_snapshot_source, "computed_from": ["NetIncomeLoss", "IncomeTaxExpenseBenefit"]},
        )
    income_tax_m = round_if(income_tax_expense / 1_000_000.0 if income_tax_expense is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.income_tax_expense_millions",
        income_tax_m,
        metadata("us-gaap:IncomeTaxExpenseBenefit", None, income_tax_m) if income_tax_m is not None else sec_snapshot_source,
    )
    net_income_m = round_if(net_income / 1_000_000.0 if net_income is not None else None, 4)
    set_value(
        caty02,
        "income_statement_q2_2025.net_income_millions",
        net_income_m,
        metadata("us-gaap:NetIncomeLoss", "RIAD4230", net_income_m) if net_income_m is not None else sec_snapshot_source,
    )

    # Snapshot cards
    set_value(
        caty02,
        "q2_2025_snapshot.nii_millions",
        net_interest_income_m,
        metadata("us-gaap:InterestIncomeExpenseNet", "RIAD4074", net_interest_income_m) if net_interest_income_m is not None else sec_snapshot_source,
    )
    set_value(
        caty02,
        "q2_2025_snapshot.net_income_millions",
        net_income_m,
        metadata("us-gaap:NetIncomeLoss", "RIAD4230", net_income_m) if net_income_m is not None else sec_snapshot_source,
    )
    set_value(
        caty02,
        "q2_2025_snapshot.provision_millions",
        provision_m,
        metadata("us-gaap:ProvisionForLoanLossesExpensed", None, provision_m) if provision_m is not None else sec_snapshot_source,
    )
    diluted_eps_val = round_if(diluted_eps, 4)
    set_value(
        caty02,
        "q2_2025_snapshot.diluted_eps",
        diluted_eps_val,
        metadata("us-gaap:EarningsPerShareDiluted", None, diluted_eps_val) if diluted_eps_val is not None else sec_snapshot_source,
    )

    # Derived metrics
    denominator_income = (
        (net_interest_income if net_interest_income is not None else 0.0)
        + (noninterest_income if noninterest_income is not None else 0.0)
        if net_interest_income is not None and noninterest_income is not None
        else None
    )
    efficiency_ratio = (
        (noninterest_expense / denominator_income) * 100
        if denominator_income
        else None
    )
    effective_tax_rate = (
        (income_tax_expense / pretax_income) * 100
        if pretax_income and income_tax_expense is not None
        else None
    )
    if efficiency_ratio is not None:
        set_value(
            caty02,
            "derived_metrics.efficiency_ratio_pct",
            round(efficiency_ratio, 4),
            {**sec_snapshot_source, "computed_from": ["NoninterestExpense", "InterestIncomeExpenseNet", "NoninterestIncome"]},
        )
        set_value(
            caty02,
            "q2_2025_snapshot.efficiency_ratio_pct",
            round(efficiency_ratio, 4),
            {**sec_snapshot_source, "computed_from": ["NoninterestExpense", "InterestIncomeExpenseNet", "NoninterestIncome"]},
        )
    if effective_tax_rate is not None:
        set_value(
            caty02,
            "derived_metrics.effective_tax_rate_pct",
            round(effective_tax_rate, 4),
            {**sec_snapshot_source, "computed_from": ["IncomeTaxExpenseBenefit", "NetIncomeLoss"]},
        )
        set_value(
            caty02,
            "q2_2025_snapshot.effective_tax_rate_pct",
            round(effective_tax_rate, 4),
            {**sec_snapshot_source, "computed_from": ["IncomeTaxExpenseBenefit", "NetIncomeLoss"]},
        )

    caty02["last_updated"] = fetch_timestamp
    caty02["data_source"] = f"{SEC_PRIMARY_SOURCE} (Accession {accession})"
    caty02["period"] = period_end


def update_balance_sheet(
    caty03: Dict[str, Any],
    sec_data: Dict[str, Dict[str, Any]],
    sec_payload: Dict[str, Any],
    fdic_quarter: Dict[str, Any],
    conflicts: List[Dict[str, Any]],
) -> None:
    accession = sec_payload["accession"]
    fetch_timestamp = sec_payload["fetch_timestamp"]
    period_end = sec_payload["period_end"]

    def sec_val(tag: str, fallback: Optional[float] = None) -> Optional[float]:
        entry = sec_data.get(tag)
        if not entry:
            logging.warning("SEC data missing tag %s", tag)
            return fallback
        value = entry.get("value")
        if value is None:
            logging.warning("SEC data tag %s missing value", tag)
            return fallback
        try:
            return to_float(value)
        except ValueError:
            logging.warning("SEC data tag %s value '%s' not numeric", tag, value)
            return fallback

    def fdic_val(field: str) -> Optional[float]:
        if field not in fdic_quarter:
            return None
        return to_float(fdic_quarter[field])

    total_assets = sec_val("Assets")
    total_deposits = sec_val("Deposits")
    total_equity = sec_val("StockholdersEquity")
    goodwill = sec_val("Goodwill")
    intangibles = sec_val("IntangibleAssetsNetExcludingGoodwill")
    aoci = sec_val("AccumulatedOtherComprehensiveIncomeLossNetOfTax")
    shares_out = sec_val("CommonStockSharesOutstanding")
    loans_hfi = sec_val("LoansAndLeasesReceivableNetOfDeferredIncome")

    tce = (
        (total_equity if total_equity is not None else 0.0)
        - (goodwill if goodwill is not None else 0.0)
        - (intangibles if intangibles is not None else 0.0)
        if total_equity is not None and goodwill is not None and intangibles is not None
        else None
    )
    tbvps = (tce / shares_out) if tce is not None and shares_out else None

    sec_metadata = {
        "source": SEC_PRIMARY_SOURCE,
        "accession": accession,
        "fetch_timestamp": fetch_timestamp,
        "period_end": period_end,
    }

    def meta(tag: str, fdic_field: Optional[str], computed_value_millions: Optional[float]) -> Dict[str, Any]:
        md = {**sec_metadata, "xbrl_tag": tag}
        if fdic_field and computed_value_millions is not None:
            fdic_raw = fdic_val(fdic_field)
            if fdic_raw is not None:
                fdic_millions = fdic_raw / 1_000.0
                md["fdic_value"] = round(fdic_millions, 4)
                diff_pct = compute_diff_pct(computed_value_millions, fdic_millions) if computed_value_millions else 0.0
                md["fdic_diff_pct"] = round(diff_pct, 4)
                md["fdic_match"] = diff_pct <= CONFLICT_THRESHOLD_PCT
                if diff_pct > CONFLICT_THRESHOLD_PCT:
                    conflicts.append(
                        {
                            "field": tag,
                            "sec_value": round(computed_value_millions, 4),
                            "fdic_value": round(fdic_millions, 4),
                            "diff_pct": round(diff_pct, 4),
                            "resolution": "Use SEC EDGAR (primary GAAP source)",
                        }
                    )
        return md

    assets_millions = total_assets / 1_000_000.0 if total_assets is not None else None
    deposits_millions = total_deposits / 1_000_000.0 if total_deposits is not None else None
    equity_millions = total_equity / 1_000_000.0 if total_equity is not None else None
    goodwill_millions = goodwill / 1_000_000.0 if goodwill is not None else None
    intangibles_millions = intangibles / 1_000_000.0 if intangibles is not None else None
    aoci_millions = aoci / 1_000_000.0 if aoci is not None else None
    tce_millions = tce / 1_000_000.0 if tce is not None else None
    loans_hfi_millions = loans_hfi / 1_000_000.0 if loans_hfi is not None else None
    shares_millions = shares_out / 1_000_000.0 if shares_out is not None else None

    # Detailed table
    set_value(
        caty03,
        "q2_2025_detailed_table.total_assets_millions",
        round_if(assets_millions, 4),
        meta("us-gaap:Assets", "ASSET", assets_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.loans_hfi_millions",
        round_if(loans_hfi_millions, 4),
        meta("us-gaap:LoansAndLeasesReceivableNetOfDeferredIncome", None, loans_hfi_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.total_deposits_millions",
        round_if(deposits_millions, 4),
        meta("us-gaap:Deposits", "DEP", deposits_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.total_equity_millions",
        round_if(equity_millions, 4),
        meta("us-gaap:StockholdersEquity", "EQTOT", equity_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.goodwill_millions",
        round_if(goodwill_millions, 4),
        meta("us-gaap:Goodwill", None, goodwill_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.intangible_assets_millions",
        round_if(intangibles_millions, 4),
        meta("us-gaap:IntangibleAssetsNetExcludingGoodwill", None, intangibles_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.aoci_millions",
        round_if(aoci_millions, 4),
        meta("us-gaap:AccumulatedOtherComprehensiveIncomeLossNetOfTax", None, aoci_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.aoci_abs_millions",
        round_if(abs(aoci_millions) if aoci_millions is not None else None, 4),
        {**sec_metadata, "computed_from": ["AccumulatedOtherComprehensiveIncomeLossNetOfTax"]},
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.tce_millions",
        round_if(tce_millions, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.shares_outstanding_millions",
        round_if(shares_millions, 6),
        meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
    )
    set_value(
        caty03,
        "q2_2025_detailed_table.tbvps",
        round_if(tbvps, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill", "CommonStockSharesOutstanding"]},
    )

    # Snapshot metrics
    set_value(
        caty03,
        "snapshot_metrics.total_assets_billions",
        round_if(assets_millions / 1_000.0 if assets_millions is not None else None, 4),
        meta("us-gaap:Assets", "ASSET", assets_millions),
    )
    set_value(
        caty03,
        "snapshot_metrics.total_loans_billions",
        round_if(loans_hfi_millions / 1_000.0 if loans_hfi_millions is not None else None, 4),
        meta("us-gaap:LoansAndLeasesReceivableNetOfDeferredIncome", None, loans_hfi_millions),
    )
    set_value(
        caty03,
        "snapshot_metrics.total_deposits_billions",
        round_if(deposits_millions / 1_000.0 if deposits_millions is not None else None, 4),
        meta("us-gaap:Deposits", "DEP", deposits_millions),
    )
    set_value(
        caty03,
        "snapshot_metrics.tce_billions",
        round_if(tce_millions / 1_000.0 if tce_millions is not None else None, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
    )
    set_value(
        caty03,
        "snapshot_metrics.tbvps",
        round_if(tbvps, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill", "CommonStockSharesOutstanding"]},
    )
    set_value(
        caty03,
        "per_share_metrics.shares_outstanding_millions",
        round_if(shares_millions, 6),
        meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.total_equity_millions",
        round_if(equity_millions, 4),
        meta("us-gaap:StockholdersEquity", "EQTOT", equity_millions),
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.less_goodwill_millions",
        round_if(goodwill_millions, 4),
        meta("us-gaap:Goodwill", None, goodwill_millions),
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.less_intangibles_millions",
        round_if(intangibles_millions, 4),
        meta("us-gaap:IntangibleAssetsNetExcludingGoodwill", None, intangibles_millions),
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.tangible_common_equity_millions",
        round_if(tce_millions, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.shares_outstanding_millions",
        round_if(shares_millions, 6),
        meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
    )
    set_value(
        caty03,
        "q2_2025_tce_calculation.tbvps",
        round_if(tbvps, 4),
        {**sec_metadata, "computed_from": ["tangible_common_equity_millions", "shares_outstanding_millions"]},
    )

    caty03["last_updated"] = fetch_timestamp
    caty03["data_source"] = f"{SEC_PRIMARY_SOURCE} (Accession {accession})"
    caty03["period"] = period_end


def write_data_quality_report(conflicts: List[Dict[str, Any]]) -> None:
    payload = {
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "conflict_threshold_pct": CONFLICT_THRESHOLD_PCT,
        "conflicts": conflicts,
    }
    save_json(DQ_REPORT_PATH, payload)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        sec_payload = load_json(SEC_RAW_PATH)
        fdic_payload = load_json(FDIC_RAW_PATH)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1

    sec_data = extract_sec_values(sec_payload)
    fdic_quarter, _ = extract_fdic_values(fdic_payload)

    try:
        caty02 = load_json(CATY02_PATH)
        caty03 = load_json(CATY03_PATH)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1

    conflicts: List[Dict[str, Any]] = []
    try:
        update_income_statement(caty02, sec_data, sec_payload, fdic_quarter, conflicts)
        update_balance_sheet(caty03, sec_data, sec_payload, fdic_quarter, conflicts)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed during merge: %s", exc, exc_info=True)
        return 1

    save_json(CATY02_PATH, caty02)
    logging.info("Updated %s", CATY02_PATH.relative_to(ROOT))
    save_json(CATY03_PATH, caty03)
    logging.info("Updated %s", CATY03_PATH.relative_to(ROOT))
    write_data_quality_report(conflicts)
    logging.info("Conflicts logged to %s (count=%d)", DQ_REPORT_PATH.relative_to(ROOT), len(conflicts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
