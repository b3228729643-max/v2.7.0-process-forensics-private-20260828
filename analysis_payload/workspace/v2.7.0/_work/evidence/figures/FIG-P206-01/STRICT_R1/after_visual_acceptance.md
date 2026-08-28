# FIG-P206-01 — STRICT_R1 visual acceptance

RESULT: **FAIL**

Audit target: the current official R91 full book. Physical PDF page 221 (printed
208) was first checked directly and contains the prose reference to 图13.1 only.
The diagram and its caption are on physical PDF page **222** (printed 209),
confirmed from the visible caption `图13.1 二维 Lp 单位球…`; all target-pixel
measurements therefore use page 222. Page-221 and page-222 official 200/300-dpi
renders are retained in this evidence directory.

## Required 12-item matrix

| Gate | Measured result | Verdict | Evidence |
|---|---:|---|---|
| `SOURCE_FONT_PASS` | ticks 8.5pt; p/q/direct-note labels 9.2pt; cumulative graphics scale 1.000 | false | `after_font_audit.csv` |
| `PIXEL_HEIGHT_PASS` | five required math/operator elements below C1 thresholds | false | `after_pixel_measurements.csv` |
| `SAME_CLASS_RATIO_PASS` | all same-role/same-script component ratios in `[0.92,1.08]` after semantic splitting | true | `after_pixel_measurements.csv` |
| `ROLE_RATIO_PASS` | plot-role vector-cell medians: axis 1.100; direct labels 1.025; query 1.025; note 1.075 to tick base | true | `after_pixel_measurements.csv` |
| `OVERLAP_PIXEL_COUNT` | **134** (`TEXT` ∩ `DATA_CURVE`) | false; must equal 0 | `after_overlap_report.csv`, `after_tick_curve_semantic_masks_300dpi.png` |
| `CLIP_PIXEL_COUNT` | 0; nearest figure-crop foreground edge 14px | true | `after_overlap_report.csv` |
| `MIN_TEXT_CLEARANCE_PX` | **0.0px** global; q1–marker 2.2px, q2–marker 0.0px | false; text/graphic must be ≥3px | `after_overlap_report.csv`, q ROI files |
| `VISUAL_HARMONY_PASS` | hidden/crossed tick glyphs plus q label crowding disrupt hierarchy | false | full/crop/standalone/ROI views |
| `MATH_SEMANTICS_PASS` | L1 diamond, L2 circle, Linf square and all six ray hits agree with source mathematics | true | source lines 30–45; calculation below |
| `TEXT_CONSISTENCY_PASS` | caption claims which *training points* enter first, but no training-point set/order is encoded; figure shows only query rays and boundary hits | false | source line 58; chapter line 194 |
| `GRAYSCALE_PASS` | solid/dashed/dash-dot boundaries and marker shapes remain distinguishable | true | `official_r91_p222_figure_crop_grayscale_300dpi.png` |
| `PAGE_INTEGRATION_PASS` | actual page 222 has coherent width, caption, and following example flow | true | `official_r91_p222_full_200dpi.png` |

Technical standalone check: `official_r91_p222_standalone_extracted_300dpi.png`
is a no-resize direct extraction from the official R91 page-222 diagram and was
visually inspected. A current-source wrapper was also attempted, but its driver
returned error 1 and produced an invalid 5,167-byte PDF (`pdfinfo` cannot find
the trailer); it is not used as a visual proof. This build limitation does not
weaken the official-PDF failures above.

## Source-size audit

There is no `scale`, `transform shape`, `resizebox`, or `scalebox` in the figure
source, so declared size × cumulative graphic scale is the effective size.

| Reader-visible role | Source location | declared/effective | Requirement | Result |
|---|---|---:|---:|---|
| tick labels | line 10 | 8.5/8.5pt | ≥9.5pt | FAIL |
| p=1/p=2/p=∞ labels | lines 46, 50, 51 via lines 4–5 | 9.2/9.2pt | ≥9.5pt | FAIL |
| q1/q2 labels | lines 52–53 via line 6 | 9.2/9.2pt | ≥9.5pt | FAIL |
| boxed note | lines 54–55 via line 7 | 9.2/9.2pt | ≥9.5pt | FAIL |
| axis titles | line 27 via line 10 | 9.5/9.5pt | ≥9.5pt | PASS |
| caption | line 58, document default | 11.0/11.0pt | ≥9.5pt | PASS |

## Pixel and pairwise failure facts

All coordinates below are raw page-222 300-dpi pixel coordinates with origin at
the official full-page raster's top left. `H_ink_px` uses C1 foreground
departure ≥20/255. Full rows, vector bboxes, class medians, source lines, and
methods are in `after_pixel_measurements.csv`.

