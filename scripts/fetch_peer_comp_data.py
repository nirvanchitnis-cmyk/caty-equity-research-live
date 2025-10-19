#!/usr/bin/env python3
"""
PEER COMP DATA EXTRACTION - Q2 2025 10-Qs
Per Derek's Cross-Exam Q3, Q5, Q7

Extracts:
- Accession IDs for Q2'25 10-Qs
- TBVPS (Tangible Book Value Per Share)
- ROTE (Return on Tangible Common Equity)
- CRE concentration
- With page/line citations for audit trail

Author: Nirvan Chitnis
Date: October 18, 2025
"""

import requests
import json
import time
from datetime import datetime

# Derek's required peer list (from Cross-Exam Q3)
PEERS = {
    'EWBC': {'name': 'East West Bancorp', 'cik': '0000922864'},
    'CVBF': {'name': 'CVB Financial', 'cik': '0000859804'},
    'HAFC': {'name': 'Hanmi Financial', 'cik': '0001072745'},
    'HOPE': {'name': 'Hope Bancorp', 'cik': '0001216184'},
    'COLB': {'name': 'Columbia Banking System', 'cik': '0000947263'},
    'WAFD': {'name': 'Washington Federal', 'cik': '0000014154'},
    'PPBI': {'name': 'Pacific Premier Bancorp', 'cik': '0001013237'},
    'BANC': {'name': 'Banc of California', 'cik': '0001232576'},
}

# SEC Edgar headers (required for rate limiting compliance)
HEADERS = {
    'User-Agent': 'Research Analysis research@analysis.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

def fetch_company_filings(cik, form_type='10-Q', count=10):
    """
    Fetch recent filings for a company from SEC Edgar

    Args:
        cik: Company CIK number
        form_type: Filing type (10-Q, 10-K, etc.)
        count: Number of filings to retrieve

    Returns:
        List of filing metadata dicts
    """
    # Remove leading zeros from CIK for API call
    cik_clean = str(int(cik))

    url = f'https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json'

    print(f"  Fetching filings for CIK {cik}...")

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Extract recent filings
        recent = data.get('filings', {}).get('recent', {})

        filings = []
        for i in range(len(recent.get('accessionNumber', []))):
            form = recent['form'][i]
            if form == form_type:
                filing_date = recent['filingDate'][i]

                # Only get Q2'25 filings (filed around Aug 2025, for quarter ending June 30, 2025)
                if filing_date >= '2025-07-01' and filing_date <= '2025-08-31':
                    filings.append({
                        'form': form,
                        'filing_date': filing_date,
                        'accession': recent['accessionNumber'][i],
                        'primary_doc': recent['primaryDocument'][i],
                        'report_date': recent.get('reportDate', [''])[i],
                    })

        return filings

    except Exception as e:
        print(f"    ❌ Error fetching filings: {e}")
        return []

def main():
    print("=" * 80)
    print("PEER COMP DATA EXTRACTION - Q2 2025")
    print("=" * 80)
    print()

    print(f"Extracting data for {len(PEERS)} peers:")
    for ticker, info in PEERS.items():
        print(f"  {ticker:5} - {info['name']:30} (CIK {info['cik']})")
    print()

    results = []

    for ticker, info in PEERS.items():
        print(f"Processing {ticker} ({info['name']})...")

        # Fetch Q2'25 10-Q
        filings = fetch_company_filings(info['cik'], '10-Q', count=10)

        if not filings:
            print(f"  ⚠️  No Q2'25 10-Q found for {ticker}")
            results.append({
                'Ticker': ticker,
                'Company': info['name'],
                'CIK': info['cik'],
                'Q2_2025_Accession': 'NOT FOUND',
                'Filing_Date': 'N/A',
                'TBVPS': 'NEEDS MANUAL EXTRACTION',
                'ROTE': 'NEEDS MANUAL EXTRACTION',
                'CRE_Pct': 'NEEDS MANUAL EXTRACTION',
                'TBVPS_Citation': 'TBD',
                'ROTE_Citation': 'TBD',
            })
            continue

        # Use the most recent Q2'25 filing
        latest = filings[0]
        accession = latest['accession']
        filing_date = latest['filing_date']

        print(f"  ✅ Found Q2'25 10-Q:")
        print(f"     Accession: {accession}")
        print(f"     Filed: {filing_date}")
        print(f"     Report Date: {latest.get('report_date', 'N/A')}")

        # Construct filing URL
        accession_no_dashes = accession.replace('-', '')
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{info['cik']}/{accession_no_dashes}/{latest['primary_doc']}"

        print(f"     URL: {filing_url}")
        print()

        results.append({
            'Ticker': ticker,
            'Company': info['name'],
            'CIK': info['cik'],
            'Q2_2025_Accession': accession,
            'Filing_Date': filing_date,
            'Report_Date': latest.get('report_date', 'N/A'),
            'Filing_URL': filing_url,
            'TBVPS': 'NEEDS MANUAL EXTRACTION',
            'ROTE': 'NEEDS MANUAL EXTRACTION',
            'CRE_Pct': 'NEEDS MANUAL EXTRACTION',
            'TBVPS_Citation': 'TBD - Review Consolidated Balance Sheet',
            'ROTE_Citation': 'TBD - Review MD&A or Financial Highlights',
        })

        # Rate limiting (SEC requires 10 requests/second max)
        time.sleep(0.12)

    # Save results to JSON
    output_file = 'evidence/peer_accessions_2025Q2.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print(f"✅ Results saved to: {output_file}")
    print()

    # Summary
    found = sum(1 for r in results if r['Q2_2025_Accession'] != 'NOT FOUND')
    print(f"Summary:")
    print(f"  Total Peers: {len(results)}")
    print(f"  Q2'25 10-Qs Found: {found}")
    print(f"  Missing: {len(results) - found}")
    print()

    print("Next Steps:")
    print("  1. Review each filing URL to extract TBVPS and ROTE")
    print("  2. Record page/line citations for each metric")
    print("  3. Update evidence/peer_snapshot_2025Q2.csv with sourced data")
    print("  4. Remove all 'Estimated' placeholders")
    print()

    # Print filing URLs for manual review
    print("=" * 80)
    print("FILING URLS FOR MANUAL REVIEW")
    print("=" * 80)
    print()

    for result in results:
        if result['Q2_2025_Accession'] != 'NOT FOUND':
            print(f"{result['Ticker']:5} - {result['Filing_URL']}")

    print()

if __name__ == '__main__':
    main()
