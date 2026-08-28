# FIG-P504-01 ROOT VALIDATION R1

## Root verdict

- `RESULT: FAIL`
- `NEXT_ROLE: SA2`
- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 550, printed page 537, figure 28.1.
- Root independently reopened the native color/grayscale crop, text overlay, limiting-pair ROIs, source, and adjacent mathematical text.

## Confirmed hard failures

1. Source-size gate fails for 11/14 visible semantic objects: general labels/formulas are 9.4 pt and note/summary text is 9.2 pt, below the 9.5 pt floor.
2. Thirteen individually measured glyphs fail their native 300 dpi class thresholds. These include base `=` and punctuation measured with their own bboxes/raw masks; no parent formula height was substituted.
3. Formula-role/base-lowercase pixel ratio is `1.325`, above the `[1.00,1.18]` formula interval.
4. `R_TITLE` and `R_W2` have zero raw-ink intersection and 14 px raw-ink separation, so the earlier 378-pixel claim was a mask-ownership false positive and is rejected. Their independent PDF/vector text bboxes nevertheless have 0 px clearance, below the required 4 px; the native ROI visibly confirms the cramped title/`w_2` placement.
5. The LSA panel is mathematically inconsistent. In the displayed two-dimensional plane, the two shown orthogonal basis directions `u_1,u_2` with `K=2` span the whole plane, hence `U_2U_2^T x=x`; the separate projected point and nonzero residual instead depict a rank-one projection. The NMF rank-two cone panel is otherwise coherent.

## Passing/nonblocking findings

- Corrected illegal raw-overlap count is 0; clip count is 0.
- Same-class ratios, grayscale redundancy, text consistency, reading order, and page integration pass.
- `FONT_VISUAL_HARMONY_PASS=false`: the absolute-size, role-ratio, clearance, and semantic failures prevent accepting the current hierarchy or any further shrinking.

The current candidate must not proceed to SA3. SA2 must choose one semantically valid LSA geometry (a true ambient-3D vector projected onto a `K=2` plane, or a two-dimensional `K=1` projection), repair source sizes/role harmony and the title-to-`w_2` bbox clearance, then produce a new frozen candidate for fresh independent SA1.
