# FIG-P222-01 — SA1 STRICT R1 formal review

## Result

`RESULT: FAIL`

This is a fresh, read-only, independent strict-SA1 review. It inspected only the fixed official candidate and the specified source, and wrote only this `STRICT_R1` evidence directory. No source, central status, or prior FIG-P222-01 SA report was read or changed. Since mandatory strict gates are false, this review does not start SA3.

## Candidate identity and exact location

| Field | Value |
|---|---|
| Figure ID | `FIG-P222-01` / 图 14.1 |
| Official candidate | `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r91_fullbook/main_full.pdf` |
| PDF length | 813 physical pages |
| Exact location used | physical PDF page **240**, printed page **227**, caption “图 14.1” |
| Figure source | `v2.7.0/_work/source/v2.7.0/src/绘图源码/第02册_基础监督学习方法/V2-C03/fig_v2_c03_star.tex` |
| Neighboring body source | `src/讲义源码/第02册_基础监督学习方法/chapters/V2-C03.tex`, lines 112–132 |
| Caption style source | `src/讲义源码/common/statlearnbook.sty`, lines 305–306 |

The direct 300 dpi official page render is `official_page_240_300dpi.png` (2481 × 3508 px). It was not scaled. `official_page_240_adjacent_text.txt` independently confirms both the caption and the immediately following explanation. The 1:1 figure crop is `(550,1400,2000,2150)` native pixels in `after_figure_crop_300dpi.png`.

## Audit method and coverage

The review used native 300 dpi pixels, PDF text-vector bboxes, and source-line enumeration. `after_semantic_object_inventory.csv` covers 28 text/formula components, four arrows, five node borders, the enclosing region, formula box, and each absent visual type (marker, curve, tick, legend) as explicitly absent rather than unknown.

`after_text_measurement_overlay_300dpi.png` is the bbox/ID overlay. `after_pixel_measurements.csv`, `after_font_audit.csv`, `after_role_ratio_audit.csv`, and `after_overlap_report.csv` give element- and relation-level native values. The semantic masks are native-coordinate masks, not inferred from resized images.

## Gate decision matrix

| Gate | Required threshold / condition | Actual | Result |
|---|---|---:|---:|
| Effective source font | visible figure text baseline ≥ 9.50 pt | 23 elements at 9.20 pt; scripts inherit a failing 9.20 pt parent | FAIL |
| Pixel glyph height | CJK ≥30; capital/digit ≥24; lowercase/Greek ≥17; base math/operator ≥22; natural script ≥15 px | `T07_ELLIPSIS` = 6 px vs 22 px | FAIL |
| Same-role source size | same role max/min ≤1.03 and difference ≤0.25 pt | source has a uniform 9.20 pt figure style | PASS |
| Same-class pixel ratio | `[0.92,1.08]` | no directly comparable-glyph-class failure | PASS |
| Role-scale ratios | annotation `[0.95,1.10]`; formula baseline `[1.00,1.18]` versus node-base role | 1.1786 and 0.9643 | FAIL |
| Illegal foreground overlap | 0 px | 0 px | PASS |
| Text–text clearance | ≥4 px | minimum 23.00 px | PASS |
| Text–line/arrow/mark clearance | ≥3 px | closest audited arrow relation 13.00 px | PASS |
| Node-text to node-border clearance | ≥5 px | `L06_XD_MINUS_1` → `NB04` = 4.472136 px | FAIL |
| Page / figure-edge clearance | ≥6 px | minimum audited crop-edge clearance 22.00 px | PASS |
| Cutting / clipping | 0 pixels | 0 pixels | PASS |
| Mathematical semantics | arrows and absent edges must mean the stated conditional relation | correct | PASS |
| Figure–text notation consistency | diagram notation must agree with surrounding formal definition | subscript versus superscript index convention differs | FAIL |
| Caption, order, grayscale, page fusion | all must be clear and correct | all four accepted | PASS |
| Visual coordination | no failed typography/spacing hierarchy gate | four visual hard failures remain | FAIL |

## Every source-font failure: native bbox, H, threshold, and repair direction

Source line 4 sets the global figure font to `9.2pt`; lines 8, 10, and 11 repeat `9.2pt` for their local roles. Each table row gives the element line in addition to the style line. `H` is the raw ink height in the official 300 dpi render and is included for reproduction; it cannot waive the independent source-font hard gate.

