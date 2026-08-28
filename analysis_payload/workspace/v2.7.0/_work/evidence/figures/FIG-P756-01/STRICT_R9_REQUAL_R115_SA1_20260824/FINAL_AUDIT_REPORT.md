# FIG-P756-01 — Strict R115 SA1 Final Audit

| Dimension | Result |
|---|---|
| Evidence integrity | **PASS** |
| Figure hard gates | **FAIL_TO_SA2** |
| Official input | R95 `main_full.pdf`, physical p801 / printed p788, native 300 dpi |
| Pair universe | 1,485 all unordered; 1,107 mandatory; one failure (`P1408`) |
| Glyph universe | 378 glyphs; 48 native 1x + 95 8x contact sheets opened by SA1 |
| Calibration | 10 valid raw-CID groups / 20 valid targets; 0 invalid targets |

The evidence package is complete: official PDF identity, source locators, independent final-visible and pre-occlusion raw masks, drawing order, per-glyph ledger, all required relation views, clipping, D/E, and valid low-profile calibration are retained. `R115_MACHINE_FINAL_CHECK.json` passed its completeness and consistency checks.

The figure nevertheless fails requalification for two separately recorded reasons:

1. `P1408` (`O-G016` / `O-G017`) has 792 px raw independent final-visible intersection and zero clearance. The source defines the supervised and unsupervised routes independently at l57-60, so it cannot be treated as shared geometry.
2. `G0208`, `G0212`, and `G0222` are non-low-profile `口` glyphs with native H=29 px against the strict H>=30 px floor.

No source, build product, central state, inventory, or historical P756 evidence was read or altered for this review. The only writes are within this evidence directory. Final routing is **FAIL_TO_SA2**.
