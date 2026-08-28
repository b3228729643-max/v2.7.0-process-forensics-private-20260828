# FIG-P210-01 — strict R1 visual-acceptance matrix

Candidate audited: official `strict_current_r91_fullbook/main_full.pdf`, physical PDF page 227 (printed page 214), Figure 13.2. This is a current-candidate audit only; no before/after assertion is made.

Render basis: native Poppler `pdftoppm` outputs at 200 dpi and 300 dpi. The 300 dpi figure crop is a pixel crop only (`x=300..2199`, `y=1580..2339`); it was not resized. `standalone_figure.tex` inputs the current figure source and compiled successfully with XeLaTeX solely to obtain an independent figure render.

| Goal 9.2.1 matrix item | Measured value | Result | Evidence / strict rationale |
|---|---:|---|---|
| SOURCE_FONT_PASS | `false` | FAIL | 42/51 visible spans have effective size below 9.5 pt: 8.7 pt (`E04–E30`, `E46`), 9.2 pt (`E02–E03`, `E35–E36`, `E38–E39`, `E43–E44`), or resolved `\footnotesize=9.265` pt (`E34`, `E37`, `E40–E42`, `E45`). See `after_font_audit.csv`. |
| PIXEL_HEIGHT_PASS | `false` | FAIL | `E04_L_SPLIT1_NUM` 23 px `<24`; `E10_L_SPLIT2R_NUM` 17 px `<24`; `E11_L_SPLIT2R_COLON` 23 px `<30`; `E14_L_SPLIT3L_COLON` 19 px `<30`. Full mapped bboxes are in `after_pixel_measurements.csv`. |
| SAME_CLASS_RATIO_PASS | `false` | FAIL | Same role/script drift breaches [0.92,1.08], e.g. axis `E02/E03=0.840/1.160`; right `2:y` components `E10/E11/E12=0.708/0.767/1.350`; see per-element ratios in the pixel CSV. |
| ROLE_RATIO_PASS | `false` | FAIL | BASE is the 36.50 px median of ordinary point/tree-node labels (no ticks exist). Axis labels are 0.575/0.795 of BASE (`E02/E03`), while normal annotations/legend/split text also fall below their specified ranges. |
| OVERLAP_PIXEL_COUNT | `1` | FAIL | `E22_L_POINT_D` and `E16–E18_L_SPLIT3R` have one 300 dpi effective foreground pixel in common; `after_overlap_report.csv`, `OVL-02`. |
| CLIP_PIXEL_COUNT | `0` | PASS | Candidate-PDF vector bboxes and native render show no text, marker, arrowhead, node, legend, or caption clipped by the figure/page edge. |
| MIN_TEXT_CLEARANCE_PX | `0` | FAIL | `L_POINT_F`/`L_SPLIT2R` and `L_POINT_D`/`L_SPLIT3R` mapped text bboxes intersect (0 px vs required 4 px); `OVL-01`, `OVL-02`. |
| VISUAL_HARMONY_PASS | `false` | FAIL | The small split labels and mixed script sizes are visually weaker than the structural geometry; the two label collisions interrupt the left-panel reading path. |
| MATH_SEMANTICS_PASS | `false` | FAIL | The displayed third-level `3:x` cuts are at `x=5` and `x=9`, but the stated upper-median construction has terminal depth-2 leaves `A(2,3)`, `B(4,7)`, `E(8,1)`; if leaf cuts were drawn their x values would be 2, 4, 8. The tree itself has no depth-2 x-split nodes. |
| TEXT_CONSISTENCY_PASS | `false` | FAIL | Source caption line 68 and adjacent text line 432 say that the illustrated cuts/tree correspond; the unmatched `3:x` cuts contradict that claim and the tree’s visible axis labels. |
| GRAYSCALE_PASS | `true` | PASS | In `grayscale_300dpi.png`, solid/dashed convention plus geometry/tree structure preserves the x/y distinction; no color-only semantic dependency was found. |
| PAGE_INTEGRATION_PASS | `true` | PASS | `official_page_227_200dpi.png` shows a stable figure width, caption placement, surrounding answer text, and the following section without clipping, orphaning, or abnormal blank space. |

## Critical locations and repair targets

| Failure | ELEMENT_ID / 300 dpi pixel bbox | Source line(s) | Executable repair action |
|---|---|---:|---|
| Effective font under 9.5 pt | `E02` `[996,2126,1021,2165]`, `E03` `[398,1685,421,1724]`; grouped complete list in `after_font_audit.csv` | 28–29 | Raise the axis-label style to at least 9.5 pt effective, then rerender. |
| Effective font under 9.5 pt | `E04–E18`, `E19–E30`, `E46`; exact bboxes and lines in the two audit CSVs | 31–45, 66 | Raise split/point/legend/note styles from 8.7 pt to at least 9.5 pt; reflow labels rather than applying a global scale. |
| Effective font under 9.5 pt | `E34`, `E37`, `E40–E42`, `E45`; plus explicit node-axis labels `E35–E36`, `E38–E39`, `E43–E44` | 54–61 | Replace `\footnotesize` with an explicit >=9.5 pt tree font and raise node-axis annotation font to >=9.5 pt; enlarge/reflow nodes as needed. |
| Pixel-height shortfall | `E04` `[751,1712,770,1750]`; `E10` `[957,1832,976,1869]`; `E11` `[975,1831,1012,1870]`; `E14` `[703,2081,740,2120]` | 31, 35, 37 | The same targeted font increase must be followed by fresh native 300 dpi measurements of each substring. |
| Text collision / clearance | `E24_L_POINT_F` `[906,1806,1020,1843]` vs `E10–E12_L_SPLIT2R` `[957,1831,1033,1870]`, bbox clearance 0 px | 35, 42 | Move the right `2:y` label below/right of its dashed line or move the `F(9,6)` label; establish >=4 px text-text bbox clearance. |
| Actual text overlap | `E22_L_POINT_D` `[797,2004,913,2041]` vs `E16–E18_L_SPLIT3R` `[817,1966,895,2006]`, 1 px / bbox clearance 0 px | 39, 42 | Remove/reposition the `3:x` label; rerender until overlap is exactly 0 and clearance is >=4 px. |
| kd-tree semantics | `E13–E18` are the visible `3:x` labels | 36–39; compare chapter lines 347, 390–432 | Preferred: remove the terminal `x=5` and `x=9` lines/labels because the drawn leaves are terminal. Alternative: draw only valid leaf-axis cuts at x=2,4,8 and add matching depth-2 axis entries to the tree; do not retain an unmatched cut. |

## Verification views used

- `official_page_227_200dpi.png`
- `official_page_227_300dpi.png`
- `figure_crop_300dpi.png`
- `standalone_300dpi.png`
- `grayscale_300dpi.png`
- `roi_F_2y_300dpi.png`, `roi_D_3x_300dpi.png`, `roi_left_labels_300dpi.png`, `roi_tree_nodes_300dpi.png`
- `after_text_measurement_overlay_300dpi.png`, `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`

**Strict result: FAIL.** A re-audit is required after a source-only correction, fresh independent compilation, and fresh 300 dpi measurements.
