"""
Quantify impact of CATY's elevated CRE concentration (+24.6 ppts above peer median)
on NCOs, provisions, and capital erosion.
"""

# CATY Data (Q2 2025)
caty_cre_pct = 52.4
peer_median_cre_pct = 27.8
caty_total_loans = 19785  # Million
caty_cre_loans = 10363    # Million
caty_cet1_ratio = 13.35   # %
caty_rwa = 19118.5        # Million

# CRE concentration gap
cre_gap_ppts = caty_cre_pct - peer_median_cre_pct  # 24.6 ppts

# Through-cycle NCO assumptions
through_cycle_nco_bps = 42.8  # All loans
cre_nco_premium_bps = 15.0    # CRE loans experience 15 bps higher NCO vs non-CRE

# Calculate incremental NCO from CRE concentration
excess_cre_loans = caty_total_loans * (cre_gap_ppts / 100)  # Loans above peer median CRE level
incremental_nco_annual = excess_cre_loans * (cre_nco_premium_bps / 10000)  # Million

# Provision impact (assume build to 1.0% ACL on incremental CRE)
target_acl_on_excess_cre = excess_cre_loans * 0.01
current_acl_on_excess = excess_cre_loans * 0.00842  # Current ACL/Loans ratio
incremental_provision_build = target_acl_on_excess_cre - current_acl_on_excess

# Capital impact
tax_rate = 0.20
after_tax_nco = incremental_nco_annual * (1 - tax_rate)
cet1_burn_bps = (after_tax_nco / caty_rwa) * 10000

print("═" * 80)
print("CRE CONCENTRATION IMPACT ANALYSIS")
print("═" * 80)
print()
print(f"CATY CRE Concentration: {caty_cre_pct}%")
print(f"Peer Median CRE:         {peer_median_cre_pct}%")
print(f"Gap:                     +{cre_gap_ppts:.1f} ppts")
print()
print(f"Total Loans:             ${caty_total_loans:,.0f}M")
print(f"Excess CRE Loans:        ${excess_cre_loans:,.0f}M ({cre_gap_ppts:.1f}% × ${caty_total_loans:,.0f}M)")
print()
print("INCREMENTAL NCO IMPACT (Annual):")
print(f"  CRE NCO Premium:       {cre_nco_premium_bps} bps higher than non-CRE")
print(f"  Incremental NCO:       ${incremental_nco_annual:.1f}M/year")
print(f"  After-tax impact:      ${after_tax_nco:.1f}M/year")
print(f"  CET1 burn:             {cet1_burn_bps:.0f} bps/year")
print()
print("RESERVE BUILD REQUIREMENT:")
print(f"  Target ACL (1.0%):     ${target_acl_on_excess_cre:.1f}M")
print(f"  Current ACL:           ${current_acl_on_excess:.1f}M")
print(f"  Incremental provision: ${incremental_provision_build:.1f}M one-time")
print()
print("TOTAL CAPITAL IMPACT (3-year):")
total_3y_impact = (after_tax_nco * 3) + (incremental_provision_build * (1 - tax_rate))
cet1_burn_3y_bps = (total_3y_impact / caty_rwa) * 10000
print(f"  3-year NCO impact:     ${after_tax_nco * 3:.1f}M")
print(f"  Provision build (AT):  ${incremental_provision_build * (1 - tax_rate):.1f}M")
print(f"  Total impact:          ${total_3y_impact:.1f}M")
print(f"  CET1 erosion:          {cet1_burn_3y_bps:.0f} bps")
print(f"  New CET1 ratio:        {caty_cet1_ratio - (cet1_burn_3y_bps / 100):.2f}%")
print()
print("THESIS IMPLICATION:")
print(f"  CATY's +24.6 ppt CRE concentration increases vulnerability to")
print(f"  through-cycle credit normalization. Incremental {cet1_burn_bps:.0f} bps annual")
print(f"  CET1 burn compounds the NCO normalization thesis.")
print()
print("═" * 80)
