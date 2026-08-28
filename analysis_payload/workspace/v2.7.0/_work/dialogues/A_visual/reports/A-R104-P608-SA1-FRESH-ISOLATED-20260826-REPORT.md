# FIG-P608-01 R104 Fresh Isolated SA1 Report

- HANDOFF_ID: `A-R104-P608-SA1-FRESH-ISOLATED-20260826`
- Role: fresh isolated read-only SA1
- Candidate: `strict_current_r104_fullbook/main_full.pdf`
- Source checked: `fig_v5_c03_trace_running_mean.tex`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R9_SA1_FRESH_ISOLATED_R104_20260826`
- Decision: `PASS`
- Next status: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
- `A_LOCAL_PASS`: not claimed
- SA3 started: no

## Independent location and scope

The target was independently located from source phrases in the R104 PDF text layer at physical PDF page 661 (1-based), printed page 648, figure 32.8. The page is 595.2760 x 841.8900 pt. The standalone TikZ graph is the UID object boundary; the caption, surrounding prose, and page composition were reviewed for fusion and cropping but are excluded from the object denominator.

Only the authorized R104 PDF, current single source, GOAL.md, current strict protocol, and current evidence schema were used. No older FIG-P608-01 evidence, SA result, handoff, state, inventory, task packet, route log, chat conclusion, or git history was read. No TeX engine or build command was run, and no source was modified.

## Complete denominators

- Visible non-space text glyph objects: 68
- Semantic foreground graphic objects: 19
- Source-declared hatch background objects: 2
- Total graphic objects: 21
- Total objects: 89
- All unordered object pairs: C(89,2) = 3916; checked 3916/3916
- Raw PDF drawing records mapped exactly once: 58/58
- Portable ordinary object masks: 89/89
- Math-rule objects: 6/6 manually reviewed
- Actual-intersection or critical relationship ROIs: 23/23 manually reviewed with raw, A, B, intersection, 1x overlay, and nearest-neighbor 8x overlay views
- Full glyph cells manually reviewed: 68/68, each with original, overlay, mask-only, and nearest-neighbor 8x views

## Hard-gate results

- Missing/tofu/wrong visible glyph: 0
- Wrong code point or mathematical semantic error: 0
- Unreadable glyph or formula: 0
- Visibly unbalanced role/script sizing: 0
- True clipping/cropping: 0 pixels
- Illegal non-whitelisted object overlap: 0 pixels
- Empty object masks: 0
- Unmapped or multiply mapped drawing records: 0
- Machine pair-gate failures: 0

Minimum measured clearances were 20 px for independent text-text pairs, 13 px for text/formula-to-graphic pairs, 154 px for cross-panel reader separation, and 20 px from text to the standalone-object edge. All exceed the applicable strict thresholds. No node, legend, or panel-border category is present.

All positive geometric intersections were manually classified as intended relationships: ticks with their axes, orthogonal axes at the origin, axes/curves/boundaries with the declared hatch background, the first top-trace point on the y-axis because the declared domain starts at t=1, and the lower running-mean curve crossing the target line. The two overline-to-formula critical relations have 7 px clearance and are correct.

## Typography, grayscale, semantics, and page fusion

Every glyph contour and all six math rules are complete and free of foreign pixels. Source role sizes are internally coherent: ordinary text 9.6 pt, panel/axis labels 10.8 pt, and natural scripts 7.56 pt, with no scaling transform. Pixel heights satisfy the applicable legibility minima, and repeated punctuation and cross-panel same-codepoint checks are stable. Font metadata and microscopic raster differences were treated only as R168 advisories.

The 20 trace values, warmup interval t=1..5, retained interval t=6..20, and 15 displayed running means were independently recomputed from the current source. They agree to source rounding; the final running mean at t=20 is 2.0000. `X_t`, `\overline X_{6:t}`, the target value 2, equality bars, overlines, line roles, markers, and panel relationships are semantically correct. Full-page, figure-crop, standalone, grayscale, and measurement-overlay views all pass readability, cropping, hierarchy, and neighboring-content fusion checks.

## Result

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

