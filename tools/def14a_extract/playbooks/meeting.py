"""Meeting metadata extraction playbook."""

PLAYBOOK = [
    "Locate Notice of Annual Meeting heading and capture surrounding prose.",
    "Extract meeting date, time, and timezone using deterministic regex patterns.",
    "Identify record date sentences and validate sequence vs meeting date.",
    "Detect virtual vs physical language and capture access URLs or addresses.",
    "Persist provenance with source paragraph references and validation warnings for anomalies.",
]
