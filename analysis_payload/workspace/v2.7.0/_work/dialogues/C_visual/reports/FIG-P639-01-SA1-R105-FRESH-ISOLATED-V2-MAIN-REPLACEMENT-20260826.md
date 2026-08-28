# FIG-P639-01 — R105 fresh isolated SA1 report

## Verdict

`FAIL_TO_SA2`

- HANDOFF_ID: `MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- official candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf`
- physical page: `689` (1-based), printed page `676`, Figure `33.6`
- candidate identity: `817 pages / 4,967,209 bytes / SHA-256 F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`
- current source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bivariate_normal_conditionals.tex`
- source SHA-256: `C9F941F4E190A9233602BB12C739874290D100F1700E16F0D9FAA2FAD6F52149`
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826`

## Freshness and isolation

The evidence, report, and handoff target paths were verified absent before this run. No old P639 evidence/report/handoff/state/inventory, no P640 material, and no Git history were read. The permanently interrupted `sa1_r105_fresh_isolated_v1` directory was neither read nor written. The PDF and TeX source remained read-only; no TeX/latexmk, source edit, commit, central state, or inventory write occurred.

## Candidate and views

- Page size: `595.276 × 841.890 pt`; native full-page 300 dpi grid: `2481 × 3508 px`.
- `full_page_200dpi.png`: page-fusion view, actually opened.
- `full_page_300dpi.png`: native inspection view, actually opened.
- `figure_crop_300dpi.png`: integer crop `[250,1354,1938,854]`, actually opened.
- `standalone_300dpi.png`: integer crop `[375,1354,1708,708]`, actually opened.
- `grayscale_300dpi.png`: same figure crop, actually opened.
- `after_text_measurement_overlay_300dpi.png`: all included objects labeled, actually opened.

## Complete denominator and all-pair account

- Visible glyphs: `147`; all have nonempty native raw masks.
- Visible graphics: `10` (`D_X_TICKS`, `D_Y_TICKS`, two arrow/axis objects, two density curves, two mean lines, and the note border). The underlying dark x-axis path was fully occluded by the final-visible blue baseline and excluded from the final-visible denominator, with the pre-occlusion object retained in machine evidence.
- Total final-visible objects: `157`.
- Expected unordered pairs: `157 × 156 / 2 = 12,246`; actual rows: `12,246`.
- Empty-mask count: `0`; independent illegal-overlap pair count: `0`; clip-failure count: `0`.
- Math-rule reconciliation: `0` separate GRAPHIC/MATH_RULE objects; all visible mathematical marks are font glyphs, and all drawing/path objects in the figure were reconciled.
- Manual glyph review: `147/147` rows after actually opening all 13 contact sheets; original match, overlay completeness and mask-only purity all pass; missing-stroke and foreign-pixel counts are zero.

## Sole hard failure

`R00008` relates `G001` (U+2212 minus in the x-axis tick `−2`) to `G009` (the independent y-axis tick `0`). The native final-visible raw masks do not overlap (`INTERSECTION_PX=0`) and have `28.0689 px` raw-mask clearance, but their PDF/vector bboxes have `0.0 px` clearance. The strict TEXT-TEXT geometry minimum is `4 px`, so this relation fails.

The corresponding `R00008_native1x_8x.png` was actually opened before the manual decision was recorded. This is a geometry failure, not a typography-pixel failure.

## R168 evaluation

- Missing/tofu/wrong glyph/codepoint: PASS.
- Mathematical semantics and caption/text consistency: PASS. For `rho=0.6`, `a=1`, `b=0.75`, the plotted full-conditionals have variance `1-rho^2=0.64` and means `rho b=0.45`, `rho a=0.60`, matching labels and caption.
- Unreadable/gross visible imbalance: PASS.
- Crop: PASS.
- Illegal overlap: PASS (`0` independent overlap pixels).
- Grayscale: PASS; solid and dashed curves remain distinguishable.
- Page fusion: PASS; the lead-in, Figure 33.6, caption and following Figure 33.7 lead-in read naturally.
- Font visual harmony: PASS under R168. Source labels/notes are 9.2pt and ticks are 8.5pt; these are advisory deviations from the legacy 9.5pt target, remain readable/balanced, and are not promoted to hard defects.

## Minimal SA2 repair recommendation

Separate the y=0 tick label and the x-axis `−2` tick label until their final PDF/vector bboxes have at least `4 native px` clearance. Preserve the current curves, mean markers, annotation, caption semantics, page placement and R168 visual balance. After a new official build, regenerate all evidence from the new candidate and rerun fresh SA1.

## Evidence cross-check

- `machine/machine_summary.json`: denominator/pair/gate summary.
- `machine/object_manifest.json`: object identities, bbox and mask paths.
- `machine/after_pixel_measurements.csv`: `157` object rows.
- `machine/after_overlap_report.csv`: `12,246` unordered-pair rows.
- `manual/glyph_review_ledger.csv`: `147` manual glyph rows.
- `manual/critical_relation_review.csv`: sole hard-failure review.
- `manual/view_review_ledger.csv`: all opened-view records.
- `after_visual_acceptance.md`: final manual matrix and verdict.

Final result: `FAIL_TO_SA2`.
