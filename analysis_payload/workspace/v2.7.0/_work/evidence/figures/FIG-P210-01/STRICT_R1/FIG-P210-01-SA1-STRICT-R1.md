RESULT: FAIL

FIGURE_ID: FIG-P210-01 (Figure 13.2, official physical PDF page 227; printed page 214)

BLOCKERS:

1. Source-font hard gate fails for 42 of 51 reader-visible text spans. Effective values are 8.700 pt, 9.200 pt, or resolved `\footnotesize=9.265` pt instead of >=9.5 pt.
2. Pixel-height and ratio gates fail, including `E04_L_SPLIT1_NUM` 23 px `<24`, `E10_L_SPLIT2R_NUM` 17 px `<24`, `E11_L_SPLIT2R_COLON` 23 px `<30`, and `E14_L_SPLIT3L_COLON` 19 px `<30`.
3. `L_POINT_D` and `L_SPLIT3R` have one illegal 300 dpi foreground-overlap pixel; both this pair and `L_POINT_F`/`L_SPLIT2R` have 0 px text-bbox clearance, below the 4 px requirement.
4. The x=5/x=9 lines labeled `3:x` cannot be produced by the visible kd-tree/body construction. They invalidate the claim that the two panels depict the same cuts.

MATH_SEMANTICS:

FAIL. The required reconstruction is:

| Depth / active set | Axis / stable sort | Upper median and children | Candidate tree |
|---|---|---|---|
| 0, `{A(2,3),B(4,7),C(5,4),D(7,2),E(8,1),F(9,6)}` | x: A, B, C, D, E, F | `D(7,2)`; left `{A,B,C}`, right `{E,F}` | root D |
| 1-left, `{A,B,C}` | y: A(3), C(4), B(7) | `C(5,4)`; left A, right B | C with leaves A/B |
| 1-right, `{E,F}` | y: E(1), F(6) | `F(9,6)`; left E, right empty | F with leaf E |

Each of A–F occurs exactly once in the tree, and the root/first-level axes/tree labels agree with chapter line 347 and chapter lines 390–432. But source lines 36–39 draw third-level x-cuts at x=5 and x=9, values belonging to C/F’s first coordinate rather than the terminal leaves’ x values (2, 4, 8). No depth-2 x-split nodes appear in the tree. This is a mathematical/topological contradiction.

TEXT_CONSISTENCY:

FAIL. Caption source line 68 and adjacent text line 432 state that the illustrated cuts/tree correspond; the unmatched `3:x` cuts in source lines 36–39 contradict that relation. The title “相同切分生成的 kd 树” therefore overclaims correspondence.

READING_ORDER:

FAIL. The intended left-to-right path is understandable, but the invalid third-level labels and the two colliding left-panel labels force an ambiguous/incorrect interpretation before readers arrive at the tree.

SOURCE_FONT_AUDIT:

FAIL. Exact per-element records are in `after_font_audit.csv` and `after_pixel_measurements.csv`.

- `E02/E03`, source lines 28–29: 9.200 pt axis labels.
- `E04–E30`, source lines 31–45: 8.700 pt split labels, point labels, and legend.
- `E34/E37/E40–E42/E45`, source line 54 inherited into 55–61: resolved `\footnotesize=9.265` pt tree coordinate labels.
- `E35/E36/E38/E39/E43/E44`, source lines 55, 56, 60: 9.200 pt tree-axis annotations.
- `E46`, source line 66: 8.700 pt leaf-order annotation.

PIXEL_HEIGHT_AUDIT:

FAIL. Native 300 dpi, 20/255 foreground threshold, no resized image:

- `E04_L_SPLIT1_NUM`, source line 31, bbox `[751,1712,770,1750]`: H=23 px, digit minimum=24 px.
- `E10_L_SPLIT2R_NUM`, source line 35, bbox `[957,1832,976,1869]`: H=17 px, digit minimum=24 px.
- `E11_L_SPLIT2R_COLON`, source line 35, bbox `[975,1831,1012,1870]`: H=23 px, fullwidth minimum=30 px.
- `E14_L_SPLIT3L_COLON`, source line 37, bbox `[703,2081,740,2120]`: H=19 px, fullwidth minimum=30 px.

SAME_CLASS_RATIO_AUDIT:

