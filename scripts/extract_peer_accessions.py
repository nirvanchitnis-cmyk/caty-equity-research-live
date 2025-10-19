#!/usr/bin/env python3
"""
Extract Q2'25 10-Q Accession IDs for 8 Peer Banks
Uses SEC browse-edgar endpoint (more reliable than data.sec.gov API)
"""

import requests
import xml.etree.ElementTree as ET
import json
import time

PEERS = [
    ('EWBC', 'East West Bancorp'),
    ('CVBF', 'CVB Financial'),
    ('HAFC', 'Hanmi Financial'),
    ('HOPE', 'Hope Bancorp'),
    ('COLB', 'Columbia Banking System'),
    ('WAFD', 'Washington Federal'),
    ('PPBI', 'Pacific Premier Bancorp'),
    ('BANC', 'Banc of California'),
]

def fetch_q2_2025_accession(ticker, company_name):
    """
    Fetch Q2'25 10-Q accession number for a given ticker

    Returns: dict with accession, filing_date, url or None if not found
    """
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-Q&dateb=&owner=exclude&count=10&output=atom'

    headers = {
        'User-Agent': 'Mozilla/5.0 (research@analysis.com)',
        'Accept': 'application/atom+xml',
    }

    try:
        print(f"  Fetching {ticker} filings...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        # Define namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        # Find all entry elements (filings)
        entries = root.findall('atom:entry', ns)

        for entry in entries:
            content = entry.find('atom:content', ns)
            if content is None:
                continue

            # Extract filing details
            accession_elem = content.find('accession-number')
            filing_date_elem = content.find('filing-date')
            filing_href_elem = content.find('filing-href')

            if accession_elem is None or filing_date_elem is None:
                continue

            accession = accession_elem.text
            filing_date = filing_date_elem.text
            filing_url = filing_href_elem.text if filing_href_elem is not None else ''

            # Check if this is Q2'25 (filed between July 1 - Aug 31, 2025)
            if filing_date >= '2025-07-01' and filing_date <= '2025-08-31':
                print(f"    ✅ Found Q2'25 10-Q:")
                print(f"       Accession: {accession}")
                print(f"       Filed: {filing_date}")
                print(f"       URL: {filing_url}")

                return {
                    'ticker': ticker,
                    'company': company_name,
                    'accession': accession,
                    'filing_date': filing_date,
                    'filing_url': filing_url,
                    'status': 'FOUND'
                }

        print(f"    ⚠️  No Q2'25 10-Q found for {ticker}")
        return {
            'ticker': ticker,
            'company': company_name,
            'accession': 'NOT FOUND',
            'filing_date': 'N/A',
            'filing_url': '',
            'status': 'NOT FOUND'
        }

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return {
            'ticker': ticker,
            'company': company_name,
            'accession': 'ERROR',
            'filing_date': 'N/A',
            'filing_url': '',
            'status': 'ERROR',
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("EXTRACTING Q2'25 10-Q ACCESSION IDS FOR 8 PEER BANKS")
    print("=" * 80)
    print()

    results = []

    for ticker, company_name in PEERS:
        print(f"Processing {ticker} ({company_name})...")
        result = fetch_q2_2025_accession(ticker, company_name)
        results.append(result)
        print()

        # SEC rate limiting: max 10 requests/second
        time.sleep(0.15)

    # Save results
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
    found = sum(1 for r in results if r['status'] == 'FOUND')
    print(f"Summary:")
    print(f"  Total Peers: {len(results)}")
    print(f"  Q2'25 10-Qs Found: {found}")
    print(f"  Missing: {len(results) - found}")
    print()

    # Print all accessions for quick reference
    print("=" * 80)
    print("PEER ACCESSION SUMMARY")
    print("=" * 80)
    print()
    for r in results:
        status_icon = "✅" if r['status'] == 'FOUND' else "❌"
        print(f"{status_icon} {r['ticker']:5} - {r['accession']}")
    print()

if __name__ == '__main__':
    main()
