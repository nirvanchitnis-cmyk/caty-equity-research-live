#!/usr/bin/env python3
"""
Reconciliation Guard Script - Validates Published Numbers vs. Script Outputs

This script ensures that headline numbers in README.md and index.html match
the outputs from valuation_bridge_final.py and probability_weighted_valuation.py.

Exit codes:
  0 - All checks passed
  1 - Discrepancies found
  2 - Script execution error

Usage:
  python3 analysis/reconciliation_guard.py

Integration:
  - Wire into monitoring runbook post-Q3 updates
  - Can be added to pre-commit hooks or CI/CD pipeline
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def run_script(script_path: str) -> Tuple[str, int]:
    """Run a Python script and capture output"""
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout, result.returncode
    except subprocess.TimeoutExpired:
        return "", 2
    except Exception as e:
        print(f"{Colors.RED}Error running {script_path}: {e}{Colors.RESET}")
        return "", 2


def extract_valuation_bridge_outputs(output: str) -> Dict[str, float]:
    """Extract target prices from valuation_bridge_final.py output"""
    data = {}

    # PATH A (Regression): $56.50 (+23.1%)
    match = re.search(r'PATH A \(Regression\): \$(\d+\.\d+)', output)
    if match:
        data['regression_target'] = float(match.group(1))

    # PATH B (Normalized): $39.32 (-14.3%)
    match = re.search(r'PATH B \(Normalized\): \$(\d+\.\d+)', output)
    if match:
        data['normalized_target'] = float(match.group(1))

    return data


def extract_probability_outputs(output: str) -> Dict[str, float]:
    """Extract Wilson 95% target from probability_weighted_valuation.py output"""
    data = {}

    # 95% Upper Bound: P(Current)=74.0%, P(Normalized)=26.0%, Target=$48.70, Return=+3.3%
    match = re.search(r'Wilson Weighted Target: \$(\d+\.\d+) \(([+-]\d+\.\d+)%\)', output)
    if match:
        data['wilson_target'] = float(match.group(1))
        data['wilson_return'] = float(match.group(2))

    return data


def extract_published_numbers() -> Dict[str, float]:
    """Extract published numbers from README.md and index.html"""
    data = {}

    # Read README.md
    readme_path = Path(__file__).parent.parent / 'README.md'
    if readme_path.exists():
        content = readme_path.read_text()

        # Expected Price: **$48.70 (+3.3%)**
        match = re.search(r'Expected Price:.*\*\*\$(\d+\.\d+)\s*\(([+-]\d+\.\d+)%\)', content)
        if match:
            data['readme_wilson_target'] = float(match.group(1))
            data['readme_wilson_return'] = float(match.group(2))

        # Regression (Current Earnings) | ... | **$56.50** | **+23.1%**
        match = re.search(r'Regression.*\*\*\$(\d+\.\d+)\*\*.*\*\*\+(\d+\.\d+)%\*\*', content)
        if match:
            data['readme_regression_target'] = float(match.group(1))

        # Normalization (Through-Cycle) | ... | **$39.32** | **-14.3%**
        match = re.search(r'(Gordon Growth|Normalization).*?\*\*\$(\d+\.\d+)\*\*', content)
        if match:
            data['readme_normalized_target'] = float(match.group(2))

    # IRC Blended value in valuation table
        match = re.search(r'IRC Blended.*\*\*\$(\d+\.\d+)\*\*', content)
        if match:
            data['readme_irc_blended'] = float(match.group(1))

    # Read index.html
    index_path = Path(__file__).parent.parent / 'index.html'
    if index_path.exists():
        content = index_path.read_text()

        # Wilson 95% Expected Value (support reconciliation or scenario tables)
        wilson_match = re.search(
            r'<td><strong>Wilson 95%.*?</td>\s*<td class="numeric">\$(\d+\.\d+)</td>',
            content,
            re.DOTALL
        )
        if wilson_match:
            data['index_wilson_target'] = float(wilson_match.group(1))

        # IRC Blended (support both metric-card and table variants). Collect duplicates for consistency checks.
        irc_values: List[float] = []
        for m in re.finditer(r'<div class="metric-label">IRC Blended</div>\s*<div class="metric-value">\$(\d+\.\d+)</div>', content, re.DOTALL):
            irc_values.append(float(m.group(1)))
        for m in re.finditer(r'<td[^>]*>\s*<strong>IRC Blended(?: Target)?</strong>\s*</td>\s*<td[^>]*class="numeric"[^>]*>\$(\d+\.\d+)</td>', content, re.DOTALL):
            irc_values.append(float(m.group(1)))
        if irc_values:
            data['index_irc_blended'] = irc_values[0]
            data['index_irc_blended_all'] = irc_values

        # SUMM table cross-check values if present
        summ_patterns = {
            'summ_wilson': r'<td[^>]*>\s*<strong>Wilson 95% Target</strong>\s*</td>\s*<td[^>]*class="numeric"[^>]*>\$(\d+\.\d+)</td>',
            'summ_irc': r'<td[^>]*>\s*<strong>IRC Blended</strong>\s*</td>\s*<td[^>]*class="numeric"[^>]*>\$(\d+\.\d+)</td>',
            'summ_regression': r'<td[^>]*>\s*<strong>Regression Target</strong>\s*</td>\s*<td[^>]*class="numeric"[^>]*>\$(\d+\.\d+)</td>',
            'summ_normalized': r'<td[^>]*>\s*<strong>Normalized Target</strong>\s*</td>\s*<td[^>]*class="numeric"[^>]*>\$(\d+\.\d+)</td>',
        }
        for key, pattern in summ_patterns.items():
            m = re.search(pattern, content, re.DOTALL)
            if m:
                data[key] = float(m.group(1))

        # Fallback: row-based extraction for SUMM table when class attributes differ
        def _summ_value(label: str):
            row = re.search(
                rf'<tr[^>]*>.*?<td[^>]*>\s*<strong>{label}</strong>\s*</td>(?P<cells>.*?)</tr>',
                content,
                re.DOTALL,
            )
            if not row:
                return None
            cells = row.group('cells')
            m2 = re.search(r'>\$(\d+\.\d+)<', cells)
            return float(m2.group(1)) if m2 else None

        for key, label in {
            'summ_wilson': 'Wilson 95% Target',
            'summ_irc': 'IRC Blended',
            'summ_regression': 'Regression Target',
            'summ_normalized': 'Normalized Target',
        }.items():
            if key not in data:
                val = _summ_value(label)
                if val is not None:
                    data[key] = val

    return data


def compare_values(label: str, published: float, calculated: float, tolerance: float = 0.50) -> bool:
    """Compare published vs calculated values with tolerance"""
    diff = abs(published - calculated)

    if diff <= tolerance:
        print(f"  {Colors.GREEN}✓{Colors.RESET} {label}: ${published:.2f} (published) = ${calculated:.2f} (calculated)")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} {label}: ${published:.2f} (published) ≠ ${calculated:.2f} (calculated) "
              f"[Δ ${diff:.2f}]")
        return False


def main():
    """Main reconciliation workflow"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}CATY Valuation Reconciliation Guard{Colors.RESET}")
    print(f"{'='*60}\n")

    all_passed = True

    # Step 1: Run valuation scripts
    print(f"{Colors.BOLD}Step 1: Running valuation scripts...{Colors.RESET}")

    bridge_output, bridge_code = run_script('analysis/valuation_bridge_final.py')
    if bridge_code != 0:
        print(f"{Colors.RED}Error running valuation_bridge_final.py (exit code {bridge_code}){Colors.RESET}")
        sys.exit(2)

    prob_output, prob_code = run_script('analysis/probability_weighted_valuation.py')
    if prob_code != 0:
        print(f"{Colors.RED}Error running probability_weighted_valuation.py (exit code {prob_code}){Colors.RESET}")
        sys.exit(2)

    print(f"{Colors.GREEN}✓ Scripts executed successfully{Colors.RESET}\n")

    # Step 2: Extract calculated values
    print(f"{Colors.BOLD}Step 2: Extracting calculated values...{Colors.RESET}")

    bridge_data = extract_valuation_bridge_outputs(bridge_output)
    prob_data = extract_probability_outputs(prob_output)

    print(f"  Regression Target: ${bridge_data.get('regression_target', 0):.2f}")
    print(f"  Normalized Target: ${bridge_data.get('normalized_target', 0):.2f}")
    print(f"  Wilson 95% Target: ${prob_data.get('wilson_target', 0):.2f}")
    print(f"  Wilson Return: {prob_data.get('wilson_return', 0):+.1f}%\n")

    # Step 3: Extract published values
    print(f"{Colors.BOLD}Step 3: Extracting published values...{Colors.RESET}")

    published = extract_published_numbers()

    print(f"  README Wilson Target: ${published.get('readme_wilson_target', 0):.2f}")
    print(f"  README Regression: ${published.get('readme_regression_target', 0):.2f}")
    print(f"  README Normalized: ${published.get('readme_normalized_target', 0):.2f}")
    print(f"  index.html Wilson: ${published.get('index_wilson_target', 0):.2f}")
    print(f"  index.html IRC Blended: ${published.get('index_irc_blended', 0):.2f}\n")

    # Step 4: Reconciliation checks
    print(f"{Colors.BOLD}Step 4: Reconciliation checks...{Colors.RESET}\n")

    checks: List[Tuple[str, float, float]] = [
        ("Wilson Target (README)",
         published.get('readme_wilson_target', 0),
         prob_data.get('wilson_target', 0)),

        ("Wilson Target (index.html)",
         published.get('index_wilson_target', 0),
         prob_data.get('wilson_target', 0)),

        ("Regression Target (README)",
         published.get('readme_regression_target', 0),
         bridge_data.get('regression_target', 0)),

        ("Normalized Target (README)",
         published.get('readme_normalized_target', 0),
         bridge_data.get('normalized_target', 0)),
    ]

    for label, pub, calc in checks:
        if pub == 0 or calc == 0:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {label}: Missing data (skipped)")
            continue

        if not compare_values(label, pub, calc):
            all_passed = False

    # Step 5: IRC Blended validation (manual calculation)
    print(f"\n{Colors.BOLD}Step 5: IRC Blended validation...{Colors.RESET}\n")

    # IRC Blended = 60% RIM + 10% DDM + 30% Relative
    # RIM = $50.08 (from RESIDUAL_INCOME_VALUATION.md)
    # DDM = $45.12 (hardcoded)
    # Relative = $56.50 (regression)
    rim_target = 50.08
    ddm_target = 45.12
    relative_target = bridge_data.get('regression_target', 56.50)

    calculated_irc_blended = 0.60 * rim_target + 0.10 * ddm_target + 0.30 * relative_target
    published_irc_blended = published.get('index_irc_blended', 0)

    if published_irc_blended > 0:
        if not compare_values("IRC Blended", published_irc_blended, calculated_irc_blended):
            all_passed = False
        # SUMM table IRC cross-check
        if published.get('summ_irc', 0) > 0:
            if not compare_values("IRC Blended (SUMM)", published['summ_irc'], calculated_irc_blended):
                all_passed = False
        # Duplicate index values should be internally consistent
        if isinstance(published.get('index_irc_blended_all'), list):
            for v in published['index_irc_blended_all']:
                if not compare_values("IRC Blended (duplicate)", v, published_irc_blended):
                    all_passed = False
    else:
        print(f"  {Colors.YELLOW}⚠{Colors.RESET} IRC Blended: Not found in index.html (expected ${calculated_irc_blended:.2f})")

    # Step 6: SUMM table cross-check
    if any(k.startswith('summ_') for k in published.keys()):
        print(f"\n{Colors.BOLD}Step 6: SUMM table cross-check...{Colors.RESET}")
        if published.get('summ_wilson', 0) > 0:
            if not compare_values("Wilson Target (SUMM)", published['summ_wilson'], prob_data.get('wilson_target', 0)):
                all_passed = False
        if published.get('summ_regression', 0) > 0:
            if not compare_values("Regression Target (SUMM)", published['summ_regression'], bridge_data.get('regression_target', 0)):
                all_passed = False
        if published.get('summ_normalized', 0) > 0:
            if not compare_values("Normalized Target (SUMM)", published['summ_normalized'], bridge_data.get('normalized_target', 0)):
                all_passed = False

    # Final summary
    print(f"\n{'='*60}")
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All reconciliation checks PASSED{Colors.RESET}")
        print(f"\nPublished numbers match script outputs within tolerance (±$0.50).")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Reconciliation FAILED{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Action required:{Colors.RESET}")
        print(f"  1. Rerun valuation scripts: python3 analysis/valuation_bridge_final.py")
        print(f"  2. Update README.md and index.html with corrected values")
        print(f"  3. Commit changes with descriptive message")
        sys.exit(1)


if __name__ == '__main__':
    main()
