# FIG-P242-01 — SA1 strict visual-acceptance record (R1)

## Result

`RESULT: FAIL`

The frozen official candidate is `main_full.pdf` at physical PDF page **261** (printed page 248).  The task-card page 277 was not used as a substitute: direct text search in the frozen R91 candidate located the caption and adjacent body on page 261.  All raster evidence is a direct, unscaled Poppler 300 dpi/200 dpi render of that page; the 300 dpi page is 2481 × 3508 px.

## Required hard-gate matrix

| Gate | Result | Measured basis |
|---|---:|---|
| `SOURCE_FONT_PASS` | false | 23 non-script reader elements are below 9.5pt effective: tree/formula/leaf text 9.20–9.30pt (`E02,E04-E08,E10,E12-E16,E18,E20-E21,E23-E26,E28-E29`), and tick labels 8.70pt (`E31-E32`). |
| `PIXEL_HEIGHT_PASS` | true | Every split semantic text element meets its direct 300 dpi ink-height category minimum; full data are in `after_pixel_measurements.csv`.  This does **not** cure a source-font failure. |
| `SAME_CLASS_RATIO_PASS` | false | Several same-role groups exceed the 1.08 class spread: comparison operators 1.292, tree-leaf bases 1.143, tree-leaf scripts 1.444, region-label scripts 1.318, axis-label scripts 1.120.  Failing ELEMENT_IDs are listed in `failure_ledger.csv`. |
| `ROLE_RATIO_PASS` | false | Right title `E30` / right tick BASE (`E31,E32`) = 10.50/8.70 = **1.207**, above the panel-title maximum 1.20. |
| `OVERLAP_PIXEL_COUNT` | **12** | `E07` (top gold `否`) ↔ `G07` gold arrow = **10 px**; `E15` (lower blue `否`) ↔ `G09` blue arrow = **2 px**.  Both have 0px clearance and are hard FAILs. |
| `CLIP_PIXEL_COUNT` | **0** | All text/vector bboxes retain >=330px to the official page boundary. |
| `MIN_TEXT_CLEARANCE_PX` | false overall | Text–text = 35px (>=4), node text–border = 7px (>=5), page edge = 330px (>=6), cross-panel = 276px (>=8); text–line/arrow minimum = **0px** (<3) because of the two collisions. |
| `VISUAL_HARMONY_PASS` | false | The low tree/tick typography, right title/tick hierarchy excess, and branch-label arrow contacts prevent strict harmony acceptance. |
| `MATH_SEMANTICS_PASS` | true | `x_1\le2.4` maps to `R_1`; `x_1>2.4,x_2\le1.6` maps to `R_2`; and `x_1>2.4,x_2>1.6` maps to `R_3`.  The right partition uses exactly the 2.4 and 1.6 boundaries. |
| `TEXT_CONSISTENCY_PASS` | true | Caption source line 72 and direct body line `V2-C04.tex:287` agree with both panels. |
| `GRAYSCALE_PASS` | true | Diagonal hatches for `R_1/R_2`, dotted `R_3`, labels, and solid/dashed boundary coding remain distinguishable in `figure_grayscale_300dpi.png`. |
| `PAGE_INTEGRATION_PASS` | true | The complete 200 dpi page shows stable caption/body flow and no page-level clipping or disruptive break. |

Only a matrix of all-true boolean gates with zero overlap and clipping can PASS.  This candidate does not qualify for SA3.

## Direct text, caption, and reading-order review

- Caption (source line 72; official page 261): “决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域。” It is one concise read-out conclusion, not a duplicated procedure.
- Adjacent body (`V2-C04.tex:287`; official page 261): it explains that the left root-to-leaf paths correspond to mutually exclusive right-hand regions, and that covering the input space gives a unique prediction.
- Reading order is left decision tree → leaf `R_i` → matching right partition region; the gold path provides a concrete `R_2` correspondence.  This is intelligible, but strict clearance defects at the two `否` labels remain unacceptable.

## Collision-specific evidence and minimum repair direction

| Element / vector | Source line(s) | Native 300dpi bbox (text ; vector) | Measured | Minimum repair |
|---|---|---|---|---|
| `E07` top `否` ↔ `G07` gold root-to-node arrow | text 38; vector 7,37 | `736,1058,775,1097 ; 681,1018,749,1115` | 10 overlap px, 0px clearance | Move the edge-label node right/up by about 1.5–2pt (or bend/move the arrow) and remeasure until overlap=0 and clearance>=3px. |
| `E15` lower `否` ↔ `G09` blue node-to-`R_3` arrow | text 42; vector 19,42 | `873,1253,912,1292 ; 818,1214,886,1310` | 2 overlap px, 0px clearance | Shift label right/up by about 1.5–2pt (or move the arrow); drawing order alone is not a repair. |

See the paired native ROIs and semantic masks: `roi_overlap_E07_G07_1to1_300dpi.png`, `semantic_mask_overlap_E07_G07_300dpi.png`, `roi_overlap_E15_G09_1to1_300dpi.png`, and `semantic_mask_overlap_E15_G09_300dpi.png`.

## Source-directed repair queue

1. Replace the tree `\footnotesize` override at source line 34 and all 9.2pt branch/path settings (lines 8, 36–48) with a safely >=9.5pt effective local specification (use >=9.6pt to leave measurement margin), then reflow nodes and path annotation without global `scale`, `resizebox`, or `scalebox`.
2. Raise PGFPlots `tick label style` at line 24 from 8.7pt to >=9.6pt.  That also corrects `E30`/tick role ratio to approximately 10.5/9.6=1.094.
3. Eliminate both branch-label arrow intersections with coordinate-level shifts, then regenerate all 300 dpi masks.
4. Requalify the same-class groups in `failure_ledger.csv`.  For patterned leaf/region labels, a minimal robust option is a consistent small opaque/halo label backing that preserves the visual coding while preventing pattern-dependent ink measurements.  For `>` versus `\le`, either predeclare genuinely distinct operator roles with a visual rationale or use a comparator treatment whose rendered operator class meets the strict 0.92–1.08 range.

## Evidence used

- `official_page_0261_200dpi.png` — full page integration.
- `official_page_0261_300dpi.png` — native measurement source; no resize.
- `figure_crop_300dpi.png` and `standalone_figure_only_300dpi.png` — direct native crops, not separately rescaled renders.
- `figure_grayscale_300dpi.png` — grayscale coding review.
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_element_inventory.csv`, `failure_ledger.csv` — traceable source/font/pixel/vector evidence.
- `after_text_measurement_overlay_300dpi.png`, `semantic_mask_*.png`, and `roi_*_1to1_300dpi.png` — original-grid inspection evidence.

