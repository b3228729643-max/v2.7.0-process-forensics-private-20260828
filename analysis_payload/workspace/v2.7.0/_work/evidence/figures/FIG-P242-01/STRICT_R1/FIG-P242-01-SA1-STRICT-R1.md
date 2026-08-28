# FIG-P242-01 — independent SA1 strict R1 report

RESULT: **FAIL**

FIGURE_ID: `FIG-P242-01` (图 15.1, 决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域)

CANONICAL_SOURCE: `v2.7.0/_work/source/v2.7.0/src/绘图源码/第02册_基础监督学习方法/V2-C04/fig_v2_c04_tree_partition.tex`

OFFICIAL_CANDIDATE: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r91_fullbook/main_full.pdf`

OFFICIAL_PDF_PHYSICAL_PAGE: **261** (printed page 248; independently identified from the official PDF’s figure caption/title text).  The static task-card value 277 does not match the frozen current candidate and was not treated as evidence.

## Independent locating and render chain

1. Direct PDF text search found the panel titles, the exact caption, and the adjacent explanatory paragraph on physical page 261.
2. That page alone was rendered directly from the official candidate using Poppler at 300 dpi and 200 dpi.  The 300 dpi evidence is the native 2481 × 3508px raster, with no resize operation.
3. All `BBOX_*` values in the CSVs use that original 300 dpi coordinate system.  Figure crop, figure-only crop, grayscale, ROIs, masks, and the overlay are all crops/conversions on the same original pixel grid.

## SA1 outcome required by section 9.2.1

| Required item | Finding | Status |
|---|---|---:|
| Source effective size | 23 regular reader elements render at 8.70–9.30pt, below >=9.5pt | FAIL |
| Actual 300 dpi ink height | All category minima meet the physical pixel threshold after script/token separation | PASS |
| Same-class ratio | Five class groups exceed max/min 1.08; detailed rows in `failure_ledger.csv` | FAIL |
| Role hierarchy | `E30` title / `E31,E32` tick BASE = 1.207 > 1.20 | FAIL |
| Illegal foreground overlap | 12 pixels total: `E07↔G07`=10, `E15↔G09`=2 | FAIL |
| Clipping | 0 pixels | PASS |
| Clearances | text–text 35px; node text–border 7px; edge 330px; cross-panel 276px; text–line 0px | FAIL due to text–line minimum >=3px |
| Four-view visual review | Full page, crop/figure-only, grayscale, and 1:1 ROIs inspected | Visual harmony FAIL; grayscale/page integration PASS |
| Math and text | Tree path/partition geometry, caption, and adjacent body all match | PASS |

No missing/unknown condition has been passed.  A FAIL result blocks SA3.

## Hard source-font failures (all rows include native bounding boxes)

The complete per-element record, including `ELEMENT_ID`, source line, native 300 dpi bbox, exact threshold, observed value, and minimum repair, is `failure_ledger.csv`.  The 23 source-font failure elements are:

| Effective size / source location | Failing elements (native bbox from `after_pixel_measurements.csv`) | Minimum repair direction |
|---|---|---|
| 9.30pt — tree `\footnotesize`, lines 16–19, 34–39, 42 | `E02(575,957,601,996)`, `E04(632,957,662,996)`, `E05(672,957,726,996)`, `E08(489,1152,517,1192)`, `E10(712,1152,738,1192)`, `E12(770,1152,800,1192)`, `E13(810,1152,863,1192)`, `E16(626,1347,654,1387)`, `E18(900,1347,928,1387)` | Remove the `\footnotesize` override and use a local effective >=9.6pt node/formula setting; enlarge/reflow the tree rather than globally scaling it. |
| 9.20pt — branch labels, lines 8, 36, 38, 41–42 | `E06(526,1058,566,1097)`, `E07(736,1058,775,1097)`, `E14(663,1253,702,1293)`, `E15(873,1253,912,1292)` | Raise the branch-label style to >=9.6pt and move the two `否` labels as specified below. |
| 9.20pt — gold path annotation/formula, lines 47–48 | `E20(452,1454,605,1493)`, `E21(643,1453,668,1492)`, `E23(694,1453,725,1492)`, `E24(734,1453,788,1492)`, `E25(796,1454,835,1493)`, `E26(843,1453,868,1492)`, `E28(894,1453,925,1492)`, `E29(934,1453,987,1492)` | Raise the entire annotation/formula baseline to >=9.6pt and preserve whitespace by moving/rewrapping the annotation, not by scaling the figure. |
| 8.70pt — PGFPlots ticks, lines 22–25, 54–58 | `E31(1832,1457,1883,1494)`, `E32(1336,1118,1385,1155)` | Set `tick label style` to >=9.6pt; retain the 10.5pt panel title. |

Natural scripts `E03,E09,E11,E17,E19,E22,E27,E34,E36,E38,E40,E42` each meet the >=15px script-height rule, but their parent formulas must still satisfy the >=9.5pt base-font gate.

## Exact native collision ledger

| Failure | Text source / native bbox | Graphic source / native bbox | Threshold and observed value | 1:1 evidence | Minimum fix |
|---|---|---|---|---|---|
| `E07` top gold `否` ↔ `G07` | line 38; `736,1058,775,1097` | lines 7,37; `681,1018,749,1115` | overlap must be 0; observed **10px**; clearance must be >=3px; observed **0px** | `roi_overlap_E07_G07_1to1_300dpi.png`, `semantic_mask_overlap_E07_G07_300dpi.png` | Offset edge label right/up ~1.5–2pt or route the arrow away, then re-render and require zero overlap. |
| `E15` lower blue `否` ↔ `G09` | line 42; `873,1253,912,1292` | lines 19,42; `818,1214,886,1310` | overlap must be 0; observed **2px**; clearance must be >=3px; observed **0px** | `roi_overlap_E15_G09_1to1_300dpi.png`, `semantic_mask_overlap_E15_G09_300dpi.png` | Offset label right/up ~1.5–2pt or move the blue arrow; z-order alone is not a fix. |

The top-level overlap row and the two individual rows are retained in `after_overlap_report.csv`.  The raw ROI image, not the colored diagnostic mask, is the proof image.

## Same-class and role-ratio blockers

| Class / elements | Raw 300dpi H_ink px | Threshold | Result / minimum repair |
|---|---|---|---|
| comparison operators `E04,E12,E23,E28` | 31,31,24,31; spread 1.292 | each H/median in [0.92,1.08], class max/min<=1.08 | FAIL.  Either predeclare `>` and `\le` as genuinely distinct visual roles with a rationale, or normalize the comparator treatment. |
| tree leaf `R` bases `E08,E16,E18` | 40,40,35; spread 1.143 | same | FAIL.  Use consistently measured/isolated leaf labels; a uniform small opaque/halo backing is a minimal robust option over the patterned cells. |
| tree leaf scripts `E09,E17,E19` | 39,37,27; spread 1.444 | same | FAIL.  Normalize label treatment and rerun the raw mask audit. |
| right region scripts `E34,E36,E38` | 29,29,22; spread 1.318 | same | FAIL.  Normalize text/background treatment before resubmission. |
| axis scripts `E40,E42` | 25,28; spread 1.120 | same | FAIL.  Normalize the x/y label script treatment and remeasure perpendicular to each local baseline. |
| right title `E30` / tick BASE `E31,E32` | effective ratio 10.50 / 8.70 = 1.207 | panel title / BASE in [1.05,1.20] | FAIL.  Raising ticks to >=9.6pt fixes this without reducing any reader text. |

## Visual, semantic, caption, and integration review

MATH_SEMANTICS: PASS.  The tree’s left branch `x_1\le2.4` maps to left region `R_1`; the gold path `x_1>2.4` and `x_2\le1.6` maps to bottom-right `R_2`; the remaining branch maps to top-right `R_3`.  The plotted split lines coincide with 2.4 and 1.6.

TEXT_CONSISTENCY: PASS.  Caption line 72 states the exact root-to-leaf/axis-aligned-region relation; adjacent body `V2-C04.tex:287` correctly adds mutual exclusivity and conditional coverage/unique prediction.

READING_ORDER: PASS.  The left-to-right panel order is clear, leaf labels identify corresponding regions, and the gold example route provides a concrete bridge.  The two label-arrow contacts prevent a visual-layout PASS despite this intelligible order.

GRAYSCALE: PASS.  The R1/R2 diagonal hatches, R3 dotted hatch, labels and boundary lines remain distinguishable in `figure_grayscale_300dpi.png`; color is not the sole signal.

CAPTION: PASS.  It is a single read-out conclusion and matches both the source and direct official-page text.

PAGE_INTEGRATION: PASS.  In `official_page_0261_200dpi.png`, the figure, caption, explanation and example start are stable and uncropped, without an isolated fragment or excessive page break.

VISUAL_HARMONY: FAIL.  The low tree/tick type, title/tick ratio excess, and both arrow contacts violate the required stable hierarchy and clear routing.  This conclusion does not rely on “it is still readable.”

## Required next action

Send only the listed source/coordinate fixes to SA2.  SA2 must generate a fresh official candidate and new 300dpi evidence; a new independent SA1 is required before SA3 may begin.

## Evidence used

- `official_page_0261_200dpi.png`, `official_page_0261_300dpi.png`
- `figure_crop_300dpi.png`, `standalone_figure_only_300dpi.png`, `figure_grayscale_300dpi.png`
- `roi_left_tree_1to1_300dpi.png`, `roi_right_partition_1to1_300dpi.png`, `roi_ticks_labels_1to1_300dpi.png`, plus the two collision ROIs/masks above
- `semantic_mask_text_300dpi.png`, `semantic_mask_line_arrow_border_300dpi.png`, `semantic_mask_colored_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_element_inventory.csv`, `failure_ledger.csv`, `measurement_summary.json`

