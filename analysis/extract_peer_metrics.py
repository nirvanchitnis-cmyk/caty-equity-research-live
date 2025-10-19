from __future__ import annotations

import gzip
import math
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, List

import pandas as pd

# Namespaces used in inline XBRL
IX = '{http://www.xbrl.org/2013/inlineXBRL}'
XBRLI = '{http://www.xbrl.org/2003/instance}'

INTANGIBLE_TAG_CANDIDATES = [
    'us-gaap:IntangibleAssetsNetExcludingGoodwill',
    'us-gaap:IntangibleAssetsNet',
    'us-gaap:FiniteLivedIntangibleAssetsNet',
    'us-gaap:OtherIntangibleAssetsNet',
    'us-gaap:IdentifiableIntangibleAssetsNet',
    'us-gaap:IntangibleAssetsNetIncludingGoodwill',
]

NET_INCOME_TAGS = [
    'us-gaap:NetIncomeLoss',
    'us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic',
    'us-gaap:NetIncomeLossAvailableToCommonStockholdersDiluted',
]

SHARE_TAGS = [
    'dei:EntityCommonStockSharesOutstanding',
    'us-gaap:CommonStockSharesOutstanding',
    'us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding',
    'us-gaap:WeightedAverageNumberOfDilutedSharesOutstandingBasicAndDiluted',
]

EQUITY_TAGS = [
    'us-gaap:StockholdersEquity',
    'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
    'us-gaap:LiabilitiesAndStockholdersEquity',
]
GOODWILL_TAG = 'us-gaap:Goodwill'

NUMBER_RE = re.compile(r'^-?\$?\(?[\d,]+(?:\.\d+)?\)?$')

@dataclass
class Context:
    id: str
    instant: Optional[str]
    start: Optional[str]
    end: Optional[str]
    has_segment: bool
    members: Tuple[str, ...]


@dataclass
class FactValue:
    value: Decimal
    fact_id: Optional[str]
    unit: Optional[str]
    scale: Optional[int]
    decimals: Optional[str]


def load_contexts(root: ET.Element) -> Dict[str, Context]:
    contexts: Dict[str, Context] = {}
    for ctx in root.findall(f'.//{XBRLI}context'):
        cid = ctx.attrib['id']
        period = ctx.find(f'{XBRLI}period')
        instant_el = period.find(f'{XBRLI}instant') if period is not None else None
        start_el = period.find(f'{XBRLI}startDate') if period is not None else None
        end_el = period.find(f'{XBRLI}endDate') if period is not None else None
        segment = ctx.find(f'{XBRLI}entity/{XBRLI}segment')
        members: List[str] = []
        if segment is not None:
            for child in segment:
                # explicitMember text includes namespace prefix; retain full qname for traceability
                if child.tag.endswith('explicitMember') and child.text:
                    members.append(child.text)
                elif child.tag.endswith('typedMember'):
                    # typed members store value inside nested element; capture tag name for identification
                    inner = next(iter(child), None)
                    if inner is not None:
                        members.append(f"typed:{inner.tag}")

        contexts[cid] = Context(
            id=cid,
            instant=instant_el.text if instant_el is not None else None,
            start=start_el.text if start_el is not None else None,
            end=end_el.text if end_el is not None else None,
            has_segment=segment is not None and len(segment) > 0,
            members=tuple(members),
        )
    return contexts


def build_value_index(root: ET.Element) -> Dict[str, Dict[str, FactValue]]:
    index: Dict[str, Dict[str, FactValue]] = {}
    for elem in root.findall(f'.//{IX}nonFraction'):
        name = elem.attrib.get('name')
        ctx = elem.attrib.get('contextRef')
        text = (elem.text or '').strip()
        if not name or not ctx or not text:
            continue
        cleaned = text.replace(',', '').replace('$', '')
        cleaned = cleaned.replace('(', '-').replace(')', '')
        # Handle optional sign attribute which sometimes overrides textual sign
        sign = elem.attrib.get('sign')
        if sign == '-':
            cleaned = '-' + cleaned.lstrip('-')

        try:
            value = Decimal(cleaned)
        except Exception:
            continue

        scale_attr = elem.attrib.get('scale')
        scale_int: Optional[int] = None
        if scale_attr:
            try:
                scale_int = int(scale_attr)
                value *= Decimal(10) ** scale_int
            except Exception:
                scale_int = None

        index.setdefault(name, {})[ctx] = FactValue(
            value=value,
            fact_id=elem.attrib.get('id'),
            unit=elem.attrib.get('unitRef'),
            scale=scale_int,
            decimals=elem.attrib.get('decimals'),
        )
    return index