| ELEMENT_ID | Source line(s) | Native bbox px `(x0,y0,x1,y1)` | H px | Failed threshold | Minimum repair direction |
|---|---|---|---:|---|---|
| T01_CATEGORY | L4 + L8 | (1187,1433,1341,1475) | 33 | 9.20 pt < 9.50 pt | Raise category baseline to ≥9.50 pt and recheck hierarchy/spacing. |
| T02_Y_NODE | L4 + L17 | (1248,1536,1275,1578) | 28 | 9.20 pt < 9.50 pt | Raise shared node-label baseline to ≥9.50 pt; re-layout circle if needed. |
| T03_X1_BASE | L4 + L19 | (826,1797,854,1839) | 28 | 9.20 pt < 9.50 pt | Same shared node-label correction. |
| T04_X1_SUB | L4 + L19 | (853,1809,873,1848) | 25 | parent baseline 9.20 pt < 9.50 pt | Keep natural script only after its parent baseline is ≥9.50 pt. |
| T05_X2_BASE | L4 + L20 | (1033,1797,1060,1839) | 28 | 9.20 pt < 9.50 pt | Same shared node-label correction. |
| T06_X2_SUB | L4 + L20 | (1059,1810,1080,1848) | 25 | parent baseline 9.20 pt < 9.50 pt | Keep natural script only after its parent baseline is ≥9.50 pt. |
| T07_ELLIPSIS | L4 + L21 | (1244,1794,1284,1837) | 6 | 9.20 pt < 9.50 pt | Replace/rebuild continuation symbol during the global type re-layout; see separate pixel failure. |
| T08_XDM1_BASE | L4 + L22 | (1420,1795,1448,1837) | 28 | 9.20 pt < 9.50 pt | Raise baseline and re-layout `X_{d-1}` node. |
| T09_XDM1_SUB | L4 + L22 | (1447,1811,1519,1849) | 29 | parent baseline 9.20 pt < 9.50 pt | Keep script only after its parent baseline is ≥9.50 pt. |
| T10_XD_BASE | L4 + L23 | (1651,1795,1678,1837) | 28 | 9.20 pt < 9.50 pt | Same shared node-label correction. |
| T11_XD_SUB | L4 + L23 | (1677,1811,1701,1849) | 29 | parent baseline 9.20 pt < 9.50 pt | Keep natural script only after its parent baseline is ≥9.50 pt. |
| T12_REGION_CJK | L4 + L10 + L32 | (1105,1872,1423,1914) | 33 | 9.20 pt < 9.50 pt | Raise region-label baseline to ≥9.50 pt; calibrate against node base. |
| T13_REGION_Y | L4 + L10 + L32 | (1190,1873,1219,1913) | 27 | 9.20 pt < 9.50 pt | Raise region-label baseline to ≥9.50 pt. |
| T14_FORMULA_XI | L4 + L11 + L34 | (1087,1992,1117,2031) | 27 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt and calibrate ≥ node-base role. |
| T15_FORMULA_I | L4 + L11 + L34 | (1116,2008,1127,2036) | 22 | parent baseline 9.20 pt < 9.50 pt | Keep natural script only after formula baseline passes. |
| T16_FORMULA_PERP | L4 + L11 + L34 | (1139,1992,1167,2031) | 26 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt. |
| T17_FORMULA_XJ | L4 + L11 + L34 | (1177,1992,1207,2031) | 27 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt and calibrate ≥ node-base role. |
| T18_FORMULA_J | L4 + L11 + L34 | (1206,2008,1221,2036) | 28 | parent baseline 9.20 pt < 9.50 pt | Keep natural script only after formula baseline passes. |
| T19_FORMULA_MID | L4 + L11 + L34 | (1233,1992,1244,2031) | 35 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt. |
| T20_FORMULA_Y | L4 + L11 + L34 | (1254,1992,1283,2031) | 27 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt and calibrate ≥ node-base role. |
| T21_FORMULA_I_PAREN | L4 + L11 + L34 | (1324,1992,1354,2031) | 37 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt. |
| T22_FORMULA_NEQ | L4 + L11 + L34 | (1364,1992,1395,2031) | 36 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt. |
| T23_FORMULA_J_PAREN | L4 + L11 + L34 | (1404,1992,1441,2031) | 38 | 9.20 pt < 9.50 pt | Raise formula baseline to ≥9.50 pt. |

The caption elements `T24`–`T28` originate at L36 under `statlearnbook.sty:L305`; their effective 10.00 pt source size passes. They are retained in the complete audit CSV and inventory.

