#!/usr/bin/env python3
"""
Headless PDF Validation - No GUI Required
Generates PDFs via headless Chrome and validates output
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# Paths
base_dir = Path(__file__).parent.parent
log_path = base_dir / 'logs' / 'automation_run.log'

def append_log(entry: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    with log_path.open('a', encoding='utf-8') as fh:
        fh.write(f"[{timestamp}] {entry}\n")

def validate_print_output():
    """
    Validate PDF generation without GUI
    Uses headless Chrome to generate PDFs and check output
    """

    print("=" * 70)
    print("PDF VALIDATION - Headless Chrome")
    print("=" * 70)
    print(f"Run Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    test_files = [
        {
            'name': 'index.html',
            'path': base_dir / 'index.html',
            'pdf_output': base_dir / 'test_output' / 'index.pdf',
            'expected_min_kb': 200,
            'expected_max_kb': 5000
        },
        {
            'name': 'CATY_12_valuation_model.html',
            'path': base_dir / 'CATY_12_valuation_model.html',
            'pdf_output': base_dir / 'test_output' / 'CATY_12.pdf',
            'expected_min_kb': 100,
            'expected_max_kb': 2000
        }
    ]

    # Create output directory
    output_dir = base_dir / 'test_output'
    output_dir.mkdir(exist_ok=True)

    results = []

    for test in test_files:
        print(f"Testing: {test['name']}")
        print("-" * 70)

        # Generate PDF using headless Chrome
        file_url = f"file://{test['path']}"
        pdf_path = test['pdf_output']

        # Use Chrome headless mode to print to PDF
        try:
            cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + str(pdf_path),
                '--no-pdf-header-footer',
                file_url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if pdf_path.exists():
                file_size = pdf_path.stat().st_size
                size_kb = file_size / 1024

                print(f"   ✅ PDF Generated: {pdf_path.name}")
                print(f"   File Size: {size_kb:.1f} KB")

                # Validate size is reasonable
                if test['expected_min_kb'] <= size_kb <= test['expected_max_kb']:
                    print(f"   ✅ Size within expected range ({test['expected_min_kb']}-{test['expected_max_kb']} KB)")
                    status = "PASS"
                else:
                    print(f"   ⚠️  Size outside expected range ({size_kb:.1f} KB not in {test['expected_min_kb']}-{test['expected_max_kb']} KB)")
                    status = "WARN_SIZE"

                # Additional checks using pdfinfo if available
                try:
                    info_cmd = ['pdfinfo', str(pdf_path)]
                    info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=5)

                    if info_result.returncode == 0:
                        for line in info_result.stdout.split('\n'):
                            if 'Pages:' in line:
                                pages = line.split(':')[1].strip()
                                print(f"   Pages: {pages}")
                                break
                except FileNotFoundError:
                    print(f"   ℹ️  pdfinfo not available (install poppler-utils for detailed PDF info)")

                results.append({'file': test['name'], 'status': status, 'size_kb': size_kb})

            else:
                print(f"   ❌ PDF generation failed")
                results.append({'file': test['name'], 'status': 'FAIL', 'size_kb': 0})

        except subprocess.TimeoutExpired:
            print(f"   ❌ PDF generation timed out")
            results.append({'file': test['name'], 'status': 'TIMEOUT', 'size_kb': 0})
        except FileNotFoundError:
            print(f"   ❌ Chrome not found at expected path")
            print(f"   Try: /usr/bin/google-chrome or adjust path for your system")
            results.append({'file': test['name'], 'status': 'NO_CHROME', 'size_kb': 0})

        print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] in ['FAIL', 'TIMEOUT', 'NO_CHROME'])

    print(f"\n✅ Passed: {passed}/{len(results)}")

    if failed > 0:
        print(f"❌ Failed: {failed}/{len(results)}")
        for r in results:
            if r['status'] not in ['PASS', 'WARN_SIZE']:
                print(f"   - {r['file']}: {r['status']}")

    # Log to automation log
    summary = f"print_validation completed: {passed}/{len(results)} passed"
    append_log(summary)
    print(f"\n📝 Logged to: {log_path}")
    print()

    # Manual verification checklist
    print("=" * 70)
    print("MANUAL VERIFICATION CHECKLIST (Open PDFs in test_output/)")
    print("=" * 70)
    print("[ ] Valuation chart visible and legible")
    print("[ ] NCO chart visible and legible")
    print("[ ] Tables don't split awkwardly across pages")
    print("[ ] Module cards render correctly")
    print("[ ] Focus states NOT visible (print CSS working)")
    print("[ ] Colors preserved for key elements (Cathay Red/Gold)")
    print()

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(validate_print_output())