FAIL. Examples from the mapped 300 dpi per-element audit: `E02/E03` axis-label ratios 0.840/1.160; `E10/E11/E12` right `2:y` ratios 0.708/0.767/1.350; `E14` ratio 0.633. All lie outside [0.92,1.08].

ROLE_RATIO_AUDIT:

FAIL. With no ticks, the declared local BASE is the 36.50 px median of ordinary point/tree-node labels. Axis labels `E02/E03` are 0.575/0.795 of BASE (required [1.00,1.18]); split labels range 0.466–0.849 (required annotation/legend-like [0.95,1.10]).

OVERLAP_PIXEL_COUNT: 1

`OVL-02`: `E22_L_POINT_D` bbox `[797,2004,913,2041]` and `E16–E18_L_SPLIT3R` bbox `[817,1966,895,2006]`, source lines 42 and 39, have one effective illegal 300 dpi foreground pixel in common. `OVL-01` has no retained common foreground pixel but still fails the independent 4 px text-bbox clearance rule (0 px).

CLIP_PIXEL_COUNT: 0

MIN_TEXT_CLEARANCE_PX: 0

`OVL-01` (`L_POINT_F` vs `L_SPLIT2R`, source lines 42/35) and `OVL-02` (`L_POINT_D` vs `L_SPLIT3R`, lines 42/39) have intersecting mapped bboxes. Both are below the mandatory 4 px text-text clearance.

VISUAL_HARMONY:

FAIL. Titles, points, and nodes are generally legible, and node borders/arrows stay clear, but the low-density split/legend text, invalid third-level cue, and pairwise collision prevent the geometry/tree relationship from having a stable first-read hierarchy.

FONT_AND_DENSITY:

FAIL. The source-level 9.5 pt hard floor is independently violated before any subjective readability judgment; several required 300 dpi substrings are also below their class minima.

LAYOUT:

FAIL. `OVL-01`/`OVL-02` establish two zero-clearance text pairs; `OVL-02` additionally has 1 px illegal foreground overlap. Other audited text-to-line, text-to-marker, node-border, page-edge, and arrowhead relationships pass their listed thresholds in `after_overlap_report.csv`.

GRAYSCALE:

PASS. `grayscale_300dpi.png` preserves x/y distinction through solid versus dashed line style and the tree structure. No semantic distinction depends solely on hue.

CAPTION:

FAIL. It is a concise single sentence, but its assertion that the displayed nodes/cuts correspond cannot be accepted until the third-level x-cuts are removed or made mathematically consistent.

PAGE_INTEGRATION:

PASS. `official_page_227_200dpi.png` shows normal width, caption spacing, and flow into the next section; no page-level clipping or abnormal whitespace was observed.

REQUIRED_FIXES:

1. Correct the mathematical topology first. Preferred minimal correction: delete source lines 36–39 (the terminal x=5/x=9 cuts and labels). If terminal cuts are intentionally meant to be shown, replace them with valid x=2/x=4/x=8 cuts and add the matching tree-node axis semantics; do not retain unmatched `3:x` labels.
2. Raise all reader-visible fonts to >=9.5 pt effective without global figure scaling: styles on source lines 5, 10–13; explicit labels on 55, 56, 60, 66; and replace the line-54 `\footnotesize` tree font by an explicit >=9.5 pt setting. Reflow minipanes/nodes and move labels as needed.
3. Move `L_SPLIT2R` or `L_POINT_F` to obtain >=4 px text-text clearance. Remove/reposition `L_SPLIT3R` as part of fix 1 to eliminate its collision with `L_POINT_D`; remeasure until illegal overlap is exactly 0.
4. Recompile the corrected figure and full candidate, regenerate native 200/300 dpi page renders and independent figure render, then redo every source/font/pixel/ratio/overlap check. PASS is unavailable until all matrix values are compliant.

EVIDENCE_USED:

- `official_page_227_200dpi.png`, `official_page_227_300dpi.png`, `figure_crop_300dpi.png`
- `standalone_figure.pdf`, `standalone_300dpi.png`, `grayscale_300dpi.png`
- Native 1:1 ROIs: `roi_F_2y_300dpi.png`, `roi_D_3x_300dpi.png`, `roi_left_labels_300dpi.png`, `roi_tree_nodes_300dpi.png`
- `after_text_measurement_overlay_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`
- Current source `fig_v2_c02_kd_tree.tex`, chapter `V2-C02.tex` lines 347, 390–432, and Goal sections 9.2.1/9.3 only.
