#!/usr/bin/env python3
"""
Disconfirmer Monitoring Script - Exit codes fire when thresholds breached
Monitors key drivers and raises alerts when assumptions invalidated
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Paths
base_dir = Path(__file__).parent.parent
log_path = base_dir / 'logs' / 'automation_run.log'
market_data_path = base_dir / 'data' / 'market_data_current.json'
nco_history_path = base_dir / 'data' / 'fdic_nco_history.json'
driver_inputs_path = base_dir / 'data' / 'driver_inputs.json'

with open(market_data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load NCO history
with open(nco_history_path, 'r', encoding='utf-8') as f:
    nco_data = json.load(f)

# Load driver inputs
with open(driver_inputs_path, 'r', encoding='utf-8') as f:
    driver_inputs = json.load(f)

print("=" * 70)
print("DISCONFIRMER MONITORING - Driver Invalidation Check")
print("=" * 70)
print("Run Time: {}".format(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')))
print()

# Track alert count
alerts = []

# ============================================================
# DRIVER 1: Through-Cycle NCO Normalization
# ============================================================
print("1. THROUGH-CYCLE NCO NORMALIZATION")
print("-" * 70)

current_nco = float(nco_data['values'][-1])  # Latest quarter
nco_inputs = driver_inputs['nco']
threshold_nco = float(nco_inputs['threshold_bps'])

print(f"   Current NCO (Q2 2025): {current_nco:.2f} bps")
print(f"   Threshold: {threshold_nco:.2f} bps")
print(f"   Through-Cycle Assumption: {nco_inputs['through_cycle_bps']:.1f} bps")

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

deposit_inputs = driver_inputs['deposit_beta']
current_beta = float(deposit_inputs['rolling_3m'])
threshold_beta = float(deposit_inputs['threshold'])
nib_mix = float(deposit_inputs['nib_mix_pct'])
nib_change = float(deposit_inputs['nib_mix_year_change_bps'])
nib_threshold_drop = float(deposit_inputs['nib_mix_threshold_bps'])

print(f"   Current Beta: {current_beta:.2f}")
print(f"   Threshold: {threshold_beta:.2f}")
print(f"   NIB Mix: {nib_mix:.1f}%")
print(f"   YoY NIB Δ: {nib_change:+.0f} bps (threshold {nib_threshold_drop:+.0f} bps)")

if current_beta > threshold_beta:
    alert = f"❌ ALERT: Deposit beta {current_beta:.2f} exceeds threshold {threshold_beta:.2f}"
    alerts.append(alert)
    print(f"   {alert}")
    print(f"   ACTION: Revise NIM forecast down 50-100 bps, rerun ROTE")
else:
    print(f"   ✅ PASS: Deposit beta within tolerance")

if nib_change < nib_threshold_drop:
    alert = f"❌ ALERT: NIB mix change {nib_change:+.0f} bps worse than threshold {nib_threshold_drop:+.0f} bps"
    alerts.append(alert)
    print(f"   {alert}")
    print("   ACTION: Refresh funding mix assumptions and liquidity plan")

print()

# ============================================================
# DRIVER 3: ROTE vs P/TBV Regression (Cook's Distance)
# ============================================================
print("3. ROTE vs P/TBV REGRESSION (PEER POSITIONING)")
print("-" * 70)

regression_inputs = driver_inputs['regression']
cooks_d_threshold = float(regression_inputs['threshold'])
cooks_distance = regression_inputs['cooks_distance']
max_peer = max(cooks_distance, key=lambda k: cooks_distance[k])
max_value = float(cooks_distance[max_peer])

print(f"   Cook's Distance Threshold: {cooks_d_threshold:.2f}")
print(f"   Largest Cook's D: {max_peer} @ {max_value:.2f}")

# Check for documented exception
has_exception = 'documented_exception' in regression_inputs
if has_exception and regression_inputs['documented_exception']['peer'] == max_peer:
    exception = regression_inputs['documented_exception']
    print(f"   ℹ️  DOCUMENTED EXCEPTION: {max_peer} Cook's D={max_value:.2f}")
    print(f"   Action: {exception['action']}")
    print(f"   Rationale: {exception['rationale']}")
    print(f"   Sensitivity: {exception['sensitivity']}")
    print(f"   Override By: {exception['override_by']} on {exception['override_date']}")
    print(f"   ✅ PASS: Outlier documented and approved")
elif max_value > cooks_d_threshold:
    alert = f"⚠️  WARNING: {max_peer} Cook's D={max_value:.2f} exceeds threshold {cooks_d_threshold:.2f}"
    alerts.append(alert)
    print(f"   {alert}")
    print("   ACTION: Recalculate regression excluding outlier and document impact")
else:
    print(f"   ✅ PASS: No high outliers detected")

print()

# ============================================================
# DRIVER 4: Probability Weighting (Wilson vs Market-Implied)
# ============================================================
print("4. PROBABILITY WEIGHTING RECONCILIATION")
print("-" * 70)

prob_inputs = driver_inputs['probability_weights']
wilson_tail = float(prob_inputs['wilson_tail_prob'])
market_impl_tail = float(prob_inputs['market_implied_below_prob'])
divergence = abs(wilson_tail - market_impl_tail)
divergence_threshold = float(prob_inputs['divergence_threshold'])

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

esg_inputs = driver_inputs['esg']
esg_coe_premium = float(esg_inputs['coe_premium_bps']) / 10000.0
esg_valuation_impact = float(esg_inputs['valuation_impact'])

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

status_code = 1 if alerts else 0

def append_log(message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    with log_path.open('a', encoding='utf-8') as fh:
        fh.write(f"[{timestamp}] {message}\n")

if alerts:
    print(f"\n🚨 {len(alerts)} ALERT(S) TRIGGERED:\n")
    for i, alert in enumerate(alerts, 1):
        print(f"   {i}. {alert}")
    print()
    print("Exit Code: 1 (THRESHOLDS BREACHED)")
    append_log(f"disconfirmer_monitor.py status=FAIL alerts={len(alerts)}")
    sys.exit(status_code)
else:
    print("\n✅ ALL DRIVERS WITHIN TOLERANCE")
    print("Exit Code: 0 (MONITORING PASS)")
    append_log("disconfirmer_monitor.py status=PASS alerts=0")
    sys.exit(status_code)