## Additional hard failures

| Failure ID | ELEMENT_ID / source line | Native bbox or raw measurement | Threshold | Result | Minimum repair direction |
|---|---|---|---|---|---|
| PIXEL-01 | `T07_ELLIPSIS`, L21 | bbox `(1244,1794,1284,1837)`; `H=6 px` | base math/operator ≥22 px | FAIL | Do not merely enlarge an isolated glyph. Rebuild the continuation representation as a semantically clear, sufficiently large figure component while preserving equal feature-node spacing; re-render at 300 dpi and measure ≥22 px. |
| ROLE-01 | `T01_CATEGORY` L8 `(1187,1433,1341,1475)`, `H=33`; `T12_REGION_CJK` L10/L32 `(1105,1872,1423,1914)`, `H=33` | median annotation 33 px / node-base median 28 px = 1.1786 | annotation `[0.95,1.10]` | FAIL | Recalibrate the enlarged source font so ordinary annotations are within the required ratio; do not fix by shrinking below 9.50 pt. |
| ROLE-02 | `T14_FORMULA_XI` L11/L34 `(1087,1992,1117,2031)`, `H=27`; `T17_FORMULA_XJ` `(1177,1992,1207,2031)`, `H=27`; `T20_FORMULA_Y` `(1254,1992,1283,2031)`, `H=27` | formula baseline median 27 px / node-base median 28 px = 0.9643 | formula baseline `[1.00,1.18]` | FAIL | Make the formula baseline at least the node-base role after raising it to ≥9.50 pt, then reflow its box. |
| CLEARANCE-01 | `L06_XD_MINUS_1` = `T08_XDM1_BASE`/`T09_XDM1_SUB`, L22 | text bbox `(1420,1795,1519,1849)`; nearest text `(y=1838,x=1514)` to `NB04` border `(y=1840,x=1518)`; 0 overlap; distance 4.472136 px | node text–border ≥5 px | FAIL | During the required font re-layout, increase the right-side node-text clearance by at least 0.527864 raw px (practically, enlarge/recenter the node or shift/recompose label) and remeasure at 300 dpi. |
| FIGTEXT-01 | diagram L19–L23 and L34 | diagram labels/formula use `X_1`, `X_i`, `X_j`; surrounding definition L113–L120 and explanation L132 use `X^{(1)}`, `X^{(j)}` | same semantic feature index notation across diagram and formal text | FAIL | Choose the chapter convention—here `X^{(j)}`—for node labels and formula, then widen/re-layout nodes and verify all gates again. |

### Dedicated clearance evidence for `CLEARANCE-01`

The relation is independently reproducible without any scale transformation:

| Artifact | Purpose |
|---|---|
| `roi_xdminus1_node_border_1to1_300dpi.png` | raw 170 × 150 px 1:1 official-page ROI `(1380,1740,1550,1890)` |
| `mask_xdminus1_text_300dpi.png` | `L06_XD_MINUS_1` semantic text mask in that same ROI frame |
| `mask_xdminus1_node_border_300dpi.png` | `NB04` border semantic mask in that same ROI frame |
| `overlay_xdminus1_node_border_clearance_300dpi.png` | red text, blue border, and exact orange nearest-pixel segment |
| `xdminus1_node_border_clearance_native.json` | raw coordinates, 4.472136 px distance, 5 px threshold, 0 overlap |

## Checks that did not cause the FAIL result

Mathematical topology is correct: source L24–L27 has arrows from `Y` to each feature and source L29–L30 encloses the feature layer. Chapter L132 says those arrows mean `P(X^{(j)}\mid Y)` and explicitly rejects unconditional independence. The caption (L36) matches that reading.

All audited text–graphic foreground intersections are zero, all page/crop clipping checks are zero, the closest text–text pair is 23.00 px (≥4), and the closest arrow clearance is 13.00 px (≥3). Full-page 200 dpi, figure 300 dpi, standalone 300 dpi, and grayscale 300 dpi were visually reviewed. Reading order and page fusion are coherent; grayscale preserves arrow direction, region grouping, nodes, formula, and caption without relying only on hue.

## Required re-audit scope after a fix

Any repair must be made in the figure source, not in this evidence directory. It requires a new official PDF build and fresh direct 300/200 dpi renders, then repeat all source-font, pixel, role-ratio, overlay, clearance, grayscale, semantics, caption, and page-integration checks. A PASS is not available until every false gate in this report becomes true.
