# FIG-P632-01 independent SA3 audit

## Outcome

`SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

This is the independent second blind review for `FIG-P632-01`. No source or PDF was modified. No TeX engine or build command was run. All writes are confined to the isolated evidence root.

## Fixed identity

- OWNER_DIALOGUE: `C_visual`
- HANDOFF_ID: `C-FIG-P632-01-R110-SA3-FRESH-ISOLATED-V1`
- role: `SA3`
- canonical instance: `/root/sa3_fig_p632_r110_fresh_isolated_v1`
- model / effort: `gpt-5.6-sol` / `xhigh`
- fork_turns: `none`
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa3_r110_fresh_isolated_v1`

## Independent identity and location

The authorized PDF is 4,967,063 bytes with SHA256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`; `pdfinfo` reports 817 A4 pages. The authorized current single source is 9,022 bytes with SHA256 `1670F496E6CEBBF5636AC5BC97474A50FBA83811FFA2AAAAEF0CF8227BE8C8EB`.

Searching the live PDF text window for the current caption and figure number independently located the target at physical page 682, printed page 669, Fig. 33.2. The source label is `fig:V5-C04-conditional-slice`. The complete caption is:

> 同一二元正态联合密度的两条截面除以相应边缘密度后，得到方差16/25、全实线积分为1的满条件密度；零边缘处须使用预先指定的正则条件版本。

The surrounding current V5-C04 text gives the same model and reading sequence: first the horizontal and vertical joint-density slices; then division by the positive marginal densities; finally the two normalized full conditionals.

## Frozen denominators and opened evidence

- 14 complete semantic visible objects in the figure and caption.
- All 91 unordered pairs of those 14 objects.
- 151 machine-extracted visible text spans and 413 glyph records.
- 22 manual semantic text/glyph IDs covering every visible phrase and mathematical label.
- 6 critical ROIs; each was opened at native 1x and nearest-neighbour 8x.
- 7 manual view adjudications covering the full page, native figure crop, grayscale, object overlay, semantic overlay, text/glyph overlay, and all ROI views.
- 12 hard-gate adjudications.

The native full-page raster is 2481 by 3508 pixels at 300 dpi. The inspected figure-plus-caption crop is 1960 by 1530 pixels. All required images were opened before any manual adjudication file was written.

## Independent mathematics and probability recomputation

For covariance matrix

`Sigma = [[1, 3/5], [3/5, 1]]`,

the determinant is `1-(3/5)^2=16/25`. Therefore the bivariate-normal coefficient is `1/(2*pi*sqrt(16/25))=5/(8*pi)`, while the exponent is `-25 q/32` for `q=x1^2-(6/5)x1x2+x2^2`. These exactly match the figure.

Both conditional variances are `1-rho^2=16/25`, with standard deviation `4/5`. At `b=4/5`, the first conditional mean is `(3/5)(4/5)=12/25`. At `a=1`, the second conditional mean is `(3/5)(1)=3/5`. The two marginal denominators are standard-normal values: `phi(4/5)=0.2896915528...`, correctly rounded to `0.290`, and `phi(1)=0.2419707245...`, correctly rounded to `0.242`. The common peak is `1/(sqrt(2*pi)*(4/5))=5/(4*sqrt(2*pi))`. Both displayed conditional densities integrate to one.

The covariance eigenvalues are `1+rho` and `1-rho`; hence a Mahalanobis contour has semiaxes `c sqrt(1+rho)` and `c sqrt(1-rho)`. Positive correlation gives the shown +45 degree major axis. The zero-marginal caveat is also correct: a regular conditional version must be fixed for null conditioning values and is unique only marginal-almost-everywhere; in this Gaussian example both denominators are positive.

## Geometry, relationships, overlap, clipping and integration

The left panel has centered nested contours with the correct +45 degree orientation. The horizontal and vertical slices cross exactly at the marked `(a,b)` point. Their different color and dash encodings remain distinguishable in grayscale. The green horizontal normalization route points only to the upper conditional plot; the blue vertical route points only to the lower plot. The two routes do not cross. Both arrowheads stop before the destination y-axes.

All 91 unordered semantic-object pairs were reviewed individually. The only visible foreground contacts are intended mathematical contacts: slices crossing axes and contours, both slices meeting at the conditioned point, the point lying on the slices, and each slice continuing into its own routed arrow. None is an illegal overlap. No text is crossed or obscured. No curve, arrow, formula, note, caption or page element is clipped.

The tightest reviewed non-contact stack is the lower `3/5` mean label above the red note box; its text ink ends at y=1407 px while the note border begins at approximately y=1440 px, giving at least 33 px. The note border ends before the caption ink with at least 23 px. These are conservative native-300-dpi clearances.

The caption describes exactly what the figure shows and sits cleanly above the following body text. The full page is balanced: the left joint panel and two right conditional panels have a stable hierarchy without excessive whitespace or crowding.

## Text, font and glyph review under R168

The source sets figure nodes at 9.6 pt. PDF extraction finds 112 spans at 9.564 pt and 8 caption spans at 9.963 pt. Thirty-one extracted spans are 6.695 pt because they are natural TeX mathematical scripts such as fraction digits, subscripts, superscripts, the integral limit and the degree symbol; they are not independent base-size labels. Native 1x and nearest-neighbour 8x review shows these scripts remain sharp and readable.

Across all 413 glyph records there is no missing glyph, tofu, wrong codepoint, broken delimiter, fused operator or unreadable character. R168 was applied: harmless pixel-edge and font-outline variations were treated as advisory. None of the permitted hard-fail conditions is present.

## Gate metrics

- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `true`
- OVERLAP_CANDIDATE_PIXEL_COUNT: `0` for illegal-overlap candidates after semantic pair review
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT: `0` true illegal overlap pixels
- PIXEL_ADJUDICATION_STATUS: `NO_ILLEGAL_CANDIDATE`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `23`
- VISUAL_HARMONY_PASS: `true`

Intended mathematical intersections are separately recorded in the pair ledger and are not illegal-overlap candidates.

## Decision and next action

No unresolved item remains in this SA3 scope. The truthful independent outcome is `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`. Main C should read this sealed evidence root and perform its own local-pass acceptance. This SA3 must not update central state or start another UID.
