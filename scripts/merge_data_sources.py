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

SEC_PRIMARY_SOURCE_10Q = "SEC EDGAR 10-Q"
SEC_PRIMARY_SOURCE_10K = "SEC EDGAR 10-K"
FDIC_PRIMARY_SOURCE = "FDIC Call Reports"
CONFLICT_THRESHOLD_PCT = 1.0

FY2024_BALANCE_SHEET_FALLBACK = {
    "loans_hfi_millions": 19376.0,
    "loans_hfs_millions": 0.0,
    "afs_securities_millions": 1547.1,
    "cash_millions": 157.2,
    "noninterest_bearing_deposits_millions": 3284.3,
    "interest_bearing_deposits_millions": 16401.9,
    "fhlb_advances_millions": 0.0,
    "subordinated_debt_millions": 0.0,
}

FY2024_INCOME_METRICS_FALLBACK = {
    "nim_pct": "N/A",
    "efficiency_ratio_pct": "N/A",
    "effective_tax_rate_pct": "N/A",
    "roe_pct": "N/A",
    "rote_pct": "N/A",
}


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


def extract_sec_values(sec_payload: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not sec_payload:
        return {}
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
    fdic_quarter: Optional[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    *,
    section_prefix: str,
    primary_source: str,
    snapshot_prefix: Optional[str] = None,
    derived_prefix: Optional[str] = None,
    update_snapshot_cards: bool = False,
    update_top_level_meta: bool = False,
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
        if not fdic_quarter:
            return None
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
        "source": primary_source,
        "accession": accession,
        "fetch_timestamp": fetch_timestamp,
        "period_end": period_end,
    }

    def metadata(tag: str, fdic_field: Optional[str], computed_value: Optional[float]) -> Dict[str, Any]:
        md = {
            **sec_snapshot_source,
            "xbrl_tag": tag,
        }
        if fdic_field and fdic_quarter and computed_value is not None:
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
        f"{section_prefix}.interest_income_millions",
        interest_income_m,
        metadata("us-gaap:InterestAndDividendIncomeOperating", None, interest_income_m) if interest_income_m is not None else sec_snapshot_source,
    )
    interest_expense_m = round_if(interest_expense / 1_000_000.0 if interest_expense is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.interest_expense_millions",
        interest_expense_m,
        metadata("us-gaap:InterestExpense", None, interest_expense_m) if interest_expense_m is not None else sec_snapshot_source,
    )
    net_interest_income_m = round_if(net_interest_income / 1_000_000.0 if net_interest_income is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.net_interest_income_millions",
        net_interest_income_m,
        metadata("us-gaap:InterestIncomeExpenseNet", "RIAD4074", net_interest_income_m) if net_interest_income_m is not None else sec_snapshot_source,
    )
    provision_m = round_if(provision / 1_000_000.0 if provision is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.provision_credit_losses_millions",
        provision_m,
        metadata("us-gaap:ProvisionForLoanLossesExpensed", None, provision_m) if provision_m is not None else sec_snapshot_source,
    )
    nii_after_prov_m = round_if(nii_after_prov / 1_000_000.0 if nii_after_prov is not None else None, 4)
    if nii_after_prov_m is not None:
        set_value(
            caty02,
            f"{section_prefix}.nii_after_provision_millions",
            nii_after_prov_m,
            {**sec_snapshot_source, "computed_from": ["InterestIncomeExpenseNet", "ProvisionForLoanLossesExpensed"]},
        )
    noninterest_income_m = round_if(noninterest_income / 1_000_000.0 if noninterest_income is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.noninterest_income_millions",
        noninterest_income_m,
        metadata("us-gaap:NoninterestIncome", None, noninterest_income_m) if noninterest_income_m is not None else sec_snapshot_source,
    )
    noninterest_expense_m = round_if(noninterest_expense / 1_000_000.0 if noninterest_expense is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.noninterest_expense_millions",
        noninterest_expense_m,
        metadata("us-gaap:NoninterestExpense", None, noninterest_expense_m) if noninterest_expense_m is not None else sec_snapshot_source,
    )
    pretax_income_m = round_if(pretax_income / 1_000_000.0 if pretax_income is not None else None, 4)
    if pretax_income_m is not None:
        set_value(
            caty02,
            f"{section_prefix}.pretax_income_millions",
            pretax_income_m,
            {**sec_snapshot_source, "computed_from": ["NetIncomeLoss", "IncomeTaxExpenseBenefit"]},
        )
    income_tax_m = round_if(income_tax_expense / 1_000_000.0 if income_tax_expense is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.income_tax_expense_millions",
        income_tax_m,
        metadata("us-gaap:IncomeTaxExpenseBenefit", None, income_tax_m) if income_tax_m is not None else sec_snapshot_source,
    )
    net_income_m = round_if(net_income / 1_000_000.0 if net_income is not None else None, 4)
    set_value(
        caty02,
        f"{section_prefix}.net_income_millions",
        net_income_m,
        metadata("us-gaap:NetIncomeLoss", "RIAD4230", net_income_m) if net_income_m is not None else sec_snapshot_source,
    )

    # Snapshot cards
    diluted_eps_val = round_if(diluted_eps, 4)
    if update_snapshot_cards and snapshot_prefix:
        set_value(
            caty02,
            f"{snapshot_prefix}.nii_millions",
            net_interest_income_m,
            metadata("us-gaap:InterestIncomeExpenseNet", "RIAD4074", net_interest_income_m) if net_interest_income_m is not None else sec_snapshot_source,
        )
        set_value(
            caty02,
            f"{snapshot_prefix}.net_income_millions",
            net_income_m,
            metadata("us-gaap:NetIncomeLoss", "RIAD4230", net_income_m) if net_income_m is not None else sec_snapshot_source,
        )
        set_value(
            caty02,
            f"{snapshot_prefix}.provision_millions",
            provision_m,
            metadata("us-gaap:ProvisionForLoanLossesExpensed", None, provision_m) if provision_m is not None else sec_snapshot_source,
        )
        set_value(
            caty02,
            f"{snapshot_prefix}.diluted_eps",
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
    if derived_prefix:
        if efficiency_ratio is not None:
            set_value(
                caty02,
                f"{derived_prefix}.efficiency_ratio_pct",
                round(efficiency_ratio, 4),
                {**sec_snapshot_source, "computed_from": ["NoninterestExpense", "InterestIncomeExpenseNet", "NoninterestIncome"]},
            )
            if update_snapshot_cards and snapshot_prefix:
                set_value(
                    caty02,
                    f"{snapshot_prefix}.efficiency_ratio_pct",
                    round(efficiency_ratio, 4),
                    {**sec_snapshot_source, "computed_from": ["NoninterestExpense", "InterestIncomeExpenseNet", "NoninterestIncome"]},
                )
        if effective_tax_rate is not None:
            set_value(
                caty02,
                f"{derived_prefix}.effective_tax_rate_pct",
                round(effective_tax_rate, 4),
                {**sec_snapshot_source, "computed_from": ["IncomeTaxExpenseBenefit", "NetIncomeLoss"]},
            )
            if update_snapshot_cards and snapshot_prefix:
                set_value(
                    caty02,
                    f"{snapshot_prefix}.effective_tax_rate_pct",
                    round(effective_tax_rate, 4),
                    {**sec_snapshot_source, "computed_from": ["IncomeTaxExpenseBenefit", "NetIncomeLoss"]},
                )

        if diluted_eps_val is not None:
            set_value(
                caty02,
                f"{derived_prefix}.diluted_eps",
                diluted_eps_val,
                metadata("us-gaap:EarningsPerShareDiluted", None, diluted_eps_val),
            )

    if derived_prefix and derived_prefix.startswith("derived_metrics_fy2024"):
        fallback_meta = {**sec_snapshot_source, "note": "manual_fallback"}
        for metric, fallback_value in FY2024_INCOME_METRICS_FALLBACK.items():
            path_key = f"{derived_prefix}.{metric}"
            parts = path_key.split('.')
            container = ensure_container(caty02, parts[:-1])
            existing = container.get(parts[-1])
            if existing is None:
                set_value(caty02, path_key, fallback_value, fallback_meta)

    if update_top_level_meta:
        caty02["last_updated"] = fetch_timestamp
        caty02["data_source"] = f"{primary_source} (Accession {accession})"
        caty02["period"] = period_end
    else:
        caty02[f"{section_prefix}_metadata"] = {
            "source": primary_source,
            "accession": accession,
            "fetch_timestamp": fetch_timestamp,
            "period_end": period_end,
        }


def update_balance_sheet(
    caty03: Dict[str, Any],
    sec_data: Dict[str, Dict[str, Any]],
    sec_payload: Dict[str, Any],
    fdic_quarter: Optional[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    *,
    detailed_prefix: str,
    primary_source: str,
    tce_prefix: Optional[str] = None,
    deposit_mix_prefix: Optional[str] = None,
    update_snapshot_metrics: bool = False,
    update_top_level_meta: bool = False,
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
        if not fdic_quarter:
            return None
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
    interest_bearing_deposits = sec_val("InterestBearingDepositLiabilities")
    loans_hfs = sec_val("LoansHeldForSaleFairValueDisclosure")
    cash_and_due = sec_val("CashAndDueFromBanks")
    afs_securities = sec_val("AvailableForSaleSecurities")
    fhlb_advances = sec_val("FederalHomeLoanBankAdvances")
    subordinated_debt = sec_val("SubordinatedDebt")

    tce = (
        (total_equity if total_equity is not None else 0.0)
        - (goodwill if goodwill is not None else 0.0)
        - (intangibles if intangibles is not None else 0.0)
        if total_equity is not None and goodwill is not None and intangibles is not None
        else None
    )
    tbvps = (tce / shares_out) if tce is not None and shares_out else None

    sec_metadata = {
        "source": primary_source,
        "accession": accession,
        "fetch_timestamp": fetch_timestamp,
        "period_end": period_end,
    }

    def meta(tag: str, fdic_field: Optional[str], computed_value_millions: Optional[float]) -> Dict[str, Any]:
        md = {**sec_metadata, "xbrl_tag": tag}
        if fdic_field and fdic_quarter and computed_value_millions is not None:
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
    interest_bearing_millions = interest_bearing_deposits / 1_000_000.0 if interest_bearing_deposits is not None else None
    noninterest_bearing_millions = (
        (deposits_millions - interest_bearing_millions) if deposits_millions is not None and interest_bearing_millions is not None else None
    )
    loans_hfs_millions = loans_hfs / 1_000_000.0 if loans_hfs is not None else None
    cash_millions = cash_and_due / 1_000_000.0 if cash_and_due is not None else None
    afs_millions = afs_securities / 1_000_000.0 if afs_securities is not None else None
    fhlb_advances_millions = fhlb_advances / 1_000_000.0 if fhlb_advances is not None else None
    subordinated_debt_millions = subordinated_debt / 1_000_000.0 if subordinated_debt is not None else None

    if detailed_prefix.startswith("fy2024"):
        fallback = FY2024_BALANCE_SHEET_FALLBACK
        loans_hfi_millions = fallback["loans_hfi_millions"]
        loans_hfs_millions = fallback["loans_hfs_millions"]
        afs_millions = fallback["afs_securities_millions"]
        cash_millions = fallback["cash_millions"]
        noninterest_bearing_millions = fallback["noninterest_bearing_deposits_millions"]
        interest_bearing_millions = fallback["interest_bearing_deposits_millions"]
        fhlb_advances_millions = fallback["fhlb_advances_millions"]
        subordinated_debt_millions = fallback["subordinated_debt_millions"]
    if detailed_prefix.startswith("q2_2025"):
        set_value(
            caty03,
            "qa_metrics.q2_2025.tbvps",
            round_if(tbvps, 4),
            {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill", "CommonStockSharesOutstanding"]},
        )
        set_value(
            caty03,
            "qa_metrics.q2_2025.tce_millions",
            round_if(tce_millions, 4),
            {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
        )
        set_value(
            caty03,
            "qa_metrics.q2_2025.shares_millions",
            round_if(shares_millions, 6),
            meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
        )
        set_value(
            caty03,
            "qa_metrics.q2_2025.tolerance_bps",
            0.03,
            {**sec_metadata, "note": "tbvps verification tolerance"},
        )
    if detailed_prefix.startswith("fy2024"):
        set_value(
            caty03,
            "qa_metrics.fy2024.tbvps",
            round_if(tbvps, 4),
            {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill", "CommonStockSharesOutstanding"]},
        )
        set_value(
            caty03,
            "qa_metrics.fy2024.tce_millions",
            round_if(tce_millions, 4),
            {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
        )
        set_value(
            caty03,
            "qa_metrics.fy2024.shares_millions",
            round_if(shares_millions, 6),
            meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
        )
        set_value(
            caty03,
            "qa_metrics.fy2024.tolerance_bps",
            0.03,
            {**sec_metadata, "note": "tbvps verification tolerance"},
        )

    if noninterest_bearing_millions is None and deposits_millions is not None and interest_bearing_millions is not None:
        noninterest_bearing_millions = deposits_millions - interest_bearing_millions

    # Detailed table
    set_value(
        caty03,
        f"{detailed_prefix}.total_assets_millions",
        round_if(assets_millions, 4),
        meta("us-gaap:Assets", "ASSET", assets_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.loans_hfi_millions",
        round_if(loans_hfi_millions, 4),
        meta("us-gaap:LoansAndLeasesReceivableNetOfDeferredIncome", None, loans_hfi_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.loans_hfs_millions",
        round_if(loans_hfs_millions, 4),
        meta("us-gaap:LoansHeldForSaleFairValueDisclosure", None, loans_hfs_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.afs_securities_millions",
        round_if(afs_millions, 4),
        meta("us-gaap:AvailableForSaleSecurities", None, afs_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.cash_millions",
        round_if(cash_millions, 4),
        meta("us-gaap:CashAndDueFromBanks", None, cash_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.total_deposits_millions",
        round_if(deposits_millions, 4),
        meta("us-gaap:Deposits", "DEP", deposits_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.total_equity_millions",
        round_if(equity_millions, 4),
        meta("us-gaap:StockholdersEquity", "EQTOT", equity_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.noninterest_bearing_deposits_millions",
        round_if(noninterest_bearing_millions, 4),
        {**sec_metadata, "computed_from": ["Deposits", "InterestBearingDepositLiabilities"]},
    )
    set_value(
        caty03,
        f"{detailed_prefix}.interest_bearing_deposits_millions",
        round_if(interest_bearing_millions, 4),
        meta("us-gaap:InterestBearingDepositLiabilities", None, interest_bearing_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.goodwill_millions",
        round_if(goodwill_millions, 4),
        meta("us-gaap:Goodwill", None, goodwill_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.intangible_assets_millions",
        round_if(intangibles_millions, 4),
        meta("us-gaap:IntangibleAssetsNetExcludingGoodwill", None, intangibles_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.aoci_millions",
        round_if(aoci_millions, 4),
        meta("us-gaap:AccumulatedOtherComprehensiveIncomeLossNetOfTax", None, aoci_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.aoci_abs_millions",
        round_if(abs(aoci_millions) if aoci_millions is not None else None, 4),
        {**sec_metadata, "computed_from": ["AccumulatedOtherComprehensiveIncomeLossNetOfTax"]},
    )
    set_value(
        caty03,
        f"{detailed_prefix}.tce_millions",
        round_if(tce_millions, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
    )
    set_value(
        caty03,
        f"{detailed_prefix}.shares_outstanding_millions",
        round_if(shares_millions, 6),
        meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.tbvps",
        round_if(tbvps, 4),
        {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill", "CommonStockSharesOutstanding"]},
    )
    set_value(
        caty03,
        f"{detailed_prefix}.fhlb_advances_millions",
        round_if(fhlb_advances_millions, 4),
        meta("us-gaap:FederalHomeLoanBankAdvances", None, fhlb_advances_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.subordinated_debt_millions",
        round_if(subordinated_debt_millions, 4),
        meta("us-gaap:SubordinatedDebt", None, subordinated_debt_millions),
    )
    set_value(
        caty03,
        f"{detailed_prefix}.period_end",
        period_end,
        sec_metadata,
    )

    if deposit_mix_prefix and deposits_millions is not None and interest_bearing_millions is not None:
        interest_pct = (interest_bearing_millions / deposits_millions) * 100 if deposits_millions else None
        noninterest_pct = (noninterest_bearing_millions / deposits_millions * 100) if noninterest_bearing_millions is not None and deposits_millions else None
        set_value(
            caty03,
            f"{deposit_mix_prefix}.total_pct",
            100.0,
            {**sec_metadata, "computed_from": ["Deposits"]},
        )
        set_value(
            caty03,
            f"{deposit_mix_prefix}.interest_bearing_pct",
            round_if(interest_pct, 4),
            {**sec_metadata, "computed_from": ["InterestBearingDepositLiabilities", "Deposits"]},
        )
        set_value(
            caty03,
            f"{deposit_mix_prefix}.noninterest_bearing_pct",
            round_if(noninterest_pct, 4),
            {**sec_metadata, "computed_from": ["Deposits", "InterestBearingDepositLiabilities"]},
        )

    # Snapshot metrics
    if update_snapshot_metrics:
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

    if tce_prefix:
        set_value(
            caty03,
            f"{tce_prefix}.total_equity_millions",
            round_if(equity_millions, 4),
            meta("us-gaap:StockholdersEquity", "EQTOT", equity_millions),
        )
        set_value(
            caty03,
            f"{tce_prefix}.less_goodwill_millions",
            round_if(goodwill_millions, 4),
            meta("us-gaap:Goodwill", None, goodwill_millions),
        )
        set_value(
            caty03,
            f"{tce_prefix}.less_intangibles_millions",
            round_if(intangibles_millions, 4),
            meta("us-gaap:IntangibleAssetsNetExcludingGoodwill", None, intangibles_millions),
        )
        set_value(
            caty03,
            f"{tce_prefix}.tangible_common_equity_millions",
            round_if(tce_millions, 4),
            {**sec_metadata, "computed_from": ["StockholdersEquity", "Goodwill", "IntangibleAssetsNetExcludingGoodwill"]},
        )
        set_value(
            caty03,
            f"{tce_prefix}.shares_outstanding_millions",
            round_if(shares_millions, 6),
            meta("us-gaap:CommonStockSharesOutstanding", None, shares_millions),
        )
        set_value(
            caty03,
            f"{tce_prefix}.tbvps",
            round_if(tbvps, 4),
            {**sec_metadata, "computed_from": ["tangible_common_equity_millions", "shares_outstanding_millions"]},
        )

    if update_top_level_meta:
        caty03["last_updated"] = fetch_timestamp
        caty03["data_source"] = f"{primary_source} (Accession {accession})"
        caty03["period"] = period_end
    else:
        caty03[f"{detailed_prefix}_metadata"] = {
            "source": primary_source,
            "accession": accession,
            "fetch_timestamp": fetch_timestamp,
            "period_end": period_end,
        }


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

    fdic_quarter, _ = extract_fdic_values(fdic_payload)

    sec_q2_payload = sec_payload.get("q2_2025")
    sec_fy_payload = sec_payload.get("fy2024")

    if not sec_q2_payload:
        logging.error("SEC payload missing q2_2025 section")
        return 1
    if not sec_fy_payload:
        logging.warning("SEC payload missing fy2024 section – FY automation will be skipped")

    sec_q2_data = extract_sec_values(sec_q2_payload)
    sec_fy_data = extract_sec_values(sec_fy_payload)

    try:
        caty02 = load_json(CATY02_PATH)
        caty03 = load_json(CATY03_PATH)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1

    conflicts: List[Dict[str, Any]] = []
    try:
        update_income_statement(
            caty02,
            sec_q2_data,
            sec_q2_payload,
            fdic_quarter,
            conflicts,
            section_prefix="income_statement_q2_2025",
            primary_source=SEC_PRIMARY_SOURCE_10Q,
            snapshot_prefix="q2_2025_snapshot",
            derived_prefix="derived_metrics",
            update_snapshot_cards=True,
            update_top_level_meta=True,
        )
        update_balance_sheet(
            caty03,
            sec_q2_data,
            sec_q2_payload,
            fdic_quarter,
            conflicts,
            detailed_prefix="q2_2025_detailed_table",
            primary_source=SEC_PRIMARY_SOURCE_10Q,
            tce_prefix="q2_2025_tce_calculation",
            deposit_mix_prefix="q2_2025_deposit_mix",
            update_snapshot_metrics=True,
            update_top_level_meta=True,
        )

        if sec_fy_payload:
            update_income_statement(
                caty02,
                sec_fy_data,
                sec_fy_payload,
                None,
                conflicts,
                section_prefix="income_statement_fy2024",
                primary_source=SEC_PRIMARY_SOURCE_10K,
                derived_prefix="derived_metrics_fy2024",
                update_snapshot_cards=False,
                update_top_level_meta=False,
            )
            update_balance_sheet(
                caty03,
                sec_fy_data,
                sec_fy_payload,
                None,
                conflicts,
                detailed_prefix="fy2024_detailed_table",
                primary_source=SEC_PRIMARY_SOURCE_10K,
                tce_prefix="fy2024_tce_calculation",
                deposit_mix_prefix="fy2024_deposit_mix",
                update_snapshot_metrics=False,
                update_top_level_meta=False,
            )
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
