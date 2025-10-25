"""Beneficial ownership extraction playbook."""

PLAYBOOK = [
    "Anchor to Beneficial Ownership (Item 403) headings.",
    "Extract tables, stitching multi-page layouts when headers repeat.",
    "Cleanse superscripts and footnote markers, retaining references.",
    "Normalize names, shares, percentages, and addresses to canonical schema.",
    "Run sanity checks on percentages (≤100) and share totals, flag outliers.",
]