| ELEMENT_ID | source line | raw bbox (x0,y0,x1,y1) | measured / threshold | hard failure |
|---|---:|---|---:|---|
| `TICK_X_NEG1_MINUS` | 10 | (762,834,786,837) | 3 / 22px | undersized operator; 9 curve-overlap px |
| `TICK_Y_NEG1_MINUS` | 10 | (1057,1141,1081,1144) | 3 / 22px | undersized operator |
| `LABEL_P2_EQUALS` | 50 | (1266,323,1291,336) | 13 / 22px | undersized operator |
| `LABEL_PINF_EQUALS` | 51 | (694,1065,719,1078) | 13 / 22px | undersized operator |
| `LABEL_PINF_INFINITY` | 51 | (736,1064,770,1082) | 18 / 22px | undersized baseline math symbol |
| `TICK_Y_POS1` | 10 | (1090,438,1096,462) | 24 / 24px | 22 `TEXT∩DATA_CURVE` px |
| `TICK_X_NEG1_MINUS` | 10 | (762,834,786,837) | n/a | 9 `TEXT∩DATA_CURVE` px |
| `TICK_X_POS1` | 10 | (1467,820,1477,845) | 25 / 24px | 82 `TEXT∩DATA_CURVE` px |
| `TICK_Y_NEG1_DIGIT` | 10 | (1088,1127,1100,1152) | 25 / 24px | 21 `TEXT∩DATA_CURVE` px |
| `LABEL_Q1_Q` + `LABEL_Q1_SUB1` | 52 | q base (1599,688,1618,716) | clearance 2.2 / 3px | too close to `MARKER_Q1` |
| `LABEL_Q2_Q` + `LABEL_Q2_SUB2` | 53 | q base (1400,367,1423,394) | clearance 0.0 / 3px | touching `MARKER_Q2` |

The 134 illegal overlap pixels are the non-overlapping sum of the four tick/data
curve pairs: 22 + 9 + 82 + 21. The semantic tick glyph masks come directly from
the official page SVG; they are intersected with raw blue/teal/gold C1 boundary
foreground. The colored curves are painted after the tick text in the official
SVG, and the native ROIs visibly show the resulting occlusion.

## Minimum-clearance ledger

| Object relationship | actual | required | result |
|---|---:|---:|---|
| independent text–text (`ANNOTATION_LINE1` ↔ `ANNOTATION_LINE2`) | 6px | ≥4px | PASS |
| q1 text–query marker | 2.2px | ≥3px | FAIL |
| q2 text–query marker | 0.0px | ≥3px | FAIL |
| tick text–Lp data curve | 0.0px and 134 overlap px | ≥3px and 0 overlap | FAIL |
| text–line/arrow | 3px | ≥3px | PASS |
| arrowhead–text | 26px | ≥3px | PASS |
| node-text–node-border | N/A: no node | ≥5px | N/A |
| text–panel-border / cross-panel | N/A: one unbordered panel | ≥5 / ≥8px | N/A |
| text–image edge | 14px | ≥6px | PASS |

## Four-view visual review

- `official_r91_p222_full_200dpi.png`: page integration is sound; the page has
  the figure, caption, and next example in normal flow.
- `official_r91_p222_figure_crop_300dpi.png`: readable overall geometry, but
  tick text is visibly run through by the boundaries and q labels crowd points.
- `official_r91_p222_standalone_extracted_300dpi.png`: the same failures remain
  without page context.
- `official_r91_p222_figure_crop_grayscale_300dpi.png`: curve and marker
  semantics survive through line/marker redundancy; this gate passes.

Native 1:1 proof: `roi_q1_marker_label_1to1_300dpi.png`,
`roi_q2_marker_label_1to1_300dpi.png`,
`roi_tick_xpos1_curve_1to1_300dpi.png`,
`roi_tick_ypos1_curve_1to1_300dpi.png`,
`roi_tick_xneg1_curve_1to1_300dpi.png`, and
`roi_tick_yneg1_curve_1to1_300dpi.png`. Element overlays are
`after_text_measurement_overlay_300dpi.png`,
`after_overlap_semantic_masks_300dpi.png`, and
`after_tick_curve_semantic_masks_300dpi.png`.

## Mathematical and textual review

For each query ray, the source hit coordinates (lines 40–45) agree to its shown
rounding with the three unit-boundary equations:

| query | L1 hit | L2 hit | Linf hit |
|---|---|---|---|
| q1=(1.34,0.25) | (0.8428,0.1572) | (0.9830,0.1834) | (1.0000,0.1866) |
| q2=(0.84,1.14) | (0.4242,0.5758) | (0.5932,0.8051) | (0.7368,1.0000) |

Thus the diamond `|z1|+|z2|=1`, circle `z1²+z2²=1`, and square
`max(|z1|,|z2|)=1` are mathematically correct, as is the intended ray-order
demonstration. But source line 58 says which *training points* enter a query
neighborhood first (`CAPTION_TEXT`, raw bbox `(883,1311,1934,1348)`) while the
graph contains neither a training-point set nor an ordering/legend for it; it
depicts only the two query points and abstract boundary hits. This is why
`TEXT_CONSISTENCY_PASS=false` despite mathematical geometry passing.

## Required repair actions before re-audit

1. At source lines 4–7 and 10, raise all ordinary reader-visible role sizes to
   at least 9.5pt effective (use 10pt or another justified value) and remeasure
   the raw 300-dpi output.
2. Replace the `p=…` labels (lines 46, 50, 51) with labels that do not retain
   13px equality glyphs; use an unambiguous larger `L_1`, `L_2`, `L_∞` labeling
   scheme and remeasure each script separately. Remove/redesign negative tick
   labels if their minus glyph cannot meet the operator rule at native size.
3. Hide the default `xtick`/`ytick` labels at line 28 and place opaque-background
   manual labels after the boundary plots, outside the Linf square and ≥3px from
   every curve. Do not merely change draw order: retain zero semantic overlap.
4. Move the q1 label at line 52 rightward and the q2 label at line 53 upward,
   allowing at least 3px final ink clearance after the larger font is applied;
   rerender and measure the q text and black query-circle masks separately.
5. Either revise the caption at line 58 to describe the visible first boundary
   intersections, or add labeled training points plus a stated ordering so its
   present claim is visibly supported.
6. Rebuild the official full book, generate a new native 300-dpi candidate, and
   repeat the complete source/pixel/overlap/clearance audit. A prior PASS cannot
   be inherited.