def pick_duration_context(contexts: Dict[str, Context], end_date: str) -> Optional[str]:
    # Prefer most recent duration ending on end_date with no segment
    durations = [
        ctx for ctx in contexts.values()
        if ctx.end == end_date and ctx.start is not None and not ctx.has_segment
    ]
    if not durations:
        return None
    scored = []
    for ctx in durations:
        try:
            start_dt = datetime.fromisoformat(ctx.start)
            end_dt = datetime.fromisoformat(ctx.end)
            span = (end_dt - start_dt).days
        except Exception:
            span = 0
        # Aim for quarterly duration (~90 days); use absolute deviation as primary key
        score = abs(span - 90)
        scored.append((score, -span, ctx.start or '', ctx.id))
    scored.sort()
    return scored[0][3]


def get_value(value_index: Dict[str, Dict[str, FactValue]], tag: str, context: Optional[str]) -> Optional[Decimal]:
    if context is None:
        return None
    fact = value_index.get(tag, {}).get(context)
    if fact is None:
        return None
    return fact.value


def get_fact(value_index: Dict[str, Dict[str, FactValue]], tag: str, context: Optional[str]) -> Optional[FactValue]:
    if context is None:
        return None
    return value_index.get(tag, {}).get(context)


def parse_number(cell) -> Optional[Decimal]:
    if isinstance(cell, (int, float)) and not math.isnan(cell):
        return Decimal(str(cell))
    if isinstance(cell, str):
        text = cell.strip()
        if not text or text in {'.', '—', '-'}:
            return None
        text = text.replace('\xa0', ' ')
        cleaned = text.replace(',', '').replace('$', '')
        cleaned = cleaned.replace('(', '-').replace(')', '')
        if NUMBER_RE.match(cleaned):
            try:
                return Decimal(cleaned)
            except Exception:
                return None
    return None


def read_html_tables(path: Path, match: Optional[str]) -> Iterable[pd.DataFrame]:
    if path.suffix == '.gz':
        from io import BytesIO
        with gzip.open(path, 'rb') as fh:
            data = fh.read()
        source = BytesIO(data)
    else:
        source = path
    if match is None:
        return pd.read_html(source, flavor='lxml')
    return pd.read_html(source, match=match, flavor='lxml')


def normalize_label(label: str) -> str:
    return re.sub(r'[^a-z0-9]', '', label.lower())


