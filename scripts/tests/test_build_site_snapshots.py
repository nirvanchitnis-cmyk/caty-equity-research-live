import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

import unittest

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "index.html"
BUILD_SCRIPT = ROOT / "scripts" / "build_site.py"
SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"

MARKERS = [
    "reconciliation-dashboard",
    "module-grid",
    "evidence-provenance",
    "exec-company-snapshot",
    "exec-valuation-metrics",
    "exec-performance-metrics",
    "exec-credit-metrics",
    "price-target-grid",
]

PATTERN_CACHE: Dict[str, re.Pattern[str]] = {}


def normalize_fragment(fragment: str) -> str:
    lines = fragment.strip("\n").splitlines()
    trimmed = [line.rstrip() for line in lines]
    indents = [len(line) - len(line.lstrip()) for line in trimmed if line.strip()]
    if indents:
        trim = min(indents)
        trimmed = [line[trim:] if len(line) >= trim else line for line in trimmed]
    return "\n".join(trimmed).strip()


def extract_marker(html: str, marker: str) -> str:
    if marker not in PATTERN_CACHE:
        PATTERN_CACHE[marker] = re.compile(
            rf"<!-- BEGIN AUTOGEN: {re.escape(marker)} -->(?P<content>.*?)<!-- END AUTOGEN: {re.escape(marker)} -->",
            re.DOTALL,
        )
    match = PATTERN_CACHE[marker].search(html)
    if not match:
        raise AssertionError(f"Marker '{marker}' not found in index.html")
    return normalize_fragment(match.group("content"))


class BuildSiteSnapshotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILD_SCRIPT), "--test-mode"], check=True, cwd=ROOT)
        cls.html = INDEX_PATH.read_text(encoding="utf-8")

    def test_snapshots(self) -> None:
        for marker in MARKERS:
            with self.subTest(marker=marker):
                actual = extract_marker(self.html, marker)
                snapshot_path = SNAPSHOT_DIR / f"{marker}.html"
                if not snapshot_path.exists():
                    self.fail(f"Snapshot missing for marker '{marker}' ({snapshot_path})")
                expected = snapshot_path.read_text(encoding="utf-8").strip()
                if actual != expected:
                    import difflib

                    diff = "\n".join(
                        difflib.unified_diff(
                            expected.splitlines(),
                            actual.splitlines(),
                            fromfile="expected",
                            tofile="actual",
                            lineterm="",
                        )
                    )
                    self.fail(f"Snapshot mismatch for '{marker}'. Diff:\n{diff}")


if __name__ == "__main__":
    unittest.main()
