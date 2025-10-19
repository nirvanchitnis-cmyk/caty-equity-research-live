#!/usr/bin/env python3
"""
Generate NCO History JSON for Chart.js
Filters FDIC NCO timeseries to post-2008 sample and formats for createNCOTrendChart()
"""

import csv
import json
from datetime import datetime
from pathlib import Path

# Paths
base_dir = Path(__file__).parent.parent
csv_path = base_dir / 'evidence' / 'raw' / 'fdic_CATY_NTLNLSCOQR_timeseries.csv'
json_path = base_dir / 'data' / 'fdic_nco_history.json'

# Filter for post-2008 (GFC window)
start_date = '20080101'

# Through-cycle assumption
through_cycle_nco_bps = 42.8

# Read CSV and filter
nco_data = []
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rep_date = row['REPDTE']
        nco_rate = float(row['NTLNLSCOQR'])

        # Filter for post-2008
        if rep_date >= start_date:
            # Convert to basis points (multiply by 10000)
            nco_bps = nco_rate * 10000

            # Format date as YYYY-QX
            year = rep_date[:4]
            month = rep_date[4:6]
            quarter = (int(month) - 1) // 3 + 1
            date_label = f"{year}-Q{quarter}"

            nco_data.append({
                'date': date_label,
                'nco_bps': round(nco_bps, 2),
                'rep_date': rep_date
            })

# Create JSON structure for Chart.js
chart_data = {
    'metadata': {
        'source': 'FDIC Call Reports (NTLNLSCOQR)',
        'start_date': nco_data[0]['date'] if nco_data else None,
        'end_date': nco_data[-1]['date'] if nco_data else None,
        'sample_size': len(nco_data),
        'through_cycle_nco_bps': through_cycle_nco_bps,
        'description': 'Quarterly net charge-off rate (annualized) as % of average loans'
    },
    'labels': [d['date'] for d in nco_data],
    'values': [d['nco_bps'] for d in nco_data],
    'raw_data': nco_data
}

# Write JSON
json_path.parent.mkdir(exist_ok=True)
with open(json_path, 'w') as f:
    json.dump(chart_data, f, indent=2)

print(f"✓ Generated {json_path}")
print(f"  Sample: {chart_data['metadata']['start_date']} to {chart_data['metadata']['end_date']}")
print(f"  Data points: {chart_data['metadata']['sample_size']}")
print(f"  Through-cycle NCO: {through_cycle_nco_bps} bps")