def extract_loan_totals(
    html_path: Path,
    contexts: Dict[str, Context],
    value_index: Dict[str, Dict[str, FactValue]],
) -> Tuple[Decimal, Decimal, Optional[str], Optional[str], Optional[str], Optional[str]]:
    loan_tag_candidates = [
        'us-gaap:FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLoss',
        'us-gaap:LoansReceivableHeldForInvestmentFairValueDisclosure',
        'us-gaap:LoansReceivableNet',
        'us-gaap:LoansReceivable',
    ]

    def is_total_loans_context(ctx: Context) -> bool:
        if not ctx.members:
            return True
        text = ' '.join(ctx.members).lower()
        return 'totalloan' in text or ('total' in text and 'loan' in text and 'portfolio' not in text)

    def is_cre_context(ctx: Context) -> bool:
        text = ' '.join(ctx.members).lower()
        return 'commercial' in text and ('realestate' in text or 'cre' in text)

    for tag in loan_tag_candidates:
        facts = value_index.get(tag)
        if not facts:
            continue

        totals: Dict[str, Tuple[str, Decimal]] = {}
        cre_values: Dict[str, Tuple[str, Decimal]] = {}

        for ctx_id, fact in facts.items():
            ctx = contexts.get(ctx_id)
            if ctx is None or ctx.instant is None:
                continue
            amount = fact.value
            if is_total_loans_context(ctx):
                entry = totals.get(ctx.instant)
                if entry is None or amount > entry[1]:
                    totals[ctx.instant] = (ctx_id, amount)
            if is_cre_context(ctx):
                entry = cre_values.get(ctx.instant)
                if entry is None or amount > entry[1]:
                    cre_values[ctx.instant] = (ctx_id, amount)

        if not totals or not cre_values:
            continue

        latest_date = max(totals.keys())
        total_ctx, total_amount = totals[latest_date]
        cre_entry = cre_values.get(latest_date)
        if cre_entry is None:
            # fall back to most recent CRE value before latest_date
            prior_dates = [d for d in cre_values.keys() if d <= latest_date]
            if not prior_dates:
                continue
            use_date = max(prior_dates)
            cre_ctx, cre_amount = cre_values[use_date]
        else:
            cre_ctx, cre_amount = cre_entry

        if total_amount > 0 and cre_amount > 0:
            return total_amount, cre_amount, total_ctx, cre_ctx, tag, tag

    # Fallback: derive CRE from portfolio percentages if available (e.g., HAFC)
    percentage_tags = [tag for tag in value_index.keys() if 'PercentageOfPortfolioSegmentLoansToTotalLoans' in tag]
    if percentage_tags:
        total_amount = None
        latest_date = None
        total_tags = [
            'us-gaap:LoansReceivableFairValueDisclosure',
            'us-gaap:LoansReceivableNet',
            'us-gaap:LoansReceivable',
        ]

        for tag in total_tags:
            for ctx_id, fact in value_index.get(tag, {}).items():
                ctx = contexts.get(ctx_id)
                if ctx is None or ctx.instant is None:
                    continue
                amount = fact.value
                if amount <= 0:
                    continue
                if ctx.members:
                    continue
                if latest_date is None or ctx.instant > latest_date:
                    latest_date = ctx.instant
                    total_amount = amount
                elif ctx.instant == latest_date and (total_amount is None or amount > total_amount):
                    total_amount = amount

        if total_amount is not None and latest_date is not None:
            cre_pct = None
            cre_ctx_id = None
            cre_tag_name = None
            for tag in percentage_tags:
                for ctx_id, fact in value_index.get(tag, {}).items():
                    ctx = contexts.get(ctx_id)
                    if ctx is None or ctx.instant != latest_date:
                        continue
                    amount = fact.value
                    text = ' '.join(ctx.members).lower()
                    if 'realestate' in text and ('portfoliosegment' in text or 'cre' in text):
                        cre_pct = amount
                        cre_ctx_id = ctx_id
                        cre_tag_name = tag
                        break
                if cre_pct is not None:
                    break

            if cre_pct is not None and cre_pct > 0:
                total_ctx_id = None
                for tag in total_tags:
                    for ctx_id, fact in value_index.get(tag, {}).items():
                        ctx = contexts.get(ctx_id)
                        if ctx is None or ctx.instant != latest_date or ctx.members:
                            continue
                        if fact.value == total_amount:
                            total_ctx_id = ctx_id
                            total_tag_name = tag
                            break
                    else:
                        continue
                    break
                else:
                    total_ctx_id = None
                    total_tag_name = None

                return total_amount, total_amount * cre_pct, total_ctx_id, cre_ctx_id, total_tag_name, cre_tag_name

    # Fallback to HTML table extraction if tagged data unavailable
    try:
        tables = read_html_tables(html_path, match='Loans held-for-investment')
    except ValueError:
        try:
            tables = read_html_tables(html_path, match='Loans receivable')
        except ValueError:
            tables = read_html_tables(html_path, match=None)

    for table_idx, table in enumerate(tables):
        table = table.fillna('')
        rows = [''.join(str(cell).strip() for cell in table.iloc[i, :3]) for i in range(len(table))]
        normalized_rows = [normalize_label(row) for row in rows]

        # Look for loan table with total loans and CRE categories
        has_loans = any('totalloan' in row or 'grossloan' in row for row in normalized_rows)
        has_cre = any('commercial' in row and 'real' in row for row in normalized_rows) or any('cre' in row for row in normalized_rows)

        if has_loans or has_cre:
            total_loans = None
            total_cre = None
            cre_components = []

            for idx, row_label in enumerate(rows):
                label_norm = normalize_label(row_label)

                # Total loans patterns
                if any(pattern in label_norm for pattern in ['totalloansheldforinvestment', 'totalloansheldfor investment', 'totalloans', 'grossloans']):
                    values = [parse_number(cell) for cell in table.iloc[idx]]
                    values = [v for v in values if v is not None and v > 0]
                    if values:
                        total_loans = values[0]

                # CRE total (direct)
                if 'totalcommercialrealestate' in label_norm or 'totalcre' in label_norm:
                    values = [parse_number(cell) for cell in table.iloc[idx]]
                    values = [v for v in values if v is not None and v > 0]
                    if values:
                        total_cre = values[0]

                # CRE components (sum if total not found)
                if any(pattern in label_norm for pattern in ['construction', 'multifamily', 'nonfarmnonresidential', 'commercialrealestate']):
                    if 'total' not in label_norm:  # Avoid double-counting totals
                        values = [parse_number(cell) for cell in table.iloc[idx]]
                        values = [v for v in values if v is not None and v > 0]
                        if values:
                            cre_components.append(values[0])

            # If no direct CRE total, sum components
            if total_cre is None and cre_components:
                total_cre = sum(cre_components)

            if total_loans is not None and total_cre is not None and total_cre > 0:
                return total_loans, total_cre, None, None, None, None

    raise ValueError(f'Unable to locate loan totals in HTML (checked {len(tables) if "tables" in locals() else 0} tables)')


