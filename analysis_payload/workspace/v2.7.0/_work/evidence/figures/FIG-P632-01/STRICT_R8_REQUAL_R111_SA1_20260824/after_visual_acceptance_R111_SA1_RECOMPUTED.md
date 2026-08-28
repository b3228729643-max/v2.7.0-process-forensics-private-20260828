# FIG-P632-01 R111 SA1 requalification acceptance record

Final result: FAIL_TO_SA2

This is a resumed, independent current-identity review. Existing evidence was preserved. The official input was main_full.pdf from the strict_current_r95_fullbook build. No source, build, inventory, or central-state file was written.

Evidence integrity: FAIL

- RESULT_CONSISTENCY_FAIL: R0046 legacy RESULT is FAIL although its raw foreground measures are overlap 0 and clearance 16px against 8px. Corrected semantic-parent foreground reconstruction is PASS at 20.518px.
- SEMANTIC_PARENT_MAPPING_FAIL: G204 through G209 are pi(a,t) glyphs assigned to P06 but source line 137 makes them part of P07.
- ROLE_RATIO_PENDING: the raw pixel-measurement rows retain ACTUAL_BASELINE_PENDING. The helper recomputation is supplemental and cannot repair that raw evidence defect.

Figure hard gates: FAIL

- 30 strict native-pixel glyph failures; effective-point font gate itself is 0 failures.
- D fails: 13; E cross-panel fails: 12.
- 36 physical raw-clearance failures. Every measured overlap is 0. A raw 1px clearance is a clearance failure, not a pixel-overlap failure.
- Edge, clipping, graphic-mask, paint-order, halo/final-visible, math semantics, and four-view checks pass.
- FONT_VISUAL_HARMONY fails only because its size subgate fails; weight and color each pass.

Current-identity viewing record: all 42 contact sheets and every cell were personally opened; all 37 legacy failing/critical relation packages were personally opened at original 1x, A, B, intersection, overlay 1x, and overlay 8x nearest; O01 through O03 pre, opaque, final, covered-xor, and 1x overlay views were personally opened.

The previous final_table_summary.json was not used as authority. The result above is recomputed from bottom-level evidence and the current identity ledger.
