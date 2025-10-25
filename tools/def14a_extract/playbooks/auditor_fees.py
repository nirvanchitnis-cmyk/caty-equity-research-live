"""Procedural playbook for auditor fee extraction."""

PLAYBOOK = [
    "Locate Audit Fees section heading using canonical anchors.",
    "Collect candidate tables adjacent to heading, prioritizing HTML tables.",
    "Normalize headers via synonym mapping and ensure fiscal year columns present.",
    "Validate sums across fee categories and fiscal years.",
    "Emit structured facts for audit, audit-related, tax, and other fees with provenance.",
]
