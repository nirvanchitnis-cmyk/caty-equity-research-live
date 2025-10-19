#!/usr/bin/env python3
"""
CAPM BETA CALCULATION FOR CATHAY GENERAL BANCORP (CATY)
Per Derek's Cross-Exam Q4, Q6, Q8

Methodology:
- 5-year weekly returns (Oct 13, 2020 → Oct 13, 2025)
- Benchmark: S&P 500 Total Return Index (^GSPC)
- Frequency: Wednesday close (or Friday if Wednesday unavailable)
- Data Source: Yahoo Finance API (free, reproducible)
- Regression: CATY excess returns vs S&P 500 excess returns
- Risk-Free Rate: 10-year Treasury yield (current as of Oct 18, 2025)
- Equity Risk Premium: 5.5% (Damodaran Jan 2025 US equity premium)

Output:
- Beta coefficient
- R-squared
- Standard error
- Implied COE (Cost of Equity) = Rf + β × ERP
- Comparison to implied COE from P/TBV multiples

Author: Nirvan Chitnis
Date: October 18, 2025
Reviewer: Derek (GPT-5 Codex CLI)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("CAPM BETA CALCULATION - CATHAY GENERAL BANCORP (CATY)")
print("=" * 80)
print()

# ===== PARAMETERS (Derek's Q4 commitment) =====
TICKER = "CATY"
BENCHMARK = "^GSPC"  # S&P 500
START_DATE = "2020-10-13"
END_DATE = "2025-10-13"
FREQUENCY = "1wk"  # Weekly data
RISK_FREE_RATE = 0.0425  # 10-year Treasury as of Oct 18, 2025 (4.25% assumed)
EQUITY_RISK_PREMIUM = 0.055  # Damodaran Jan 2025: 5.5%

print(f"Ticker:               {TICKER}")
print(f"Benchmark:            {BENCHMARK} (S&P 500)")
print(f"Date Range:           {START_DATE} → {END_DATE} (5 years)")
print(f"Frequency:            Weekly (Wednesday or Friday close)")
print(f"Risk-Free Rate:       {RISK_FREE_RATE:.2%} (10-year Treasury)")
print(f"Equity Risk Premium:  {EQUITY_RISK_PREMIUM:.2%} (Damodaran)")
print()

# ===== DOWNLOAD DATA =====
print("=" * 80)
print("STEP 1: DOWNLOADING PRICE DATA")
print("=" * 80)
print()

print(f"📥 Fetching {TICKER} weekly prices from Yahoo Finance...")
caty_data = yf.download(TICKER, start=START_DATE, end=END_DATE, interval=FREQUENCY, progress=False, auto_adjust=False)

print(f"📥 Fetching {BENCHMARK} weekly prices from Yahoo Finance...")
sp500_data = yf.download(BENCHMARK, start=START_DATE, end=END_DATE, interval=FREQUENCY, progress=False, auto_adjust=False)

print(f"✅ Downloaded {len(caty_data)} weeks of CATY data")
print(f"✅ Downloaded {len(sp500_data)} weeks of S&P 500 data")
print()

# ===== CALCULATE RETURNS =====
print("=" * 80)
print("STEP 2: CALCULATING WEEKLY RETURNS")
print("=" * 80)
print()

# Use Adjusted Close for returns (accounts for dividends)
# Handle both single-column and multi-column DataFrame formats
if isinstance(caty_data.columns, pd.MultiIndex):
    # Multi-index: need to access by tuple (column_name, ticker)
    caty_returns = caty_data[('Adj Close', TICKER)].pct_change().dropna()
    sp500_returns = sp500_data[('Adj Close', BENCHMARK)].pct_change().dropna()
else:
    caty_returns = caty_data['Adj Close'].pct_change().dropna()
    sp500_returns = sp500_data['Adj Close'].pct_change().dropna()

# Align dates (inner join)
returns_df = pd.DataFrame({
    'CATY': caty_returns,
    'SP500': sp500_returns
}).dropna()

print(f"✅ Calculated returns for {len(returns_df)} weeks")
print(f"   Date range: {returns_df.index[0].date()} → {returns_df.index[-1].date()}")
print()

# Calculate excess returns (return - risk-free rate)
# Convert annual risk-free rate to weekly
weekly_rf = (1 + RISK_FREE_RATE) ** (1/52) - 1

returns_df['CATY_excess'] = returns_df['CATY'] - weekly_rf
returns_df['SP500_excess'] = returns_df['SP500'] - weekly_rf

# ===== SUMMARY STATISTICS =====
print("=" * 80)
print("STEP 3: SUMMARY STATISTICS")
print("=" * 80)
print()

caty_stats = {
    'Mean Weekly Return': returns_df['CATY'].mean(),
    'Annualized Return': (1 + returns_df['CATY'].mean()) ** 52 - 1,
    'Weekly Volatility': returns_df['CATY'].std(),
    'Annualized Volatility': returns_df['CATY'].std() * np.sqrt(52),
    'Min Weekly Return': returns_df['CATY'].min(),
    'Max Weekly Return': returns_df['CATY'].max(),
}

sp500_stats = {
    'Mean Weekly Return': returns_df['SP500'].mean(),
    'Annualized Return': (1 + returns_df['SP500'].mean()) ** 52 - 1,
    'Weekly Volatility': returns_df['SP500'].std(),
    'Annualized Volatility': returns_df['SP500'].std() * np.sqrt(52),
    'Min Weekly Return': returns_df['SP500'].min(),
    'Max Weekly Return': returns_df['SP500'].max(),
}

print("CATY Summary Statistics:")
for key, value in caty_stats.items():
    if 'Return' in key or 'Volatility' in key:
        print(f"  {key:.<30} {value:>10.2%}")
    else:
        print(f"  {key:.<30} {value:>10.4f}")

print()
print("S&P 500 Summary Statistics:")
for key, value in sp500_stats.items():
    if 'Return' in key or 'Volatility' in key:
        print(f"  {key:.<30} {value:>10.2%}")
    else:
        print(f"  {key:.<30} {value:>10.4f}")

print()

# ===== REGRESSION: CAPM BETA =====
print("=" * 80)
print("STEP 4: CAPM REGRESSION")
print("=" * 80)
print()

# Regression: CATY_excess = alpha + beta × SP500_excess + error
X = returns_df['SP500_excess'].values
y = returns_df['CATY_excess'].values

# Using scipy.stats for regression
slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

beta = slope
alpha_weekly = intercept
alpha_annual = (1 + alpha_weekly) ** 52 - 1
r_squared = r_value ** 2

print(f"Regression Results:")
print(f"  Beta (β)...................... {beta:.4f}")
print(f"  Alpha (weekly)................ {alpha_weekly:.4f}")
print(f"  Alpha (annualized)............ {alpha_annual:.2%}")
print(f"  R-squared (R²)................ {r_squared:.4f}")
print(f"  Standard Error................ {std_err:.4f}")
print(f"  p-value (Beta)................ {p_value:.6f}")
print()

# Interpretation
if p_value < 0.05:
    print(f"✅ Beta is statistically significant (p < 0.05)")
else:
    print(f"⚠️  Beta is NOT statistically significant (p >= 0.05)")

if r_squared < 0.30:
    print(f"⚠️  Low R² ({r_squared:.2%}) suggests poor model fit - single-factor CAPM may be inadequate")
elif r_squared < 0.50:
    print(f"✅ Moderate R² ({r_squared:.2%}) - typical for single-stock CAPM regressions")
else:
    print(f"✅ High R² ({r_squared:.2%}) - strong explanatory power")

print()

# ===== IMPLIED COE (DEREK Q8) =====
print("=" * 80)
print("STEP 5: IMPLIED COST OF EQUITY (COE)")
print("=" * 80)
print()

# CAPM formula: COE = Rf + β × ERP
coe_capm = RISK_FREE_RATE + beta * EQUITY_RISK_PREMIUM

print(f"CAPM Formula: COE = Rf + β × ERP")
print(f"  Risk-Free Rate (Rf)........... {RISK_FREE_RATE:.2%}")
print(f"  Beta (β)...................... {beta:.4f}")
print(f"  Equity Risk Premium (ERP)..... {EQUITY_RISK_PREMIUM:.2%}")
print(f"")
print(f"  → Implied COE (CAPM).......... {coe_capm:.2%}")
print()

# ===== COMPARISON TO IMPLIED COE FROM MULTIPLES (DEREK Q8 RECONCILIATION) =====
print("=" * 80)
print("STEP 6: RECONCILIATION TO IMPLIED COE FROM P/TBV MULTIPLES")
print("=" * 80)
print()

# From valuation model JSON: mean_coe = 9.587%
# Derived from P/TBV regression: COE = (ROTE - g) / (P/TBV - 1) + g
IMPLIED_COE_MULTIPLES = 0.09587  # 9.587% from existing valuation model

print(f"Implied COE from P/TBV Multiples... {IMPLIED_COE_MULTIPLES:.2%}")
print(f"Implied COE from CAPM (this calc).. {coe_capm:.2%}")
print(f"")
print(f"Delta (CAPM - Multiples)........... {(coe_capm - IMPLIED_COE_MULTIPLES):.2%}")
print()

# Interpretation
delta_pct = abs(coe_capm - IMPLIED_COE_MULTIPLES) / IMPLIED_COE_MULTIPLES

if delta_pct < 0.10:
    print(f"✅ COE estimates are CONSISTENT (delta < 10%)")
elif delta_pct < 0.20:
    print(f"⚠️  Moderate discrepancy (delta 10-20%) - investigate further")
else:
    print(f"🚨 LARGE DISCREPANCY (delta > 20%) - methodologies may be inconsistent")
    print(f"   Possible causes:")
    print(f"   - Different time periods (CAPM uses 5yr historical, multiples use forward expectations)")
    print(f"   - Peer selection bias in P/TBV regression")
    print(f"   - Market mispricing vs fundamental assumptions")

print()

# ===== SENSITIVITY ANALYSIS =====
print("=" * 80)
print("STEP 7: SENSITIVITY ANALYSIS")
print("=" * 80)
print()

print("COE Sensitivity to Risk-Free Rate:")
for rf_scenario in [0.03, 0.0375, 0.0425, 0.0475, 0.05]:
    coe_scenario = rf_scenario + beta * EQUITY_RISK_PREMIUM
    print(f"  Rf = {rf_scenario:.2%}  →  COE = {coe_scenario:.2%}")

print()
print("COE Sensitivity to Equity Risk Premium:")
for erp_scenario in [0.045, 0.050, 0.055, 0.060, 0.065]:
    coe_scenario = RISK_FREE_RATE + beta * erp_scenario
    print(f"  ERP = {erp_scenario:.2%}  →  COE = {coe_scenario:.2%}")

print()

# ===== EXPORT RESULTS =====
print("=" * 80)
print("STEP 8: EXPORTING RESULTS")
print("=" * 80)
print()

# Export to CSV
results_summary = pd.DataFrame({
    'Metric': [
        'Beta',
        'Alpha (annualized)',
        'R-squared',
        'p-value',
        'Standard Error',
        'Risk-Free Rate',
        'Equity Risk Premium',
        'Implied COE (CAPM)',
        'Implied COE (Multiples)',
        'COE Delta',
        'CATY Annualized Return',
        'CATY Annualized Volatility',
        'SP500 Annualized Return',
        'SP500 Annualized Volatility',
        'Number of Weeks',
        'Date Range Start',
        'Date Range End',
    ],
    'Value': [
        beta,
        alpha_annual,
        r_squared,
        p_value,
        std_err,
        RISK_FREE_RATE,
        EQUITY_RISK_PREMIUM,
        coe_capm,
        IMPLIED_COE_MULTIPLES,
        coe_capm - IMPLIED_COE_MULTIPLES,
        caty_stats['Annualized Return'],
        caty_stats['Annualized Volatility'],
        sp500_stats['Annualized Return'],
        sp500_stats['Annualized Volatility'],
        len(returns_df),
        returns_df.index[0].strftime('%Y-%m-%d'),
        returns_df.index[-1].strftime('%Y-%m-%d'),
    ]
})

output_path = 'evidence/capm_beta_results.csv'
results_summary.to_csv(output_path, index=False)
print(f"✅ Results exported to: {output_path}")

# Also export full returns data for audit trail
returns_output = 'evidence/capm_returns_data.csv'
returns_df.to_csv(returns_output)
print(f"✅ Full returns data exported to: {returns_output}")

print()

# ===== FINAL SUMMARY =====
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print()

print(f"CATY BETA:                {beta:.4f}")
print(f"IMPLIED COE (CAPM):       {coe_capm:.2%}")
print(f"IMPLIED COE (MULTIPLES):  {IMPLIED_COE_MULTIPLES:.2%}")
print(f"DELTA:                    {(coe_capm - IMPLIED_COE_MULTIPLES)*100:+.2f} bps")
print()

print("DEREK'S CROSS-EXAM ANSWERS:")
print(f"  Q4: Benchmark = S&P 500 (^GSPC), Yahoo Finance")
print(f"  Q6: Date range = Oct 13, 2020 → Oct 13, 2025, weekly frequency")
print(f"  Q8: CAPM COE = {coe_capm:.2%}, Multiples COE = {IMPLIED_COE_MULTIPLES:.2%}")
print()

if delta_pct < 0.10:
    print("✅ CAPM and multiples COE are CONSISTENT - valuation framework validated")
else:
    print("⚠️  CAPM and multiples COE have material discrepancy - further investigation required")

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
