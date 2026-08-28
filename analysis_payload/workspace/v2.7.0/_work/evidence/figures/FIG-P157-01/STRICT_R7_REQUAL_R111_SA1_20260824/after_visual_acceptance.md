# FIG-P157-01 R111 independent SA1 visual acceptance

`RESULT: FAIL`

Required views were actually opened by this SA1 and logged in `R111_REQUIRED_VIEW_REVIEW_LEDGER.csv`. All 80 glyph original/target-overlay/mask 1× views and all 10 contact sheets containing the 8× cells were personally opened; the 9 relation packages were likewise opened at 1× and 8× in `R111_GLYPH_MANUAL_LEDGER.csv` and `R111_RELATION_MANUAL_LEDGER.csv`.

| Required gate | Result | Evidence and determination |
| --- | --- | --- |
| `SOURCE_FONT_PASS` | `true` | All reader-visible elements have effective font size at least 9.5 pt; smallest is 9.8192 pt region label. `after_font_audit.csv`, corrected source map. |
| `PIXEL_HEIGHT_PASS` | `false` | Valid same-codepoint calibration finds G0005, G0014, G0050, G0068, and G0080 outside both H-ink and ink-area ratio `[0.92,1.08]`. `R111_LOW_PROFILE_CALIBRATION_VALIDATION.csv`, `R111_PIXEL_FINAL_ADJUDICATION.csv`. |
| `SAME_CLASS_RATIO_PASS` | `true` | Native 1× raw-mask D audit: 80/80 rows within `[0.92,1.08]`; singleton/script exclusions are explicitly closed, not pending. `R111_D_E_FINAL_ADJUDICATION.csv`. |
| `ROLE_RATIO_PASS` | `false` | BODY region-label CJK median `35 px` / ordinary annotation CJK base `37 px` = `0.9459`, below strict `[0.95,1.10]`; eight affected glyph rows. `R111_D_E_ROLE_SUMMARY.csv`. |
| `OVERLAP_PIXEL_COUNT` | `139` | Canonical independent curves `O-G001`/`O-G002` intersect in 139 px; all text-related illegal overlaps are 0. `r111_curve_raw_recheck_v2/R111_CURVE_RAW_RECHECK.json`. |
| `CLIP_PIXEL_COUNT` | `0` | 20/20 objects pass crop/page-edge final adjudication. `R111_CLIP_FINAL_ADJUDICATION.csv`. |
| `MIN_TEXT_CLEARANCE_PX` | `16` | Minimum text-to-graphic relation clearance; crop-edge text minimum is 29 px. All required text relations pass. |
| `VISUAL_HARMONY_PASS` | `true` | Human panel/role/script review finds no oversized, undersized, weight, colour, density, grayscale, or page-fusion visual defect. Numeric D/E and pixel failures are retained separately and are not visually waived. `R111_FONT_VISUAL_HARMONY_LEDGER.csv`. |
| `MATH_SEMANTICS_PASS` | `false` | Source curves do not mathematically cross, but their visible envelopes merge, defeating their independent-curve teaching role. `R111_MATH_SEMANTICS_AUDIT.md`. |
| `TEXT_CONSISTENCY_PASS` | `true` | Source, labels, marker, and caption agree on monotone training error and U-shaped validation error. |
| `GRAYSCALE_PASS` | `true` | Direct grayscale review preserves solid/dashed/marker/reference distinctions and text hierarchy. |
| `PAGE_INTEGRATION_PASS` | `true` | Full-page review shows balanced width, caption placement, and adjacent-prose integration. |

The visual/harmony observation is not a substitute for hard metrics. The final result is FAIL because the calibrated pixel gate, strict role-ratio gate, independent-curve overlap/clearance gate, and mathematical representation-semantics gate are false.

Legacy finding note: no final conclusion relies on the unverified 516 px claim or the 37 px peer-removal result. Both are retracted; 139 px / clearance 0 from independent raw masks is the only R111 curve result.
