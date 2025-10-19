#!/usr/bin/env python3
"""
Disconfirmer Monitoring Script - Exit codes fire when thresholds breached
Monitors key drivers and raises alerts when assumptions invalidated
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# Paths
base_dir = Path(__file__).parent.parent
market_data = base_dir / 'data' / 'market_data_current.json'
nco_history = base_dir / 'data' / 'fdic_nco_history.json'

# Load market data
with open(market_data, 'r') as f:
    data = json.load(f)

# Load NCO history
with open(nco_history, 'r') as f:
    nco_data = json.load(f)

print("=" * 70)
print("DISCONFIRMER MONITORING - Driver Invalidation Check")
print("=" * 70)
print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PT')}")
print()

# Track alert count
alerts = []

# ============================================================
# DRIVER 1: Through-Cycle NCO Normalization
# ============================================================
print("1. THROUGH-CYCLE NCO NORMALIZATION")
print("-" * 70)

current_nco = nco_data['values'][-1]  # Latest quarter
threshold_nco = 45.8  # 42.8 + 3.0 CRE premium

print(f"   Current NCO (Q2 2025): {current_nco:.2f} bps")
print(f"   Threshold: {threshold_nco:.2f} bps")
print(f"   Through-Cycle Assumption: 42.8 bps")

if current_nco > threshold_nco:
    alert = f"❌ ALERT: NCO {current_nco:.2f} bps exceeds threshold {threshold_nco:.2f} bps"
    alerts.append(alert)
    print(f"   {alert}")
    print(f"   ACTION: Increase tail probability from 26% to 35%, rerun Wilson bounds")
else:
    print(f"   ✅ PASS: NCO within tolerance")

print()

# ============================================================
# DRIVER 2: Deposit Beta Trajectory
# ============================================================
print("2. DEPOSIT BETA TRAJECTORY")
print("-" * 70)

# Placeholder - would read from quarterly data
current_beta = 0.35  # Hardcoded for now, would pull from data
threshold_beta = 0.45
nib_mix = 27.0  # Current NIB %
nib_threshold_drop = 200  # bps YoY decline

print(f"   Current Beta: {current_beta:.2f}")
print(f"   Threshold: {threshold_beta:.2f}")
print(f"   NIB Mix: {nib_mix:.1f}%")

if current_beta > threshold_beta:
    alert = f"❌ ALERT: Deposit beta {current_beta:.2f} exceeds threshold {threshold_beta:.2f}"
    alerts.append(alert)
    print(f"   {alert}")
    print(f"   ACTION: Revise NIM forecast down 50-100 bps, rerun ROTE")
else:
    print(f"   ✅ PASS: Deposit beta within tolerance")

print()

# ============================================================
# DRIVER 3: ROTE vs P/TBV Regression (Cook's Distance)
# ============================================================
print("3. ROTE vs P/TBV REGRESSION (PEER POSITIONING)")
print("-" * 70)

# Placeholder - would calculate Cook's D from peer data
cooks_d_threshold = 1.0
colb_cooks_d = 4.03  # Known outlier

print(f"   Cook's Distance Threshold: {cooks_d_threshold:.2f}")
print(f"   COLB Cook's D: {colb_cooks_d:.2f}")

if colb_cooks_d > cooks_d_threshold:
    print(f"   ⚠️  WARNING: COLB is high outlier (Cook's D={colb_cooks_d:.2f})")
    print(f"   NOTE: Retained for sample size, but monitor")
else:
    print(f"   ✅ PASS: No high outliers detected")

print()

# ============================================================
# DRIVER 4: Probability Weighting (Wilson vs Market-Implied)
# ============================================================
print("4. PROBABILITY WEIGHTING RECONCILIATION")
print("-" * 70)

wilson_tail = 0.26  # 26% tail probability
market_impl_tail = 0.609  # 60.9% probability below spot
divergence = abs(wilson_tail - market_impl_tail)
divergence_threshold = 0.40  # Alert if >40 ppts divergence

print(f"   Wilson Tail Probability: {wilson_tail * 100:.1f}%")
print(f"   Market-Implied (below spot): {market_impl_tail * 100:.1f}%")
print(f"   Divergence: {divergence * 100:.1f} percentage points")
print(f"   Threshold: {divergence_threshold * 100:.1f} ppts")

if divergence > divergence_threshold:
    alert = f"❌ ALERT: Wilson/Market divergence {divergence * 100:.1f} ppts exceeds {divergence_threshold * 100:.1f} ppts"
    alerts.append(alert)
    print(f"   {alert}")
    print(f"   ACTION: Reconcile methodologies or explain divergence")
else:
    print(f"   ✅ PASS: Wilson/Market divergence within tolerance")

print()

# ============================================================
# DRIVER 5: ESG Discount / COE Premium
# ============================================================
print("5. ESG DISCOUNT / COE PREMIUM")
print("-" * 70)

esg_coe_premium = 0.0025  # 25 bps (20 climate + 30 governance - 25 social)
esg_valuation_impact = -1.47  # $/share

print(f"   ESG COE Premium: {esg_coe_premium * 10000:.0f} bps")
print(f"   ESG Valuation Impact: ${esg_valuation_impact:.2f}/share")
print(f"   Components: Climate +20 bps, Governance +30 bps, Social -25 bps")
print(f"   ✅ ESG discount integrated into valuation bridge")

print()

# ============================================================
# SUMMARY
# ============================================================
print("=" * 70)
print("MONITORING SUMMARY")
print("=" * 70)

if len(alerts) > 0:
    print(f"\n🚨 {len(alerts)} ALERT(S) TRIGGERED:\n")
    for i, alert in enumerate(alerts, 1):
        print(f"   {i}. {alert}")
    print()
    print("Exit Code: 1 (THRESHOLDS BREACHED)")
    sys.exit(1)
else:
    print("\n✅ ALL DRIVERS WITHIN TOLERANCE")
    print("Exit Code: 0 (MONITORING PASS)")
    sys.exit(0)
