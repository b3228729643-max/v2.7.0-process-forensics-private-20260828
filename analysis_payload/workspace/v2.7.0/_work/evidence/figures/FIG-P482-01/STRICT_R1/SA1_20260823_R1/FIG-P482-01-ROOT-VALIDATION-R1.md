# FIG-P482-01 ROOT VALIDATION R1

## Root verdict

- `RESULT: FAIL`
- `NEXT_ROLE: SA2`
- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 526, printed page 513, figure 27.1.
- Root independently reopened the native 300 dpi figure crop, grayscale view, raw illegal-overlap mask, and all four limiting pair ROIs. No rendered image was resized.

## Confirmed hard failures

1. Source-size gate fails for 7/10 semantic text objects. Effective sizes are 9.0 pt or 9.4 pt, below the 9.5 pt floor. The annotation role also mixes 9.0 pt and 9.4 pt (`max/min=1.0444`, `delta=0.40 pt`), failing both same-role source limits.
2. Four independent text--graphic pairs have genuine raw foreground collisions at native 300 dpi:
   - `T02_AXIS1` / `G04_OUTER_ELLIPSE`: 164 px;
   - `T05_1SIGMA` / `M17_SAMPLE`: 162 px;
   - `T07_PROJECTION` / `G03_INNER_ELLIPSE`: 80 px;
   - `T07_PROJECTION` / `M20_SAMPLE`: 29 px.
   Their sum is 435 px, minimum clearance is 0 px, and the collisions are visible in the separated pair ROIs. These are not dilation, paint-order, or geometry-contact false positives.
3. Role hierarchy fails: formula annotation / annotation base is `0.7647` and axis-title formula / annotation base is `0.8824`, both below the required `[1.00,1.18]` interval.
4. Clip count is 0. Literal glyph-height thresholds themselves are all met (`0/47` height-only failures); the 12 composite pixel rows fail because the four parent objects collide. This distinction does not change the overall FAIL.

## Nonblocking findings

- Covariance-ellipse geometry, principal-axis ordering, orthogonal projection semantics, variable naming, grayscale redundancy, and page integration are consistent with the adjacent text.
- The subagent's initial prose sentence claiming zero text--graphic overlap contradicted its CSV and summary. It reran/corrected the evidence; the formal report, visual report, summary, pair CSV, and root inspection now agree on four pairs and 435 px.

The current candidate must not proceed to SA3. SA2 must repair source size/harmony and move or re-anchor labels so every independent text--graphic pair has zero foreground overlap and at least 3 px clearance, followed by a newly frozen candidate and fresh independent SA1.