def load_root(path: Path) -> ET.Element:
    if path.suffix == '.gz':
        with gzip.open(path, 'rb') as fh:
            data = fh.read()
        return ET.fromstring(data)
    return ET.parse(path).getroot()


def calculate_peer_metrics(html_path: Path) -> Dict[str, Decimal]:
    root = load_root(html_path)
    contexts = load_contexts(root)
    values = build_value_index(root)

    def select_equity_contexts() -> Tuple[str, str, Decimal, str, str, Decimal]:
        preferred_tags = [
            'us-gaap:StockholdersEquity',
            'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
            'us-gaap:LiabilitiesAndStockholdersEquity',
        ]

        for tag in preferred_tags:
            grouped: Dict[str, list[Tuple[str, Decimal]]] = {}
            for ctx_id, fact in values.get(tag, {}).items():
                ctx = contexts.get(ctx_id)
                if ctx is None or ctx.has_segment or ctx.instant is None:
                    continue
                amount = fact.value
                if amount <= 0:
                    continue
                grouped.setdefault(ctx.instant, []).append((ctx_id, amount))

            if not grouped:
                continue

            sorted_dates = sorted(grouped.keys())
            latest_date = sorted_dates[-1]
            latest_ctx, latest_amount = max(grouped[latest_date], key=lambda item: item[1])

            prior_dates = [d for d in sorted_dates if d < latest_date]
            if not prior_dates:
                continue
            prior_date = prior_dates[-1]
            prior_ctx, prior_amount = max(grouped[prior_date], key=lambda item: item[1])
            return latest_date, latest_ctx, latest_amount, tag, prior_ctx, prior_amount

        raise ValueError('Unable to fetch stockholders equity values')

    latest_date, latest_ctx, stock_latest, equity_tag, prior_ctx, stock_prior = select_equity_contexts()
    prior_date = contexts[prior_ctx].instant

    goodwill_latest = get_value(values, GOODWILL_TAG, latest_ctx) or Decimal('0')
    goodwill_prior = get_value(values, GOODWILL_TAG, prior_ctx) or Decimal('0')

    intangible_latest = Decimal('0')
    intangible_prior = Decimal('0')
    intangible_tag_latest: Optional[str] = None
    intangible_tag_prior: Optional[str] = None
    for tag in INTANGIBLE_TAG_CANDIDATES:
        val_latest = get_value(values, tag, latest_ctx)
        val_prior = get_value(values, tag, prior_ctx)
        if val_latest is not None and val_latest != 0:
            intangible_latest = val_latest
            intangible_tag_latest = tag
        if val_prior is not None and val_prior != 0:
            intangible_prior = val_prior
            intangible_tag_prior = tag
        if (intangible_tag_latest is not None) or (intangible_tag_prior is not None):
            break

    # if tag included goodwill, ensure we exclude goodwill when necessary
    if intangible_latest and intangible_latest < goodwill_latest:
        intangible_latest = Decimal('0')
    if intangible_prior and intangible_prior < goodwill_prior:
        intangible_prior = Decimal('0')

    equity_fact = get_fact(values, equity_tag, latest_ctx)
    intangible_fact = get_fact(values, intangible_tag_latest, latest_ctx) if intangible_tag_latest else None
    goodwill_fact = get_fact(values, GOODWILL_TAG, latest_ctx)
    equity_fact_prior = get_fact(values, equity_tag, prior_ctx)
    goodwill_fact_prior = get_fact(values, GOODWILL_TAG, prior_ctx)
    intangible_fact_prior = get_fact(values, intangible_tag_prior, prior_ctx) if intangible_tag_prior else None

    tce_latest = stock_latest - goodwill_latest - intangible_latest
    tce_prior = stock_prior - goodwill_prior - intangible_prior

    # shares
    shares_val = None
    shares_ctx = None
    shares_tag_used: Optional[str] = None
    for tag in SHARE_TAGS:
        share_points = []
        for ctx_id, fact in values.get(tag, {}).items():
            ctx = contexts.get(ctx_id)
            if ctx is None or ctx.has_segment or ctx.instant is None:
                continue
            share_points.append((ctx.instant, ctx_id, fact.value))
        if share_points:
            share_points.sort(key=lambda item: item[0])
            shares_ctx = share_points[-1][1]
            shares_val = share_points[-1][2]
            shares_tag_used = tag
            break
    if shares_val is None:
        raise ValueError('Unable to locate share count')

    shares_fact = get_fact(values, shares_tag_used, shares_ctx) if shares_tag_used and shares_ctx else None

    tbvps = tce_latest / shares_val

    # Net income and average TCE (annualized)
    end_date = contexts[latest_ctx].instant
    income_ctx = pick_duration_context(contexts, end_date)
    net_income = None
    net_income_tag_used: Optional[str] = None
    if income_ctx:
        for tag in NET_INCOME_TAGS:
            val = get_value(values, tag, income_ctx)
            if val is not None:
                net_income = val
                net_income_tag_used = tag
                break
    if net_income is None:
        raise ValueError('Unable to fetch net income for duration context')

    net_income_fact = get_fact(values, net_income_tag_used, income_ctx) if net_income_tag_used and income_ctx else None

    average_tce = (tce_latest + tce_prior) / 2
    rote = (net_income * 4) / average_tce

    # CRE / loans from HTML table
    total_loans, total_cre, total_loans_ctx, total_cre_ctx, total_loans_tag, total_cre_tag = extract_loan_totals(html_path, contexts, values)
    cre_ratio = total_cre / total_loans
    total_loans_fact = get_fact(values, total_loans_tag, total_loans_ctx) if total_loans_tag and total_loans_ctx else None
    total_cre_fact = get_fact(values, total_cre_tag, total_cre_ctx) if total_cre_tag and total_cre_ctx else None

    return {
        'tbvps': tbvps,
        'tce_latest': tce_latest,
        'shares': shares_val,
        'net_income': net_income,
        'average_tce': average_tce,
        'rote': rote,
        'total_loans': total_loans,
        'total_cre': total_cre,
        'cre_ratio': cre_ratio,
        'latest_date': latest_date,
        'prior_instant': contexts[prior_ctx].instant,
        'shares_context': shares_ctx,
        'shares_tag': shares_tag_used,
        'equity_context': latest_ctx,
        'equity_tag': equity_tag,
        'equity_fact_id': equity_fact.fact_id if equity_fact else None,
        'equity_context_prior': prior_ctx,
        'equity_fact_id_prior': equity_fact_prior.fact_id if equity_fact_prior else None,
        'net_income_context': income_ctx,
        'net_income_tag': net_income_tag_used,
        'net_income_fact_id': net_income_fact.fact_id if net_income_fact else None,
        'total_loans_context': total_loans_ctx,
        'total_loans_tag': total_loans_tag,
        'total_loans_fact_id': total_loans_fact.fact_id if total_loans_fact else None,
        'total_cre_context': total_cre_ctx,
        'total_cre_tag': total_cre_tag,
        'total_cre_fact_id': total_cre_fact.fact_id if total_cre_fact else None,
        'goodwill_fact_id': goodwill_fact.fact_id if goodwill_fact else None,
        'goodwill_fact_id_prior': goodwill_fact_prior.fact_id if goodwill_fact_prior else None,
        'goodwill_tag': GOODWILL_TAG if goodwill_fact else None,
        'intangible_tag': intangible_tag_latest,
        'intangible_fact_id': intangible_fact.fact_id if intangible_fact else None,
        'intangible_fact_id_prior': intangible_fact_prior.fact_id if intangible_fact_prior else None,
        'shares_fact_id': shares_fact.fact_id if shares_fact else None,
    }


