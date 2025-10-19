from __future__ import annotations

import gzip
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

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


def load_contexts(root: ET.Element) -> Dict[str, Context]:
    contexts: Dict[str, Context] = {}
    for ctx in root.findall(f'.//{XBRLI}context'):
        cid = ctx.attrib['id']
        period = ctx.find(f'{XBRLI}period')
        instant_el = period.find(f'{XBRLI}instant') if period is not None else None
        start_el = period.find(f'{XBRLI}startDate') if period is not None else None
        end_el = period.find(f'{XBRLI}endDate') if period is not None else None
        segment = ctx.find(f'{XBRLI}segment')
        contexts[cid] = Context(
            id=cid,
            instant=instant_el.text if instant_el is not None else None,
            start=start_el.text if start_el is not None else None,
            end=end_el.text if end_el is not None else None,
            has_segment=segment is not None and len(segment) > 0,
        )
    return contexts


def build_value_index(root: ET.Element) -> Dict[str, Dict[str, Decimal]]:
    index: Dict[str, Dict[str, Decimal]] = {}
    for elem in root.findall(f'.//{IX}nonFraction'):
        name = elem.attrib.get('name')
        ctx = elem.attrib.get('contextRef')
        text = (elem.text or '').strip()
        if not name or not ctx or not text:
            continue
        cleaned = text.replace(',', '').replace('$', '')
        cleaned = cleaned.replace('(', '-').replace(')', '')
        try:
            value = Decimal(cleaned)
        except Exception:
            continue
        index.setdefault(name, {})[ctx] = value
    return index


def pick_duration_context(contexts: Dict[str, Context], end_date: str) -> Optional[str]:
    # Prefer most recent duration ending on end_date with no segment
    durations = [
        ctx for ctx in contexts.values()
        if ctx.end == end_date and ctx.start is not None and not ctx.has_segment
    ]
    if not durations:
        return None
    # choose one with latest start
    durations.sort(key=lambda c: c.start, reverse=True)
    return durations[0].id


def get_value(value_index: Dict[str, Dict[str, Decimal]], tag: str, context: Optional[str]) -> Optional[Decimal]:
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


def extract_loan_totals(html_path: Path) -> Tuple[Decimal, Decimal]:
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
                return total_loans, total_cre

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

    # Determine equity contexts directly from tag values
    equity_points = []
    for tag in EQUITY_TAGS:
        for ctx_id, amount in values.get(tag, {}).items():
            ctx = contexts.get(ctx_id)
            if ctx is None or ctx.has_segment or ctx.instant is None:
                continue
            equity_points.append((ctx.instant, ctx_id, amount))
    if not equity_points:
        raise ValueError('Unable to fetch stockholders equity values')
    equity_points.sort(key=lambda item: item[0])
    latest_date, latest_ctx, stock_latest = equity_points[-1]
    prior_candidates = [item for item in equity_points if item[0] < latest_date]
    if not prior_candidates:
        raise ValueError('No prior instant context found for equity')
    prior_date, prior_ctx, stock_prior = prior_candidates[-1]

    goodwill_latest = get_value(values, GOODWILL_TAG, latest_ctx) or Decimal('0')
    goodwill_prior = get_value(values, GOODWILL_TAG, prior_ctx) or Decimal('0')

    intangible_latest = Decimal('0')
    intangible_prior = Decimal('0')
    for tag in INTANGIBLE_TAG_CANDIDATES:
        val_latest = get_value(values, tag, latest_ctx)
        val_prior = get_value(values, tag, prior_ctx)
        if val_latest is not None:
            intangible_latest = val_latest
        if val_prior is not None:
            intangible_prior = val_prior
        if intangible_latest or intangible_prior:
            break

    # if tag included goodwill, ensure we exclude goodwill when necessary
    if intangible_latest and intangible_latest < goodwill_latest:
        intangible_latest = Decimal('0')
    if intangible_prior and intangible_prior < goodwill_prior:
        intangible_prior = Decimal('0')

    tce_latest = stock_latest - goodwill_latest - intangible_latest
    tce_prior = stock_prior - goodwill_prior - intangible_prior

    # shares
    shares_val = None
    shares_ctx = None
    for tag in SHARE_TAGS:
        share_points = []
        for ctx_id, amount in values.get(tag, {}).items():
            ctx = contexts.get(ctx_id)
            if ctx is None or ctx.has_segment or ctx.instant is None:
                continue
            share_points.append((ctx.instant, ctx_id, amount))
        if share_points:
            share_points.sort(key=lambda item: item[0])
            shares_ctx = share_points[-1][1]
            shares_val = share_points[-1][2]
            break
    if shares_val is None:
        raise ValueError('Unable to locate share count')

    tbvps = tce_latest / shares_val

    # Net income and average TCE (annualized)
    end_date = contexts[latest_ctx].instant
    income_ctx = pick_duration_context(contexts, end_date)
    net_income = None
    if income_ctx:
        for tag in NET_INCOME_TAGS:
            val = get_value(values, tag, income_ctx)
            if val is not None:
                net_income = val
                break
    if net_income is None:
        raise ValueError('Unable to fetch net income for duration context')

    average_tce = (tce_latest + tce_prior) / 2
    rote = (net_income * 4) / average_tce

    # CRE / loans from HTML table
    total_loans, total_cre = extract_loan_totals(html_path)
    cre_ratio = total_cre / total_loans

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
