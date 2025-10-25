# Confidence Model

Final confidence scores per fact are computed as the product of weighted components:

```
confidence = source_weight
           * parser_quality
           * header_match
           * validation_multiplier
           * provenance_multiplier
           + corroboration_bonus
```

Where:

- `source_weight`: HTML=1.00, native PDF=0.90, OCR=0.75.
- `parser_quality`: normalized text/table parsing quality (0.7–1.0).
- `header_match`: exact anchor=1.0, synonym=0.8, rerank=0.6.
- `validation_multiplier`: 1.1 all checks pass, 0.85 warnings, 0.6 adjustments.
- `provenance_multiplier`: 1.0 when selector + page + hash present; 0.8 selector missing; 0.6 page inferred.
- `corroboration_bonus`: up to +0.05 when multiple artifacts agree; −0.10 when conflicts appear.

Values are clamped to [0, 1] prior to emission.
