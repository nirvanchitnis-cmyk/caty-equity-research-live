#!/usr/bin/env python3
"""
Remove Inline Styles Script - Convert to Utility Classes
Systematically replaces inline style attributes with semantic class names
"""

import re
from pathlib import Path

# Mapping of inline styles to utility classes
STYLE_REPLACEMENTS = [
    # Typography
    (r'style="font-size: 1\.1em; line-height: 1\.8;"', 'class="text-large"'),
    (r'style="font-size: 0\.95em; line-height: 1\.8;"', 'class="text-small"'),
    (r'style="line-height: 1\.8;"', 'class="line-height-relaxed"'),
    (r'style="font-size: 1\.3em; font-family: monospace; margin: 15px 0;"', 'class="text-mono"'),
    (r'style="margin-bottom: 20px; font-size: 1\.05em; line-height: 1\.8;"', 'class="text-intro"'),
    (r'style="margin-bottom: 20px; font-size: 1\.05em;"', 'class="text-intro"'),
    (r'style="font-size: 1\.2em; line-height: 1\.8;"', 'class="text-emphasis"'),
    (r'style="font-size: 1\.5em; font-weight: 700; margin: 15px 0;"', 'class="text-emphasis-large"'),
    (r'style="margin-top: 15px; font-style: italic; color: var\(--text-secondary\);"', 'class="text-note"'),
    (r'style="font-size: 1\.4em;"', 'class="font-size-14"'),
    (r'style="font-size: 1\.6em;"', 'class="font-size-16"'),
    (r'style="font-size: 1\.3em;"', 'class="font-size-13"'),
    (r'style="font-size: 1\.2em;"', 'class="font-size-12"'),
    (r'style="font-size: 1\.2em; line-height: 1\.3;"', 'class="font-size-12 line-height-13"'),
    (r'style="line-height: 1\.9; font-size: 1\.05em;"', 'class="line-height-19 font-size-12"'),
    (r'style="font-size: 1\.5em;"', 'class="font-size-15"'),

    # Colors
    (r'style="color: var\(--cathay-red\);"', 'class="text-danger"'),
    (r'style="color: var\(--bear-sell\);"', 'class="text-danger-dark"'),
    (r'style="color: var\(--success\);"', 'class="numeric-success"'),
    (r'style="color: var\(--danger\);"', 'class="numeric-danger"'),

    # Margins
    (r'style="margin: 20px 0;"', 'class="margin-y-20"'),
    (r'style="margin-top: 15px;"', 'class="margin-top-15"'),
    (r'style="margin-bottom: 20px;"', 'class="margin-bottom-20"'),
    (r'style="margin-top: 15px; line-height: 1\.8;"', 'class="margin-top-15 line-height-relaxed"'),

    # Borders
    (r'style="border-left-color: var\(--cathay-gold\);"', 'class="border-left-gold"'),
    (r'style="border-left-color: var\(--cathay-red\);"', 'class="border-left-danger"'),
    (r'style="border-left-color: var\(--info\);"', 'class="border-left-info"'),
    (r'style="border-left-color: var\(--success\);"', 'class="border-left-success"'),

    # Table rows
    (r'style="background: #FFF9E6;"', 'class="row-highlight-yellow"'),
    (r'style="background: #FFF9E5;"', 'class="row-highlight-yellow"'),
    (r'style="background: #FFEBEE;"', 'class="row-highlight-red"'),

    # Callout boxes
    (r'style="background: #FFF9E5; border-left: 5px solid var\(--cathay-gold\);"', 'class="callout-box-gold"'),
    (r'style="background: #E8F4F8; border-left: 4px solid var\(--info\);"', 'class="callout-box-info"'),

    # Badges
    (r'style="background: rgba\(45, 119, 56, 0\.15\); padding: 2px 8px; border-radius: 3px; font-weight: 600;"', 'class="badge-success"'),
    (r'style="background: rgba\(220, 38, 38, 0\.15\); padding: 2px 8px; border-radius: 3px;"', 'class="badge-danger"'),

    # Lists
    (r'style="line-height: 2\.0; font-family: monospace; font-size: 0\.95em;"', 'class="list-mono"'),

    # Specific patterns
    (r'style="margin-top: 20px; background: var\(--bg-tertiary\);"', 'class="highlight-box-spaced"'),
    (r'style="font-size: 1\.2em; font-family: \'Courier New\', monospace;"', 'class="source-label-mono"'),

    # Notice boxes
    (r'style="background: #E6F4FF; border-color: var\(--info\);"', 'class="notice-box-info"'),
    (r'style="background: #FFF9E6; border-color: var\(--warning\);"', 'class="notice-box-warning"'),
    (r'style="color: var\(--info\);"', 'class="notice-title-info"'),
    (r'style="color: var\(--warning\);"', 'class="notice-title-warning"'),

    # Text alignment
    (r'style="text-align: right;"', 'class="text-align-right"'),
    (r'style="text-align: center;"', 'class="text-align-center"'),

    # Display
    (r'style="display: block;"', 'class="display-block"'),
    (r'style="display: block; margin-top: 15px;"', 'class="display-block margin-top-15"'),

    # Text secondary variations
    (r'style="margin-bottom: 20px; color: var\(--text-secondary\);"', 'class="margin-bottom-20 text-secondary"'),
    (r'style="margin-bottom: 15px; font-size: 0\.9em; color: var\(--text-secondary\);"', 'class="text-secondary-small"'),
    (r'style="margin-top: 15px; font-size: 0\.85em; color: var\(--text-secondary\);"', 'class="text-secondary-tiny"'),
    (r'style="margin-top: 15px; font-size: 0\.85em; color: var\(--text-secondary\); text-align: center;"', 'class="text-secondary-tiny text-align-center"'),
    (r'style="margin: 15px 0; color: var\(--text-secondary\);"', 'class="text-secondary-margin"'),

    # Table rows
    (r'style="border-top: 2px solid var\(--cathay-red\);"', 'class="row-border-top-red"'),
    (r'style="background: rgba\(220, 38, 38, 0\.2\);"', 'class="row-danger-highlight"'),

    # SVG and plots
    (r'style="font-family: Arial, sans-serif;"', 'class="svg-chart"'),
    (r'style="background: white; position: relative;"', 'class="scatter-plot-white"'),

    # Source boxes with border colors
    (r'<div class="source-box" style="border-left-color: var\(--danger\);"', '<div class="source-box border-left-danger"'),
    (r'<div class="source-box" style="border-left-color: var\(--warning\);"', '<div class="source-box border-left-warning"'),

    # Lists with margins
    (r'style="margin-top: 10px; margin-left: 20px; line-height: 1\.8;"', 'class="list-spaced"'),
    (r'style="margin-left: 20px; line-height: 2;"', 'class="list-margin-20"'),

    # Table cells
    (r'style="padding-left: 30px;"', 'class="cell-indent-30"'),

    # Text colors for specific elements
    (r'<td class="numeric" style="color: var\(--text-secondary\);"', '<td class="numeric text-color-secondary"'),
    (r'style="color: var\(--text-secondary\);"', 'class="text-color-secondary"'),
    (r'style="color: var\(--text-primary\);"', 'class="text-color-primary"'),

    # Paragraphs with combined styles
    (r'style="margin-bottom: 20px; line-height: 1\.8; color: var\(--text-primary\);"', 'class="paragraph-intro-primary"'),

    # Badges
    (r'style="background: var\(--warning\); color: white; padding: 4px 12px; border-radius: 12px; font-size: 0\.85em; font-weight: 600;"', 'class="badge-warning"'),

    # Table rows - specific backgrounds
    (r'style="background: #F0F9FF;"', 'class="row-highlight-blue"'),
    (r'style="background: #FFF0F0;"', 'class="row-highlight-pink"'),
    (r'style="background: rgba\(255, 152, 0, 0\.15\);"', 'class="row-highlight-orange"'),
    (r'style="background: #fff3cd;"', 'class="row-highlight-yellow-alt"'),
    (r'style="background: var\(--bg-tertiary\); font-weight: 600;"', 'class="row-strong"'),

    # Table margins
    (r'<table style="margin-top: 20px;"', '<table class="table-margin-top"'),

    # Table row borders
    (r'style="border-top: 2px solid var\(--cathay-gold\);"', 'class="row-border-top-gold"'),

    # Callout titles (if not already covered)
    (r'<div class="callout-title" style="font-size: 1\.3em; color: var\(--cathay-red\);"', '<div class="callout-title"'),

    # Notice titles
    (r'<div class="notice-title" style="color: var\(--info\);"', '<div class="notice-title notice-title-info"'),
    (r'<div class="notice-title" style="color: var\(--warning\);"', '<div class="notice-title notice-title-warning"'),

    # Formulas and monospace
    (r'style="font-family: monospace; font-size: 1\.2em; margin: 15px 0;"', 'class="formula-mono-large"'),
    (r'style="font-family: monospace; font-size: 1\.1em; margin: 15px 0;"', 'class="formula-mono-medium"'),
    (r'style="font-family: monospace; margin: 15px 0;"', 'class="formula-mono"'),

    # Paragraphs
    (r'style="font-size: 1\.1em;"', 'class="paragraph-11"'),

    # Lists
    (r'style="margin-top: 10px; margin-left: 20px;"', 'class="list-simple"'),

    # Table cells with colspan
    (r'style="text-align: center; color: var\(--text-secondary\); padding: 20px;"', 'class="cell-center-secondary"'),

    # Final edge cases
    (r'<ul style="margin-left: 20px; margin-top: 10px;"', '<ul class="list-reversed"'),
    (r'style="text-align: center; font-size: 1\.3em; margin-bottom: 30px;"', 'class="text-center-large"'),
    (r'<pre style="font-family: monospace; white-space: pre;"', '<pre class="pre-mono"'),
    (r'style="background: rgba\(196, 30, 58, 0\.1\);"', 'class="row-red-subtle"'),
    (r'style="background: var\(--bg-tertiary\);"', 'class="row-tertiary"'),
]

def convert_inline_styles(html_path: Path) -> tuple[str, int]:
    """
    Convert inline styles to utility classes.

    Returns:
        tuple: (converted_html, count_of_replacements)
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = 0

    for pattern, replacement in STYLE_REPLACEMENTS:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            replacements += matches
            content = re.sub(pattern, replacement, content)

    return content, replacements


def main():
    """Convert all CATY_*.html modules to remove inline styles."""

    base_dir = Path(__file__).parent.parent

    # Skip CATY_12 (already done) and index.html (already done)
    modules = sorted([m for m in base_dir.glob('CATY_*.html')
                      if m.name != 'CATY_12_valuation_model.html'])

    print("=" * 70)
    print("INLINE STYLE REMOVAL - Module Sweep")
    print("=" * 70)
    print()

    total_replacements = 0

    for module_path in modules:
        converted_html, count = convert_inline_styles(module_path)

        if count > 0:
            # Write converted file
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(converted_html)

            total_replacements += count
            print(f"✓ {module_path.name}: {count} inline styles removed")
        else:
            print(f"  {module_path.name}: No inline styles found")

    print()
    print("=" * 70)
    print(f"TOTAL: {total_replacements} inline styles replaced with utility classes")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
