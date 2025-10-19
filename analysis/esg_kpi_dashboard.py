#!/usr/bin/env python3
"""
ESG KPI Dashboard - Data Module and Analysis

Loads ESG metrics from evidence/esg_kpi_data.json and provides:
1. KPI retrieval and comparison functions
2. Time series trending
3. Peer benchmarking
4. Valuation impact calculations
5. Dashboard export (HTML, JSON, CSV)

Usage:
    python3 analysis/esg_kpi_dashboard.py                    # Print dashboard
    python3 analysis/esg_kpi_dashboard.py --export-html      # Generate HTML
    python3 analysis/esg_kpi_dashboard.py --export-csv       # Generate CSV
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class ESGDashboard:
    """ESG KPI Dashboard for CATY"""

    def __init__(self, data_path: str = "evidence/esg_kpi_data.json"):
        """Load ESG data from JSON"""
        base_path = Path(__file__).parent.parent
        full_path = base_path / data_path

        if not full_path.exists():
            raise FileNotFoundError(f"ESG data file not found: {full_path}")

        with open(full_path, 'r') as f:
            self.data = json.load(f)

        self.last_updated = self.data['metadata']['last_updated']

    def get_kpi(self, category: str, subcategory: str, metric: str) -> Dict[str, Any]:
        """
        Retrieve a specific KPI

        Example: get_kpi('social', 'cra_performance', 'cra_rating')
        """
        try:
            return self.data[category][subcategory][metric]
        except KeyError:
            return {}

    def get_esg_scores(self) -> Dict[str, float]:
        """Get E/S/G component scores and composite"""
        return {
            'environmental': self.data['environmental']['esg_score_environmental']['value'],
            'social': self.data['social']['esg_score_social']['value'],
            'governance': self.data['governance']['esg_score_governance']['value'],
            'composite': self.data['esg_aggregate']['esg_composite_score']['value']
        }

    def get_material_weaknesses(self) -> List[Dict[str, Any]]:
        """Identify material weaknesses (high materiality + risk flags)"""
        weaknesses = []

        # Scan all KPIs for risk flags
        for category in ['environmental', 'social', 'governance']:
            cat_data = self.data[category]

            for subcat_key, subcat_data in cat_data.items():
                if isinstance(subcat_data, dict):
                    for metric_key, metric_data in subcat_data.items():
                        if isinstance(metric_data, dict):
                            if metric_data.get('risk_flag'):
                                weaknesses.append({
                                    'category': category.upper()[0],
                                    'subcategory': subcat_key,
                                    'metric': metric_key,
                                    'value': metric_data.get('value'),
                                    'risk_flag': metric_data['risk_flag'],
                                    'materiality': metric_data.get('materiality', 'UNKNOWN')
                                })

        return weaknesses

    def get_peer_comparison(self) -> Dict[str, Any]:
        """Get peer ESG scores and CATY ranking"""
        peer_data = self.data['peer_comparison']
        scores = peer_data['esg_scores']

        caty_score = scores['CATY']
        median_score = scores['median']

        # Calculate percentile (include CATY in ranking)
        all_scores = [scores[peer] for peer in peer_data['peers']] + [caty_score]
        all_scores.sort()
        caty_rank = all_scores.index(caty_score) + 1
        percentile = caty_rank / len(all_scores) * 100

        return {
            'caty_score': caty_score,
            'peer_median': median_score,
            'gap': caty_score - median_score,
            'percentile': percentile,
            'rank': caty_rank,
            'total': len(all_scores),
            'peers': peer_data['peers'],
            'scores': scores
        }

    def get_valuation_impact(self) -> Dict[str, Any]:
        """Get ESG-adjusted valuation metrics"""
        return self.data['esg_aggregate']['valuation_impact']

    def get_coe_adjustments(self) -> Dict[str, float]:
        """Get COE adjustments by ESG component"""
        return self.data['esg_aggregate']['esg_coe_adjustment_bps']

    def print_dashboard(self):
        """Print formatted dashboard to stdout"""
        print("\n" + "="*70)
        print("CATY ESG KPI DASHBOARD")
        print(f"Last Updated: {self.last_updated}")
        print("="*70 + "\n")

        # ESG Scores
        scores = self.get_esg_scores()
        print("ESG SCORES (0-10 scale):")
        print(f"  Environmental (E):  {scores['environmental']:.1f} / 10")
        print(f"  Social (S):         {scores['social']:.1f} / 10")
        print(f"  Governance (G):     {scores['governance']:.1f} / 10")
        print(f"  Composite:          {scores['composite']:.1f} / 10")
        print()

        # Peer Comparison
        peer_comp = self.get_peer_comparison()
        print(f"PEER COMPARISON:")
        print(f"  CATY Score:         {peer_comp['caty_score']:.1f}")
        print(f"  Peer Median:        {peer_comp['peer_median']:.1f}")
        print(f"  Gap:                {peer_comp['gap']:+.1f} pts")
        print(f"  Percentile:         {peer_comp['percentile']:.0f}th")
        print()

        # Material Weaknesses
        weaknesses = self.get_material_weaknesses()
        print(f"MATERIAL WEAKNESSES ({len(weaknesses)}):")
        for w in weaknesses:
            print(f"  [{w['category']}] {w['metric']}: {w['value']} ({w['risk_flag']})")
        print()

        # Valuation Impact
        val_impact = self.get_valuation_impact()
        print("VALUATION IMPACT:")
        print(f"  ESG-Neutral Target: ${val_impact['esg_neutral_gordon_target']:.2f}")
        print(f"  ESG-Adjusted Target: ${val_impact['esg_adjusted_gordon_target']:.2f}")
        print(f"  ESG Discount:       {val_impact['esg_discount_pct']:.1f}% (${val_impact['esg_discount_per_share']:.2f}/share)")
        print()

        # COE Adjustments
        coe_adj = self.get_coe_adjustments()
        print("COE ADJUSTMENTS (bps):")
        print(f"  Environmental:      +{coe_adj['environmental_premium']} bps (climate risk)")
        print(f"  Social:             {coe_adj['social_offset']:+} bps (community moat)")
        print(f"  Governance:         +{coe_adj['governance_premium']} bps (independence gap)")
        print(f"  Net ESG Premium:    +{coe_adj['net_esg_premium']} bps")
        print(f"  Base COE:           {coe_adj['base_coe_pct']:.3f}%")
        print(f"  ESG-Adjusted COE:   {coe_adj['esg_adjusted_coe_pct']:.3f}%")
        print()

        # Key Initiatives
        initiatives = self.data['key_initiatives']
        print(f"KEY INITIATIVES ({len(initiatives)}):")
        for init in initiatives:
            status_emoji = {
                'PENDING': '⏳',
                'ON_TRACK': '✅',
                'RECOMMENDED': '💡'
            }.get(init['status'], '⚠️')
            print(f"  {status_emoji} {init['initiative']}: {init['target']}")
        print()

        print("="*70 + "\n")

    def export_csv(self, output_path: str = "evidence/esg_kpi_summary.csv"):
        """Export key metrics to CSV"""
        import csv

        base_path = Path(__file__).parent.parent
        full_path = base_path / output_path

        rows = []

        # E metrics
        cre_exp = self.get_kpi('environmental', 'climate_risk', 'cre_portfolio_exposure_pct')
        rows.append(['E', 'CRE Portfolio Exposure', f"{cre_exp['value']}%", cre_exp['materiality']])

        office_exp = self.get_kpi('environmental', 'climate_risk', 'cre_office_exposure_mm')
        rows.append(['E', 'CRE Office Exposure', f"${office_exp['value']}M", office_exp['materiality']])

        # S metrics
        cra = self.get_kpi('social', 'cra_performance', 'cra_rating')
        rows.append(['S', 'CRA Rating', cra['value'], cra['materiality']])

        dep_beta = self.get_kpi('social', 'competitive_moat_metrics', 'deposit_beta')
        rows.append(['S', 'Deposit Beta', dep_beta['value'], dep_beta['materiality']])

        # G metrics
        independence = self.get_kpi('governance', 'board_composition', 'board_independence_pct')
        rows.append(['G', 'Board Independence', f"{independence['value']}%", independence['materiality']])

        iss = self.get_kpi('governance', 'governance_quality', 'iss_governance_score')
        rows.append(['G', 'ISS Governance Score', f"{iss['value']}/10", iss['materiality']])

        # Aggregate
        scores = self.get_esg_scores()
        rows.append(['Aggregate', 'Composite ESG Score', f"{scores['composite']}/10", 'HIGH'])

        with open(full_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Metric', 'Value', 'Materiality'])
            writer.writerows(rows)

        print(f"CSV exported to: {full_path}")


def main():
    """CLI entry point"""
    dashboard = ESGDashboard()

    if '--export-csv' in sys.argv:
        dashboard.export_csv()
    else:
        dashboard.print_dashboard()


if __name__ == '__main__':
    main()
