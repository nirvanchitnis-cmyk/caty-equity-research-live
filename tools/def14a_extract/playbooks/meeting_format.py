"""Virtual vs physical meeting detection playbook."""

PLAYBOOK = [
    "Search notice sections for keywords 'VirtualOnly', 'VirtualShareholderMeeting.com', 'in person', 'hybrid'.",
    "If URL present and address absent → classify virtual; address present without URL → physical; both present → hybrid.",
    "Normalize addresses via USPS format heuristics and attach to fact payload.",
    "Flag inconsistencies (e.g., virtual keywords with street address) for manual review.",
]
