#!/usr/bin/env python3
"""
Module Conversion Script - Extract CSS/JS to Shared Assets
Converts CATY_*.html modules to use styles/caty-equity-research.css and scripts/theme-toggle.js
"""

import re
from pathlib import Path

def convert_module(html_path: Path) -> tuple[str, dict]:
    """
    Convert a module HTML file to use shared CSS/JS assets.

    Returns:
        tuple: (converted_html, stats_dict)
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_lines = content.count('\n')
    stats = {
        'original_lines': original_lines,
        'style_removed': 0,
        'script_removed': 0,
        'inline_styles_replaced': 0
    }

    # STEP 1: Replace embedded <style> block with link to shared CSS
    style_pattern = r'    <style>.*?    </style>\n'
    style_match = re.search(style_pattern, content, re.DOTALL)

    if style_match:
        stats['style_removed'] = style_match.group(0).count('\n')
        replacement = '    <link rel="stylesheet" href="styles/caty-equity-research.css">\n'
        content = re.sub(style_pattern, replacement, content, count=1, flags=re.DOTALL)

    # STEP 2: Replace embedded theme toggle <script> with link to shared JS
    # Find the script block that contains toggleTheme function
    script_pattern = r'    <script>\n        function toggleTheme\(\).*?    </script>\n'
    script_match = re.search(script_pattern, content, re.DOTALL)

    if script_match:
        stats['script_removed'] = script_match.group(0).count('\n')
        replacement = '    <script src="scripts/theme-toggle.js"></script>\n'
        content = re.sub(script_pattern, replacement, content, count=1, flags=re.DOTALL)

    # STEP 3: Replace common inline styles with semantic classes
    # (Same patterns as used in index.html conversion)

    inline_replacements = [
        # Module cards
        (r'<a href="([^"]+)"[^>]*style="display: block; background: var\(--bg-tertiary\); padding: 20px;[^"]*"[^>]*>',
         r'<a href="\1" class="module-card">'),

        # Grids
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(200px, 1fr\)\); gap: 20px;">',
         r'<div class="grid-auto-fit-200">'),
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(250px, 1fr\)\); gap: 20px;">',
         r'<div class="grid-auto-fit-250">'),
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(300px, 1fr\)\); gap: 15px;">',
         r'<div class="module-grid">'),

        # Dashboard grids
        (r'<div style="display: grid; grid-template-columns: repeat\(4, 1fr\); gap: 16px; margin: 24px 0;">',
         r'<div class="dashboard-grid">'),

        # Tables
        (r'<div style="overflow-x: auto; margin: 20px 0;">',
         r'<div class="table-container">'),

        # Sections
        (r'<section style="margin-bottom: 50px;">',
         r'<section class="content-section">'),

        # Cards with border-left
        (r'<div style="background: var\(--bg-secondary\); padding: 20px; border-radius: 8px; border-left: 4px solid var\(--success\);">',
         r'<div class="metric-card metric-card-success">'),
        (r'<div style="background: var\(--bg-secondary\); padding: 20px; border-radius: 8px; border-left: 4px solid var\(--danger\);">',
         r'<div class="metric-card metric-card-danger">'),
        (r'<div style="background: var\(--bg-secondary\); padding: 20px; border-radius: 8px; border-left: 4px solid var\(--warning\);">',
         r'<div class="metric-card metric-card-warning">'),
        (r'<div style="background: var\(--bg-secondary\); padding: 20px; border-radius: 8px; border-left: 4px solid var\(--cathay-gold\);">',
         r'<div class="metric-card metric-card-gold">'),

        # Generic cards
        (r'<div style="background: var\(--bg-secondary\); padding: 20px; border-radius: 8px;">',
         r'<div class="metric-card">'),

        # Text alignment
        (r'<div style="text-align: center;">',
         r'<div class="text-center">'),
        (r'<p style="text-align: center;">',
         r'<p class="text-center">'),

        # Dashboard cards
        (r'<div style="background: rgba\(255,255,255,0\.05\); padding: 16px; border-radius: 8px;">',
         r'<div class="dashboard-card">'),

        # Price target grids
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(200px, 1fr\)\); gap: 12px; margin: 20px 0;">',
         r'<div class="price-target-grid">'),
    ]

    for pattern, replacement in inline_replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            stats['inline_styles_replaced'] += matches
            content = re.sub(pattern, replacement, content)

    # Count final lines
    stats['final_lines'] = content.count('\n')
    stats['lines_removed'] = original_lines - stats['final_lines']

    return content, stats


def main():
    """Convert all CATY_*.html modules to use shared CSS/JS."""

    base_dir = Path(__file__).parent.parent
    modules = sorted(base_dir.glob('CATY_*.html'))

    print("=" * 70)
    print("MODULE CONVERSION - Shared CSS/JS Migration")
    print("=" * 70)
    print()

    total_stats = {
        'files_converted': 0,
        'total_lines_removed': 0,
        'total_style_lines': 0,
        'total_script_lines': 0,
        'total_inline_replaced': 0
    }

    for module_path in modules:
        print(f"Converting {module_path.name}...", end=" ")

        converted_html, stats = convert_module(module_path)

        # Write converted file
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(converted_html)

        # Update totals
        total_stats['files_converted'] += 1
        total_stats['total_lines_removed'] += stats['lines_removed']
        total_stats['total_style_lines'] += stats['style_removed']
        total_stats['total_script_lines'] += stats['script_removed']
        total_stats['total_inline_replaced'] += stats['inline_styles_replaced']

        print(f"✓ ({stats['lines_removed']:+d} lines, {stats['inline_styles_replaced']} inline styles)")

    print()
    print("=" * 70)
    print("CONVERSION SUMMARY")
    print("=" * 70)
    print(f"Files converted:       {total_stats['files_converted']}")
    print(f"Total lines removed:   {total_stats['total_lines_removed']:,}")
    print(f"  - CSS removed:       {total_stats['total_style_lines']:,} lines")
    print(f"  - JS removed:        {total_stats['total_script_lines']:,} lines")
    print(f"Inline styles fixed:   {total_stats['total_inline_replaced']}")
    print()
    print("✅ All modules now use:")
    print("   - styles/caty-equity-research.css (shared stylesheet)")
    print("   - scripts/theme-toggle.js (shared JavaScript)")
    print()


if __name__ == '__main__':
    main()
