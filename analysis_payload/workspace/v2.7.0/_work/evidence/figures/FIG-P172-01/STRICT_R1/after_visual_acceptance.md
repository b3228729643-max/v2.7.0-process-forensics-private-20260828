# FIG-P172-01 — strict R1 visual acceptance

Official object: `strict_current_r90_fullbook/main_full.pdf`, physical page 187,
Figure 11.1.  The original-page raster is `official_page_p187_300dpi-187.png`
(2481 × 3508, produced directly at 300 dpi; no resize or resampling).

## Required decision matrix

| Gate | Result | Evidence / measured result |
|---|---:|---|
| SOURCE_FONT_PASS | false | `P172-CONDITION` and the four legend labels resolve to 9.20pt, below 9.50pt. |
| PIXEL_HEIGHT_PASS | false | All four visible `\cdots` sequence markers have `H_ink=4px`, below the 22px base-math-symbol floor. |
| SAME_CLASS_RATIO_PASS | false | Natural script `t` is 23px while `t+1`/`T` is 26px: 23/26 = 0.885, below 0.92, in both panels and both Y/X rows. |
| ROLE_RATIO_PASS | true | The named HMM/CRF panel titles are titles, not `(a)/(b)` serial panel labels; their 0.90–1.25 emphasis ratios pass. Annotation/legend role ratios also pass. |
| OVERLAP_PIXEL_COUNT | 0 | No thresholded illegal foreground intersection in the text-text, text-border/path, marker, legend, caption, or cross-panel checks. |
| CLIP_PIXEL_COUNT | 0 | No text, factor, arrowhead, brace, marker, legend, or caption ink is clipped on the native official page. |
| MIN_TEXT_CLEARANCE_PX | 2.000 | `P172-HMM-HX2` (X_t+1) to its node border; required node-text clearance is 5px. |
| VISUAL_HARMONY_PASS | false | The four `t+1` labels visibly crowd their circular node borders; 9.2pt legend/condition text and 4px ellipses weaken the intended hierarchy. |
| MATH_SEMANTICS_PASS | true | HMM uses directed state/emission arrows; CRF uses undirected transition/observation factors conditioned on x. |
| TEXT_CONSISTENCY_PASS | true | Caption, task cards, figure, and following reading sentence are consistent: capitals label graph variables, while x/y denote observed/candidate realizations. |
| GRAYSCALE_PASS | true | Directional arrows, circle/square shapes, observed-node hatch, and factor topology remain distinguishable without color. |
| PAGE_INTEGRATION_PASS | true | The figure, two-line caption, and following reading sentence remain visually integrated on the official page; no clipping or abnormal page break is present. |

## Four-view inspection

- Full-page fit: `full_page_p187_200dpi-187.png`
- Full-page 100% native reference: `official_page_p187_300dpi-187.png`
- Figure-only native crop: `figure_crop_300dpi.png` and `standalone_300dpi_from_official_page.png`
- Grayscale native view: `after_grayscale_300dpi.png`
- 1:1 critical ROIs: `roi_hmm_hy2_clearance_100pct.png`,
  `roi_hmm_hx2_clearance_100pct.png`, `roi_crf_yx2_clearance_100pct.png`,
  `roi_hmm_panel_100pct.png`, `roi_crf_panel_100pct.png`, and
  `roi_condition_legend_caption_100pct.png`.

## Strict outcome

**FAIL.**  All required evidence files are present, but the source-font,
pixel-height, same-class-ratio, node-clearance, and harmony gates are not all
true.  This is an SA1 failure, not an authorization to edit the figure.
