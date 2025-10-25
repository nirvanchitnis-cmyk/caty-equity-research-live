"""Summary Compensation Table & PVP extraction playbook."""

PLAYBOOK = [
    "Identify Summary Compensation Table and Pay Versus Performance headings.",
    "Parse tables, resolving merged headers and aligning executive rows.",
    "Normalize numeric currency columns, handling parentheses as negatives.",
    "Cross-check totals against reported summary lines and CAP/TSR ties.",
    "Attach provenance (table id, cell coordinates) and downgrade confidence on validation failures.",
]
