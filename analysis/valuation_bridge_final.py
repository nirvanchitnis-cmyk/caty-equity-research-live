"""
DUAL VALUATION BRIDGE - Regression vs Gordon Growth Reconciliation
Generated: 2025-10-19 04:30 PT
"""

import numpy as np
from scipy import stats
import csv

# Load peer data
with open('evidence/peer_snapshot_2025Q2.csv', 'r') as f:
    reader = csv.DictReader(f)
    peers = [r for r in reader 
             if r['Ticker'] not in ['CATY', 'NA', ''] 
             and 'Median' not in r.get('Company', '')
             and r['ROTE_Pct'] 
             and float(r['ROTE_Pct']) > 0]

rote = np.array([float(p['ROTE_Pct']) for p in peers])
ptbv = np.array([float(p['P_TBV']) for p in peers])

# PATH A: Regression
slope, intercept, r_value, p_value, std_err = stats.linregress(rote, ptbv)
caty_rote_current = 11.95
caty_tbvps = 36.16
implied_ptbv = intercept + slope * caty_rote_current
target_regression = implied_ptbv * caty_tbvps

# PATH B: Gordon Growth  
ltm_ni = 294.671
through_cycle_nco_bps = 45.8  # 42.8 + 3.0 CRE premium
ltm_nco_bps = 18.13
delta_provision = ((through_cycle_nco_bps - ltm_nco_bps) / 10000) * 19448.955
normalized_ni = ltm_ni - (delta_provision * 0.80)
normalized_rote = (normalized_ni / 2465.091) * 100
coe = 9.587
g = 2.5
justified_ptbv = (normalized_rote - g) / (coe - g)
target_gordon = justified_ptbv * caty_tbvps

# PATH C: Required COE for reconciliation
required_coe = ((normalized_rote - g) / (target_regression / caty_tbvps)) + g
coe_premium_bps = (coe - required_coe) * 100

print(f"PATH A (Regression): ${target_regression:.2f} (+{((target_regression-45.87)/45.87)*100:.1f}%)")
print(f"PATH B (Normalized): ${target_gordon:.2f} ({((target_gordon-45.87)/45.87)*100:.1f}%)")
print(f"Gap: ${target_regression - target_gordon:.2f}")
print(f"Required CRE Premium: {coe_premium_bps:.0f} bps")
print(f"\nCONCLUSION: {coe_premium_bps:.0f} bps CRE premium UNSUBSTANTIATED")
print(f"RATING: HOLD (was SELL)")
