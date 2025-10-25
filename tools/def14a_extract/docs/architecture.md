# DEF 14A Extraction Architecture

This document tracks the top-level components built in `tools/def14a_extract`:

- **Fetchers** discover and download filings with SEC-compliant throttling.
- **Normalizers** convert raw artifacts to structured text across HTML, native PDF, and OCR modalities.
- **Section/location** modules map canonical sections to page offsets for downstream extractors.
- **Table extraction** orchestrates multi-backend parsing with provenance snapshots.
- **Fact extractors** apply registry-driven heuristics for meeting metadata, ownership, compensation, and audit data.
- **Validation and provenance** layer deterministic cross-checks and confidence scoring.
- **CLI/API** expose `def14a facts` and programmatic `get_def14a_facts` surfaces for downstream automations.
