# FIG-P346-01 - independent SA1 strict recheck R1

## Verdict

**FAIL. Do not start SA3.**

The frozen R93 full-book figure fails the source-font, native-pixel-height, same-class-ratio, role-ratio, zero-overlap, visual-harmony, direct-text-consistency, and page-integration gates. One independently isolated TEXT/DATA_CURVE pair has 50 illegal overlap pixels.

## Scope and independence

- Figure: `FIG-P346-01`, caption `图 20.1 可复算的相切下界`.
- Frozen candidate: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r93_fullbook/main_full.pdf`.
- Official physical page: 375; printed page: 362.
- Read-only figure source: `v2.7.0/_work/source/v2.7.0/src/绘图源码/第03册_优化模型与序列模型/V3-C04/fig_v3_c04_bound.tex`.
- Direct body context: `v2.7.0/_work/source/v2.7.0/src/讲义源码/第03册_优化模型与序列模型/chapters/V3-C04.tex:234-256`.
- I did not read or inherit any earlier P346 R1/SA2/SA3/ROOT report or central-inventory conclusion. `STRICT_R1` did not exist when this audit began.
- I did not modify the figure source, chapter source, frozen full-book PDF, inventory, or central state. All generated files are confined to this evidence directory.

## Reproducible measurement method

1. The caption was located by direct text extraction from the frozen 813-page PDF. Poppler rendered physical page 375 directly at 300 dpi to 2481 x 3508 pixels and at 200 dpi for whole-page overview. No 300 dpi image was resized.
2. PDF character bboxes were mapped to pixels with `300/72`. Every visible in-figure token received a unique `ELEMENT_ID`; the rotated y-axis CJK glyphs were orientation-normalized before measuring `H_ink`.
3. Text masks were not inferred from broad bboxes. A one-page derivative retained the frozen page's text operators and removed path-painting operators; Poppler then rendered that independent text layer at native 300 dpi. Each token mask used local-background contrast `>=20/255` with no dilation.
4. Each line, arrowhead, curve, leader, marker, and note border was reconstructed from its own PDF vector object, preserving stroke width and dash pattern at 4x supersampling before mapping the same contrast threshold. No dilation was used. The 71 saved masks comprise 50 token TEXT masks, 7 logical TEXT-object masks, and 14 individually attributable graphic masks.
5. Foreground overlap and nearest coordinates use the independent masks. Text-text PASS additionally uses PDF/vector bbox clearance, not merely foreground distance. Edge/clip evidence and single-panel applicability are in `edge_clip_panel_report.csv`.
6. A real source-only wrapper was compiled to `v260_FIG-P346-01_standalone.pdf`, rendered directly at 300 dpi, and losslessly cropped to `standalone_300dpi.png`. The overlap is visible in both the frozen page and the independent standalone view.

## Four-view review

- `full_page_200dpi.png`: figure width and surrounding prose are balanced, but the following prose describes objects that are absent from the figure.
- `figure_crop_300dpi.png`: the teal dashed lower-bound curve visibly passes through its own label.
- `standalone_300dpi.png`: independently compiled source view reproduces the same label/curve collision.
- `grayscale_300dpi.png`: solid/dashed curve coding and the tangent marker remain distinguishable, but the collision remains visible.

There is one panel and no figure title, panel label, legend, panel border, or adjacent panel. Those checks are not applicable rather than unknown.

## A. Source effective-font audit

`GRAPHICS_SCALE=1.0000` for all elements. Same-role source sizes are internally uniform, and there is no cross-panel comparison, but the absolute 9.5 pt floor fails for 46 of 50 token elements.

- Source line 15, 8.50 pt: `T01_X_TICK_2`.
- Source line 31, 9.20 pt: `T04A_ELL_L`, `T04B_ELL_OPEN`, `T04C_ELL_THETA`, `T04D_ELL_CLOSE`.
- Source line 35, 9.20 pt: `T05A_BOUND_B`, `T05B_BOUND_OPEN`, `T05C_BOUND_THETA`, `T05D_BOUND_COMMA`, `T05F_BOUND_TWO`, `T05G_BOUND_CLOSE`, `T05H1_BOUND_CJK_1`, `T05H2_BOUND_CJK_2`, `T05H3_BOUND_CJK_3`.
- Source line 39, 9.00 pt: `T06A_TANGENCY_1`, `T06B_TANGENCY_2`, `T06C_TANGENCY_3`, `T06D_TANGENCY_4`, `T06E_TANGENCY_5`, `T06F_TANGENCY_6`, `T06G_TANGENCY_7`, `T06H_TANGENCY_8`.
- Source line 44, 9.00 pt: `T07A_FORMULA_L`, `T07B_FORMULA_OPEN1`, `T07C_FORMULA_THETA1`, `T07D_FORMULA_CLOSE1`, `T07E_FORMULA_MINUS1`, `T07F_FORMULA_B`, `T07G_FORMULA_OPEN2`, `T07H_FORMULA_THETA2`, `T07I_FORMULA_COMMA`, `T07J_FORMULA_TWO_ARG`, `T07K_FORMULA_CLOSE2`, `T07L_FORMULA_EQUALS`, `T07M_FORMULA_ZERO1`, `T07N_FORMULA_DOT`, `T07O_FORMULA_ONE`, `T07P_FORMULA_SIX`, `T07Q_FORMULA_OPEN3`, `T07R_FORMULA_THETA3`, `T07S_FORMULA_MINUS2`, `T07T_FORMULA_TWO_BASE`, `T07U_FORMULA_CLOSE3`, `T07V_FORMULA_EXP2`, `T07W_FORMULA_GE`, `T07X_FORMULA_ZERO2`. The exponent is not exempt because its base formula is only 9.00 pt, below the required 9.5 pt base.
- Only `T02_X_AXIS_THETA`, `T03A_Y_AXIS_目`, `T03B_Y_AXIS_标`, and `T03C_Y_AXIS_值` pass at 9.50 pt.

Exact declared, PDF-span, effective, and source-line values are in `after_font_audit.csv`.

## B. Native 300 dpi pixel-height failures

Five token elements miss their hard ink-height floor:

| ELEMENT_ID | Token | Class | H_ink | Required |
|---|---:|---|---:|---:|
| `T05H1_BOUND_CJK_1` | `：` | FULLWIDTH_SYMBOL | 20 px | 30 px |
| `T06D_TANGENCY_4` | `；` | FULLWIDTH_SYMBOL | 26 px | 30 px |
| `T07E_FORMULA_MINUS1` | `−` | MATH_OPERATOR | 4 px | 22 px |
| `T07L_FORMULA_EQUALS` | `=` | MATH_OPERATOR | 13 px | 22 px |
| `T07S_FORMULA_MINUS2` | `−` | MATH_OPERATOR | 4 px | 22 px |

All token bboxes, class medians, role ratios, and reasons are recorded in `after_pixel_measurements.csv`; `roi/roi_formula_operators_raw_1to1_300dpi.png` is the native raw operator view.

## C. Same-class and role-ratio failures

For formula-block `MATH_OPERATOR` elements, the class median is 37 px. `T07E`, `T07L`, `T07S`, and `T07W` have ratios 0.1081, 0.3514, 0.1081, and 0.8378, all outside `[0.92,1.08]`.

The tick `T01` is the 24 px BASE required by the protocol. Principal-glyph role medians are:

| Role | Median | Ratio to BASE | Allowed | Result |
|---|---:|---:|---:|---|
| TICK | 24 px | 1.0000 | `[1.00,1.00]` | PASS |
| AXIS_TITLE | 35 px | 1.4583 | `[1.00,1.18]` | FAIL |
| DIRECT_LABEL | 29 px | 1.2083 | `[0.95,1.10]` | FAIL |
| ANNOTATION | 32 px | 1.3333 | `[0.95,1.10]` | FAIL |
| FORMULA_BLOCK | 27 px | 1.1250 | `[1.00,1.18]` | PASS |

The machine-readable table and method are in `role_ratio_report.csv`.

## D. Zero-overlap, bbox clearance, edge, and clip audit

The sole illegal foreground-overlap pair is:

| Text object | Graphic object | N_overlap | Foreground clearance | Required | Bbox clearance | Nearest coordinates |
|---|---|---:|---:|---:|---:|---|
| `L05_BOUND_LABEL` | `G07_BOUND_CURVE` | 50 | 0.0000 px | 3 px | 0.0000 px, intersects | `(1648,1018)` / `(1648,1018)` |

The raw 1:1 ROI, independent TEXT mask, independent DATA_CURVE mask, overlap mask, and colored overlap overlay are saved under `roi/roi_bound_*`. The white overlap pixels lie on the math portion of `B(theta,2)`, matching the visible dashed stroke through the label.

Passing geometry checks:

- Text-text foreground minimum: 50.4480 px.
- PDF/vector text-text bbox minimum: 22.1158 px >= 4 px.
- X-axis `theta` foreground to external formula-note border: 9.0000 px >= 3 px, overlap 0. Its font bbox intersects the border bbox, which is why both bbox and actual-foreground fields are retained.
- Formula text to its own node border: 24.0000 px >= 5 px.
- Minimum tracked full-page edge clearance: 502.6244 px >= 6 px.
- `CLIP_PIXEL_COUNT=0` for every tracked text and graphic object.
- Cross-panel 8 px gate: not applicable because the figure has one panel.

All 119 logical relation rows, independent-mask methods, bbox fields, overlaps, clearances, and nearest coordinates are in `after_overlap_report.csv`.

## E. Mathematics, caption, body text, and reading path

The internal plotted mathematics is correct:

- `ell(theta)=3.8-0.18(theta-4.5)^2`.
- `B(theta,2)=ell(theta)-0.16(theta-2)^2`.
- At `theta=2`, both values are `2.675`.
- `ell'(2)=0.9` and `B'(2)=0.9`, matching the gold tangent line `2.675+0.9(theta-2)`.
- The displayed difference is nonnegative for every `theta`.

Therefore `MATH_SEMANTICS_PASS=true` and the caption itself is consistent. The within-figure reading order (tangent point -> two curves -> nonnegative difference) is also understandable.

However, `V3-C04.tex:256` says the reader should see “似然、当前相切下界、旧点、新点和上升箭头”. The figure has no distinct old point, new point, or ascent arrow. This is a direct and material `TEXT_CONSISTENCY_PASS=false` failure.

## F. Font visual coordination and page integration

The STIX Two and Noto Serif CJK families are stylistically compatible, and there is no oversized title or legend. The visual hierarchy is nonetheless unacceptable under the hard protocol:

- The 8.5 pt tick is an undersized BASE.
- Curve labels at 9.2 pt, the annotation at 9.0 pt, and the formula at 9.0 pt all miss the source floor.
- Their measured ink heights make axis, annotation, and direct-label roles exceed the permitted ratios to that BASE.
- The lower-bound curve physically cuts its own label, damaging legibility and making that annotation a visual collision rather than a clean direct label.
- The full page is not crowded and the formula block does not dominate, so shrinking text would be unjustified and prohibited here. Layout space should be recovered by movement/rewording, not by dropping below 9.5 pt.

Thus `VISUAL_HARMONY_PASS=false`, `FONT_VISUAL_COORDINATION_PASS=false`, and `PAGE_INTEGRATION_PASS=false`. Grayscale line-style hierarchy by itself passes.

## Minimal repair direction for SA2

1. Raise tick, direct-label, annotation, and formula bases to at least 9.5 pt. Do not shrink these already undersized roles. Rebalance the role medians after the absolute floor is met.
2. Move or re-anchor `B(theta,2)：下界`, or use a deliberate opaque halo/background, so its independent TEXT mask has zero intersection with the dashed curve and at least 3 px clearance without obscuring a key curve segment.
3. If the in-figure identity cannot satisfy the 22 px operator gate without becoming visually dominant, recompose it or move it into the adjacent prose/caption; merely enlarging the entire formula until it overwhelms the plot is not acceptable.
4. Rewrite `V3-C04.tex:256` to describe only the objects actually present, or add and then independently verify the promised old point, new point, and ascent arrow.
5. Recompile, regenerate all native 300 dpi evidence, repeat the complete audit, and obtain a new independent SA1 PASS. SA3 is forbidden before that PASS.

## Required evidence set

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `role_ratio_report.csv`
- `edge_clip_panel_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `after_visual_acceptance.md`
- `full_page_200dpi.png`, `full_page_300dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`
- `page375_text_only_independent.pdf/png` and `page375_graphics_only_independent.pdf/png`
- `masks/` (71 independent token/object masks)
- `roi/` (12 native 1:1 raw, mask, overlap, and nearest-point files)

Final SA1 result: **FAIL; SA3 not allowed.**