def main():
    peers = {
        'EWBC': Path('evidence/primary_sources/EWBC_2025-06-30_10Q.html'),
        'COLB': Path('evidence/primary_sources/COLB_2025-06-30_10Q.html.gz'),
        'BANC': Path('evidence/primary_sources/BANC_2025-06-30_10Q.html.gz'),
        'CVBF': Path('evidence/primary_sources/CVBF_2025-06-30_10Q.html.gz'),
        'HAFC': Path('evidence/primary_sources/HAFC_2025-06-30_10Q.html.gz'),
        'HOPE': Path('evidence/primary_sources/HOPE_2025-06-30_10Q.html.gz'),
        'WAFD': Path('evidence/primary_sources/WAFD_2025-06-30_10Q.html.gz'),
        'PPBI': Path('evidence/primary_sources/PPBI_2025-06-30_10Q.html.gz'),
    }

    results = []
    for ticker, path in peers.items():
        try:
            metrics = calculate_peer_metrics(path)
            tbvps = float(metrics['tbvps'])
            rote_pct = float(metrics['rote']) * 100  # Convert to percentage
            cre_pct = float(metrics['cre_ratio']) * 100  # Convert to percentage

            print(f"✅ {ticker:5} - TBVPS: ${tbvps:>6.2f}  ROTE: {rote_pct:>5.2f}%  CRE: {cre_pct:>5.1f}%")

            results.append({
                'ticker': ticker,
                'tbvps': tbvps,
                'rote_pct': rote_pct,
                'cre_pct': cre_pct,
                'tce_latest': float(metrics['tce_latest']),
                'shares': float(metrics['shares']),
                'net_income': float(metrics['net_income']),
                'average_tce': float(metrics['average_tce']),
                'total_loans': float(metrics['total_loans']),
                'total_cre': float(metrics['total_cre']),
            })
        except Exception as e:
            print(f"❌ {ticker:5} - ERROR: {str(e)}")
            results.append({
                'ticker': ticker,
                'error': str(e)
            })

    return results


if __name__ == '__main__':
    results = main()

    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print()

    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]

    print(f"Successful: {len(successful)}/8")
    print(f"Failed: {len(failed)}/8")
    print()

    if failed:
        print("Failed extractions:")
        for r in failed:
            print(f"  ❌ {r['ticker']}: {r['error']}")
        print()
