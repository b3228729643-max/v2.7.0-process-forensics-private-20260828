RESULT: LOCAL_CANDIDATE_PASS

# FIG-P157-01 — SA2 STRICT-R2 four-view visual acceptance

Scope is the independently compiled local candidate only. Root must still build a new continuous official PDF and obtain fresh independent SA1 and isolated SA3 reviews; this file does not sign final project PASS.

## §9.2.1 hard matrix

- SOURCE_FONT_PASS = true
- PIXEL_HEIGHT_PASS = true
- SAME_CLASS_RATIO_PASS = true
- ROLE_RATIO_PASS = true
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 9.76
- MIN_TEXT_TEXT_CLEARANCE_PX = 9.76
- MIN_TEXT_GRAPHIC_CLEARANCE_PX = 14.04
- T02_VALIDATION_CURVE_CLEARANCE_PX = 164.12
- TEXT_TO_PAGE_EDGE_CLEARANCE_PX = 334.11
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

## Native evidence and complete-object coverage

- `standalone_page_300dpi.png` and `local_page_300dpi.png` are direct Poppler renders at 300 dpi, each 2481×3508 px. No render was resized. `standalone_300dpi.png`, `figure_crop_300dpi.png`, and all ROIs are lossless native-pixel crops only.
- `element_inventory.csv` covers all 12 reader-visible figure text elements and all 7 foreground graphic objects: two data curves, the selection reference line, the minimum marker, the training-label leader, and both axes with arrowheads. It expressly records the absent node-border, panel-border, and legend classes.
- `after_overlap_report.csv` contains all 66 TEXT–TEXT pairs, all 84 TEXT–graphic pairs, and the page-edge clip row: 151/151 PASS, overlap sum 0, clip count 0. The tightest TEXT–TEXT bbox gap is 9.76 px; the tightest ink-to-line/marker gap is 14.04 px (T03–G04), both above their 4 px and 3 px thresholds.
- The repaired T02 `验证误差：先降后升` versus G02 dashed validation curve pair has overlap 0 and 164.12 px native-ink clearance. The unresampled 1:1 proof is `roi_05_validation_label_curve_clearance_100pct.png`.

## Font, pixel height, and hierarchy

- `after_font_audit.csv`: 12/12 PASS. Effective sizes range from 9.856 pt to 11.200 pt; same-role source sizes have ratio 1.000 and difference 0.000 pt. The figure is single-panel.
- `after_pixel_measurements.csv`: 12/12 PASS. CJK minimum-glyph ink heights are 35–43 px and the caption digit element is 27 px, above the applicable 30 px and 24 px floors. Same-role/same-script ratios range from 0.973 to 1.027.
- With curve labels as BASE (median 37 px), key annotations have role ratio 1.014, region annotations 1.000, and axis titles 1.135. These satisfy the required annotation and axis-title bands. No ordinary text becomes the first visual focus.

## Four required views

| View | Evidence | Finding |
|---|---|---|
| Local full page / fit | `full_page_200dpi.png` | Figure, caption, and revised reading sentence fit without collision, clipping, orphan text, or abnormal local compression. |
| Local full page / native | `local_page_300dpi.png` | Direct 300 dpi page candidate; figure number/reference are both 10.1 and the revised sentence is visible in context. |
| Figure / native | `figure_crop_300dpi.png`, `standalone_300dpi.png`, `roi_01`–`roi_05` | T02 now occupies genuine upper-middle blank space and does not cover either curve, the minimum marker, reference line, axis, leader, or another label. |
| Grayscale / native | `figure_grayscale_300dpi.png` | Solid training and dashed validation curves remain distinct; the filled minimum point and vertical dashed reference line remain identifiable; label placement remains clear. |

## Semantic and text checks

- Curves and teaching data are unchanged: training error is `0.36+3.35 exp(-0.34x)` and strictly decreases; validation error is `1.08+0.105(x-5.25)^2` and has its unique minimum at `(5.25,1.08)`. The gold filled point and vertical reference line still use that coordinate, and the underfit/suitable/overfit regions are unchanged.
- The local page text extraction contains `实线表示训练误差`, `虚线表示验证误差`, and the normalized phrase `金色实心点和竖向参考线共同标出按预先约定规则选中的复杂度`. It contains neither `实线圆点` nor `虚线三角`.
- Caption, axis labels, region labels, formulas, line types, selected point, and adjacent prose now agree. No color-only distinction is required for the two error series.

## Build acceptance

- `build/standalone_wrapper.pdf` and `build/page_wrapper.pdf` each compile successfully with LuaLaTeX; the page wrapper was rerun to stabilize `\cref`.
- Final `standalone_wrapper.log` and `page_wrapper.log` have 0 combined matches for LaTeX/Package error, undefined control sequence, fatal/emergency stop, overfull/underfull box, undefined/multiply-defined reference, and font-warning hard patterns.
- Root still must verify the newly rebuilt continuous official page because SA2 is not authorized to publish or issue final PASS.
