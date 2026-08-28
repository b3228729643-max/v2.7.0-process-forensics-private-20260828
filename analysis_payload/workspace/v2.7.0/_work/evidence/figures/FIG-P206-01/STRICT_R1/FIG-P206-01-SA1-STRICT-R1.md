# FIG-P206-01 — SA1 STRICT_R1 independent audit report

RESULT: **FAIL**

## Assigned scope and evidence boundary

- Figure: `FIG-P206-01` / 图13.1, Lp unit balls.
- Official candidate: `strict_current_r91_fullbook/main_full.pdf`.
- Requested physical-page locator 221 was independently checked. It is printed
  page 208 and contains only the prose reference. The actual visible figure and
  caption are physical PDF page **222**, printed page 209.
- Source inspected read-only:
  `src/绘图源码/第02册_基础监督学习方法/V2-C02/fig_v2_c02_lp_balls.tex` and
  `src/讲义源码/第02册_基础监督学习方法/chapters/V2-C02.tex:193–194` plus direct
  style dependencies required to recover font and color/axis settings.
- No source, PDF, style, manifest, state, or central record was changed. Every
  artifact written by this audit is within this `STRICT_R1` directory.

## Independent render/inspection record

| Required view | Evidence and result |
|---|---|
| official full page 200dpi | `official_r91_p221_full_200dpi.png`, `official_r91_p222_full_200dpi.png`; both inspected |
| official full page 300dpi | `official_r91_p221_full_300dpi.png`, `official_r91_p222_full_300dpi.png` |
| current figure crop 300dpi | `official_r91_p222_figure_crop_300dpi.png`; crop is native pixels, no resize |
| standalone 300dpi | `official_r91_p222_standalone_extracted_300dpi.png`; native direct extraction from R91 candidate |
| grayscale 300dpi | `official_r91_p222_figure_crop_grayscale_300dpi.png`; inspected |
| 1:1 diagnostics | q-label, tick/curve, label/axis, annotation ROIs; see files prefixed `roi_` |
| per-element overlays | `after_text_measurement_overlay_300dpi.png`, `after_overlap_semantic_masks_300dpi.png`, `after_tick_curve_semantic_masks_300dpi.png` |

The current-source wrapper `official_r91_standalone_wrapper.tex` was compiled
only as an independent environment check; its driver returned error 1 and the
resulting PDF is invalid. It was not used to claim a standalone visual PASS.

## Decisive failures

1. **Source font gate:** ticks are 8.5pt (source line 10); p/q/direct-note
   labels are 9.2pt (lines 4–7, 46, 50–55). Both are below 9.5pt effective,
   with graphics scale exactly 1.000. See `after_font_audit.csv`.
2. **Raw pixel gate:** `TICK_X_NEG1_MINUS` and `TICK_Y_NEG1_MINUS` are 3px
   against 22px; `LABEL_P2_EQUALS` and `LABEL_PINF_EQUALS` are 13px against
   22px; `LABEL_PINF_INFINITY` is 18px against 22px. Exact bboxes, source
   locations, and raw measurement paths are in `after_pixel_measurements.csv`.
3. **Illegal overlap:** four tick glyphs are painted through by the Lp
   boundaries: 22 + 9 + 82 + 21 = **134** effective `TEXT∩DATA_CURVE` pixels.
   `TICK_Y_POS1`, `TICK_X_NEG1_MINUS`, `TICK_X_POS1`, and
   `TICK_Y_NEG1_DIGIT` all resolve to source line 10. See
   `after_overlap_report.csv` and the magenta semantic overlay.
4. **Net clearance:** q1 text (`LABEL_Q1_Q`/`LABEL_Q1_SUB1`, line 52) is 2.2px
   from `MARKER_Q1`; q2 text (`LABEL_Q2_Q`/`LABEL_Q2_SUB2`, line 53) is 0.0px
   from `MARKER_Q2`. Required clearance is 3px. The two dedicated raw 1:1 ROIs
   and SVG semantic mask overlay make this directly reproducible.
5. **Caption-to-visual mismatch:** `CAPTION_TEXT` at raw bbox
   `(883,1311,1934,1348)`, source line 58, says which training points enter a
   query neighborhood first, but the figure only encodes query points and
   abstract Lp-boundary hits, not a training-point set/order.

## Positive checks retained

- `CLIP_PIXEL_COUNT=0`; raw foreground is 14px or more from the figure crop
  edge.
- Same-class ratios pass after splitting natural scripts/operators into
  independent element IDs; plot role hierarchy ratios pass.
- The three mathematical boundaries and six hit coordinates agree with the
  unit-ball equations and the two rays (calculation in
  `after_visual_acceptance.md`).
- Solid/dashed/dash-dot outlines and marker shapes remain distinguishable in
  the grayscale view.
- The real page-222 layout is coherent; the locator discrepancy is recorded,
  not used to fabricate a page-layout failure.

## Decision

`PASS` is prohibited. The complete 12-gate matrix, integer overlap/clip count,
clearance ledger, mathematical consistency computation, and precise repair
actions are in `after_visual_acceptance.md`. The next valid step is a targeted
source repair followed by a new official build and an entirely fresh native
300-dpi audit.
