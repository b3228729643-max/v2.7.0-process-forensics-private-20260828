# Superseded artifacts retained for traceability

`roi_packages/` is a superseded preliminary ROI set. It was produced before geometric isolation of graphic masks and may contain text-coloured pixels in broad graphic regions. It is retained rather than deleted so the audit trail is non-destructive, but it is not active evidence and must not be used for any verdict.

The active pair evidence path is `roi_packages_r2_geometry_isolated/`, which is the path referenced by `after_overlap_report.csv`. The terminal validator explicitly distinguishes this declared superseded folder from active evidence; it does not conceal its presence, and it does not treat its files as a substitute for the active package.

## Superseded initial glyph diagnostics

`glyph_reviewer_ledger.csv` and `glyph_machine_integrity.csv` are **SUPERSEDED_INITIAL_RAW** forensic records. They describe the unseparated initial mask extraction, including the nine component-assignment candidates and the P0717 shared pixels. They remain ordinary parseable CSV files for traceability only and must not contribute a final contamination, final reviewer, or evidence-integrity count.

The active final records are `glyph_final_reviewer_ledger.csv` (139/139 manually completed cells pointing to `glyph_final_*` and all 12 final contact sheets), `glyph_final_mask_integrity.csv`, and `glyph_isolation_ledger.csv`. G0114, G0124, G0029, and G0036 are judged from those final records; no initial raw FAIL is silently relabeled as a final PASS.
