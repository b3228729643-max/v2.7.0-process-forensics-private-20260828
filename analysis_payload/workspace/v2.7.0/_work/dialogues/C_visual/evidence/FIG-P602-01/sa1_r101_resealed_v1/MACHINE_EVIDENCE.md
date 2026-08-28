# FIG-P602-01 R101 machine evidence

This package contains measurements only.  It deliberately contains no manual PASS decision.

## Frozen identity

- scope row: `B52`
- branch denominator: `46`
- semantic object denominator: `26` (`T01--T14`, `B01--B06`, `E01--E06`)
- unordered pair denominator: `325 = C(26,2)`
- R101 PDF page: `651`; printed book page: `638`
- identity and SHA values: `00_identity/identity.json`
- write stop seal: `00_identity/WRITE_STOPPED.json`

## Machine outputs

- `03_objects/object_manifest_26.csv`: 26 semantic masks and native 1x/8x paths.
- `after_pixel_measurements.csv`: 175 native-300-dpi glyph measurements. Fixed-threshold machine gates are measurements, not manual verdicts.
- `04_glyphs/low_profile_peer_measurements.csv`: 27 low-profile peer rows, all `UNADJUDICATED`.
- `05_pairs/object_pair_ledger.csv`: all 325 unordered pairs. `MANUAL_DECISION` is `UNADJUDICATED` for every row.
- `05_pairs/intersection_register.csv`: eight raw-intersection pairs; every row remains manually unadjudicated.
- `05_pairs/critical/*_1x.png` and `*_8x.png`: native evidence cards for those eight intersections.
- `08_reports/glyph_role_ratio_audit.csv`: 50 role/script measurements, all manually unadjudicated.
- `08_reports/clipping_audit.csv`: 26 page/crop edge measurements, all manually unadjudicated.
- `after_font_audit.csv`: source declaration measurements, all manually unadjudicated.
- `after_text_measurement_overlay_300dpi.png`, `07_views/grayscale_300dpi.png`, and `02_renders/figure32_5_evidence_crop_300dpi.png`: views for independent review.

The generator reports 26 objects, 325 pairs, eight raw-intersection pairs, zero machine-classified illegal-overlap pairs, 175 glyphs, zero fixed-threshold/isolation machine misses, and 27 low-profile rows awaiting human review.  These facts must not be promoted to a strict result until a completely fresh read-only SA1 has adjudicated every required ID.
