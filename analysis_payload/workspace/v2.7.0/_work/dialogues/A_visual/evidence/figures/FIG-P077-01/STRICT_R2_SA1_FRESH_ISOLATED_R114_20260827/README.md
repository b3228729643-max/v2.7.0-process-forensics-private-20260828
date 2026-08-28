# FIG-P077-01 R114 fresh isolated SA1 evidence

Handoff: `A-R114-P077-SA1-FRESH-ISOLATED-20260827`

This root contains an independent read-only review of the current official R114 PDF and current P077 source. The reviewer located the caption on physical page 79 from the official PDF, froze 30 visible objects and all 435 unordered pairs, opened all required and critical views, and wrote the manual decision fields only after observation.

Evidence map:

- `machine/input_identity.json`: official input identities.
- `machine/page_locator.json`: independently found page/caption and direct-raster geometry.
- `machine/visible_object_geometry.csv`: 30-object denominator geometry without reviewer decisions.
- `machine/all_unordered_pairs_geometry.csv`: all 435 unordered pairs without reviewer decisions.
- `machine/pdf_text_spans_and_raster_ink.csv`: vector spans and direct native-300-dpi ink observations.
- `machine/foreground_pair_pixel_clearance.csv` and `mechanical_overlap_candidates.csv`: mechanical pixel observations only.
- `visual/`: full page, direct native crop, grayscale, overlays, native1x/nearest8x ROIs, and per-object semantic masks.
- `manual/visible_object_manual_ledger.md`: 30/30 post-observation object decisions.
- `manual/all_unordered_pairs_manual_ledger.md`: 435/435 post-observation pair decisions.
- `manual/opened_view_ledger.md`: 18/18 actually opened views.
- `manual/overlap_adjudication.md`: current-PDF collision/contamination and clearance adjudication.
- `manual/after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_model_route.md`, and `after_visual_acceptance.md`: manual SA1 acceptance fields.
- `audit/PRESEAL_MANUAL_VALIDATION.md`: final pre-seal completeness and identity check.

Fresh SA1 result: `PASS`; authorized next token: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.
