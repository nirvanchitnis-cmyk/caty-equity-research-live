#!/usr/bin/env python3
"""
Apply Market Data - SURGICAL Propagation Script

Reads data/market_data_current.json and CAREFULLY updates ONLY:
1. Spot/current price references (NOT target prices)
2. "As of [date]" references for market data
3. Report generation dates

DOES NOT touch:
- Target prices ($52.03, $56.50, $39.32, etc.)
- Scenario prices
- Valuation outputs

Usage:
    python3 scripts/apply_market_data.py [--dry-run]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def load_market_data(base_path: Path) -> dict:
    """Load market data JSON"""
    data_path = base_path / 'data' / 'market_data_current.json'
    with open(data_path, 'r') as f:
        return json.load(f)


def surgical_replace(content: str, data: dict) -> str:
    """
    Surgically replace ONLY spot price and date references.
    Uses context clues to avoid replacing target prices.
    """
    price = data['price']
    price_date = data['price_date']
    report_date = data['report_generated'][:10]

    # Format dates
    price_date_long = datetime.strptime(price_date, '%Y-%m-%d').strftime('%B %d, %Y')  # "October 18, 2025"
    price_date_short = datetime.strptime(price_date, '%Y-%m-%d').strftime('%b %d, %Y')  # "Oct 18, 2025"
    report_date_long = datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')

    # RULE 1: Replace "Current Price: $XX.XX" → "Current Price: $45.89"
    content = re.sub(
        r'(Current Price[:\s]+)\$\d+\.\d{2}',
        fr'\1${price:.2f}',
        content,
        flags=re.IGNORECASE
    )

    # RULE 2: Replace "Spot Price: $XX.XX" or "spot = $XX.XX"
    content = re.sub(
        r'((?:Spot|spot)[:\s=]+)\$\d+\.\d{2}',
        fr'\1${price:.2f}',
        content
    )

    # RULE 3: Replace "As of Oct XX, 2025" → "As of October 18, 2025"
    content = re.sub(
        r'As of Oct(?:ober)? \d{1,2}, 2025',
        f'As of {price_date_long}',
        content
    )

    # RULE 4: Replace "(Oct XX, 2025)" in metric subtexts → "(October 18, 2025)"
    content = re.sub(
        r'\(Oct(?:ober)? \d{1,2}, 2025\)',
        f'({price_date_long})',
        content
    )

    # RULE 5: Replace "| October XX, 2025" in page titles → "| October 19, 2025"
    content = re.sub(
        r'(\| )October \d{1,2}, 2025',
        fr'\1{report_date_long}',
        content
    )

    # RULE 6: Replace "Analysis Date: October XX" → "Report Date: October 19"
    content = re.sub(
        r'Analysis Date: October \d{1,2}, 2025',
        f'Report Date: {report_date_long}',
        content
    )

    # RULE 7: Update "vs current $XX.XX" references in prose
    # Only replace if in 45-46 range (spot price range, not targets)
    content = re.sub(
        r'(vs current|vs\. current|vs spot) \$45\.\d{2}',
        fr'\1 ${price:.2f}',
        content,
        flags=re.IGNORECASE
    )

    return content


def process_file(file_path: Path, data: dict, dry_run: bool) -> int:
    """Process a single file"""
    try:
        content = file_path.read_text()
        updated_content = surgical_replace(content, data)

        if content != updated_content:
            if not dry_run:
                file_path.write_text(updated_content)
            return 1
        return 0

    except Exception as e:
        print(f"ERROR processing {file_path.name}: {e}")
        return 0


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Propagate market data from JSON to report files")
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    args = parser.parse_args()

    base_path = Path(__file__).parent.parent
    data = load_market_data(base_path)

    print("\n" + "="*70)
    print("MARKET DATA PROPAGATION (SURGICAL)")
    print("="*70)
    print(f"\nSource: data/market_data_current.json")
    print(f"  Price: ${data['price']:.2f} (as of {data['price_date']})")
    print(f"  Report Date: {data['report_generated'][:10]}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}\n")

    # Get target files
    html_files = list(base_path.glob('*.html'))
    md_files = [
        base_path / 'README.md',
        base_path / 'DEREK_EXECUTIVE_SUMMARY.md',
    ]
    md_files += [f for f in (base_path / 'analysis').glob('*.md') if f.exists()]
    md_files += [f for f in (base_path / 'evidence').glob('*.md') if f.exists()]

    all_files = html_files + md_files
    print(f"Target Files: {len(all_files)}\n")

    updated_count = 0
    for file_path in all_files:
        if process_file(file_path, data, args.dry_run):
            status = "[DRY RUN]" if args.dry_run else "[UPDATED]"
            print(f"  {status} {file_path.name}")
            updated_count += 1

    print(f"\n{'='*70}")
    print(f"Files Updated: {updated_count} / {len(all_files)}")
    if args.dry_run:
        print("\n[DRY RUN MODE] No files were modified.")
        print("Run without --dry-run to apply changes.")
    else:
        print(f"\n✓ Market data propagated successfully.")
        print("\nNext steps:")
        print("  1. Run: python3 analysis/reconciliation_guard.py")
        print("  2. Review changes: git diff")
        print("  3. Commit if validation passes")

    print("="*70 + "\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
