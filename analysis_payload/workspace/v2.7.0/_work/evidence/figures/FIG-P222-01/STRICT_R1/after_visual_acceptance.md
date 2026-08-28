# FIG-P222-01 — SA1 STRICT R1 visual acceptance

## Verdict

`RESULT: FAIL` — a strict gate is failed whenever any required item is false. No SA3 was started.

## Candidate, location, and render provenance

| Item | Recorded value |
|---|---|
| Candidate PDF | `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r91_fullbook/main_full.pdf` (813 physical pages) |
| Figure source | `src/绘图源码/第02册_基础监督学习方法/V2-C03/fig_v2_c03_star.tex` |
| Official location | PDF physical page 240; printed page 227; caption is 图 14.1 |
| Location evidence | `official_page_240_adjacent_text.txt`, `official_page_240_text_bboxes.html`, `official_page_240_layout.xml` |
| 300 dpi page | `official_page_240_300dpi.png`, direct Poppler render, 2481 × 3508 px, no resampling |
| 200 dpi page | `official_page_240_200dpi.png`, direct Poppler render |
| Figure view | `after_figure_crop_300dpi.png`, native-pixel crop `(550,1370,2000,2150)`, no scaling |
| Standalone view | `standalone_page_300dpi_raw.png`; its unscaled nonwhite crop is `after_standalone_300dpi.png` |
| Grayscale view | `after_grayscale_300dpi.png`, created from the native 300 dpi crop without resizing |

## Mandatory acceptance matrix

| Required check | Result | Evidence / measured result |
|---|---:|---|
| `FOUR_VIEWS_COMPLETE` | true | page 200 dpi, figure crop 300 dpi, standalone 300 dpi, grayscale 300 dpi above |
| `SOURCE_FONT_PASS` | false | 23 visible figure elements inherit 9.20 pt, below 9.50 pt; see `after_font_audit.csv` |
| `PIXEL_HEIGHT_PASS` | false | `T07_ELLIPSIS` is 6 px vs 22 px required math-base/operator threshold; see `after_pixel_measurements.csv` |
| `SAME_ROLE_SOURCE_PASS` | true | shared visible figure style is 9.20 pt; the failure is absolute 9.50 pt, not within-role drift |
| `SAME_CLASS_PIXEL_RATIO_PASS` | true | all directly comparable same-glyph-class ratios are within `[0.92,1.08]` |
| `ROLE_RATIO_PASS` | false | annotation 1.1786 vs `[0.95,1.10]`; formula baseline 0.9643 vs `[1.00,1.18]`; see `after_role_ratio_audit.csv` |
| `ILLEGAL_FOREGROUND_OVERLAP_PASS` | true | text–graphic foreground overlap total = 0 px |
| `CLIPPING_PASS` | true | 0 clipped pixels / every audited figure-crop and page-edge relation meets 6 px |
| `TEXT_TEXT_CLEARANCE_PASS` | true | minimum audited text–text gap = 23.00 px, versus 4 px |
| `TEXT_GRAPHIC_CLEARANCE_PASS` | false | `L06_XD_MINUS_1` → `NB04` = 4.472136 px vs required 5 px; zero overlap is not sufficient |
| `MATH_SEMANTICS_PASS` | true | arrows encode class-conditional dependence and absent feature-feature edges encode conditional independence; adjacent body explicitly confirms this |
| `TEXT_CONSISTENCY_PASS` | false | diagram uses `X_i`/`X_j` while formal definition and adjacent body use `X^{(i)}`/`X^{(j)}` |
| `CAPTION_PASS` | true | concise caption identifies conditional-dependence structure and agrees with body text |
| `READING_ORDER_PASS` | true | category → `Y` → arrows → feature nodes → conditional-independence statement → caption |
| `GRAYSCALE_PASS` | true | arrow direction, node containment, border/fill contrast, and formula region remain distinguishable without color |
| `PAGE_INTEGRATION_PASS` | true | 200 dpi page shows coherent continuation from definition/body to figure, caption, explanation, then §14.2 |
| `VISUAL_HARMONY_PASS` | false | the sub-threshold source font, 6 px ellipsis, role-scale violations, and 4.47 px node-label clearance prevent acceptance |

## Per-element enumeration and reproducibility

`after_semantic_object_inventory.csv` enumerates every visible text/formula object, four arrows, five node borders, one panel border, one formula border, and explicitly records absent markers, curves, ticks, and legend as `ABSENT_NOT_UNKNOWN`.

`after_text_measurement_overlay_300dpi.png` puts native element IDs and bboxes on the official crop. The semantic masks are `mask_text_formula_300dpi.png`, `mask_line_arrow_300dpi.png`, `mask_node_border_300dpi.png`, `mask_panel_border_300dpi.png`, and `mask_formula_box_border_300dpi.png`; absent visual types have dedicated empty masks.

The failed relation has additional raw evidence in a shared 1:1 native coordinate frame:

- `roi_xdminus1_node_border_1to1_300dpi.png`
- `mask_xdminus1_text_300dpi.png`
- `mask_xdminus1_node_border_300dpi.png`
- `overlay_xdminus1_node_border_clearance_300dpi.png`
- `xdminus1_node_border_clearance_native.json`

The raw closest pair is text `(y=1838,x=1514)` to border `(y=1840,x=1518)`, Euclidean distance `sqrt(20)=4.472136 px`; overlap is `0 px` and the hard threshold remains `5 px`.
