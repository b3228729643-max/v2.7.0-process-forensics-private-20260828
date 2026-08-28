# FIG-P632-01 R111 independent SA1 requalification report

## Scope and stop condition

Reviewer: R111_SA1_REQUAL_CURRENT_IDENTITY_20260824
Review timestamp: 2026-08-24T10:56:40+08:00
Official frozen input: D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r95_fullbook/main_full.pdf
The evidence directory was resumed without deletion or rebuilding of prior artifacts. No source, build, central status, or inventory file was changed.

## Current-identity actual viewing

- CS001 through CS042 were personally opened. Every one of the 413 contact-sheet cells was checked in its embedded original, target-overlay, mask, and 8x nearest triad presentation.
- R0018, R0046, R0096, R0097, R0098, R0099, R0100, R0101, R0102, R0103, R0122, R0125, R0156, R0172, R0188, R0189, R0212, R0213, R0216, R0248, R0249, R0250, R0272, R0273, R0276, R0287, R0288, R0290, R0291, R0292, R0305, R0306, R0314, R0315, R0334, R0363, and R0390 were personally opened in original 1x, A mask, B mask, intersection, overlay 1x, and overlay 8x nearest.
- O01 through O03 were personally opened in pre-occlusion, opaque ground, final-visible, covered-xor, and 1x overlay views.
- Full page, figure crop, standalone, and grayscale views were personally opened.

## Recomputed finding

EVIDENCE_INTEGRITY: FAIL

- RESULT_CONSISTENCY_FAIL. R0046 raw row reports overlap 0 and min clearance 16px with threshold 8px, but reports RESULT FAIL because an extra composite bbox gate is 0. This conflicts with foreground measurement. Corrected semantic-parent reconstruction gives 20.518px and PASS. R0046 is excluded from physical clearance-failure count.
- SEMANTIC_PARENT_MAPPING_FAIL. G204-G209 pi(a,t) are incorrectly attached to P06 rather than P07. This explains the composite-parent condition behind R0046.
- ROLE_RATIO_PENDING. Every raw after_pixel_measurements row retains ACTUAL_BASELINE_PENDING. A separately documented helper recomputation cannot close the required raw trace.

FIGURE_HARD_GATES: FAIL

- Strict native pixel glyph gate: 30 failures of 413. Font effective-point gate: 0 failures.
- D intra-panel: 13 failures. E cross-panel: 12 failures.
- Relation physical clearance: 36 failures; all overlap measurements are 0. R0188 and analogous cases are recorded as overlap 0 with raw clearance 1px less than 3px, never as overlap.
- Font visual harmony: SIZE FAIL, WEIGHT PASS, COLOR PASS, aggregate FAIL.
- Passes: 27 graphic masks, 12 edge relations and clipping, O01-O03 paint/halo/final-visible, math semantics, and four views.

## Terminal disposition

FINAL: FAIL_TO_SA2

No conclusion above relies on the previous final_table_summary.json. The attached recomputation and current-identity ledgers are authoritative for this requalification.
