RESULT: FAIL

# FIG-P172-01 — independent SA1 strict R1 review

## Scope and method

- Official candidate: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r90_fullbook/main_full.pdf`, physical page 187.
- Figure: 11.1, source `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C11/fig_v1_c11_tagging.tex`.
- Read-only review.  No source, wrapper, public style, inventory, or project-state file was modified.
- The official page was directly rasterized once with `pdftocairo -png -f 187 -l 187 -r 300`; its native dimensions are **2481 × 3508**.  All measurement bboxes, masks, and ROIs use those pixels at 1:1, with no resize or resampling.
- Text boxes were independently extracted from the official PDF vector page and mapped with 300/72 px per PDF point.  Foreground masks retain core ink whose local-background contrast is comfortably above the required 20/255; antialiased pale-edge pixels are excluded rather than used to inflate values.

## Element coverage

The text inventory contains 25 reader-visible semantic parent elements and 50
granular measurement elements (base and natural script components separated):

- Panel titles: `P172-TITLE-HMM`, `P172-TITLE-CRF`.
- HMM: `P172-HMM-HY1`, `HY2`, `Y-GAP`, `HY3`, `HX1`, `HX2`, `X-GAP`, `HX3`.
- CRF: `P172-CRF-CY1`, `CY2`, `Y-GAP`, `CY3`, `CX1`, `CX2`, `X-GAP`, `CX3`.
- Condition annotation: `P172-CONDITION`; legend: `P172-LEGEND-LATENT`,
  `-OBSERVED`, `-FACTOR`, `-GENERATIVE`; caption: `P172-CAPTION-L1`,
  `P172-CAPTION-L2`.

The graphic-object inventory covers HMM latent/observed node borders
`hy1..hy3`, `hx1..hx3`; all six directed HMM arrows; CRF node borders
`cy1..cy3`, `cx1..cx3`; six factor boxes `f12`, `f23a`, `f23b`, `g1..g3`;
all ten undirected edge segments; the condition brace; and four legend samples.
Each text group was checked against its own node/border and incident paths or,
for sequence labels/legend/caption/title, every locally adjacent independent
object.  All 300 mutual text-parent bbox pairs were checked, as were the
nearest cross-panel pair and physical page edge.

## Hard findings

1. **Source font gate fails.**  `P172-CONDITION` and the four legend labels
   explicitly resolve to effective 9.20pt (PDF spans 9.166pt), not 9.50pt.
   This is a direct failure even though their raw pixel heights happen to meet
   their character-class floors.  The default named node content resolves to
   10pt through the later common `every node/.append style={font=\small}`;
   natural math scripts derive legally from that 10pt baseline.

2. **The four ellipses fail the pixel-height floor.**  `P172-HMM-Y-GAP`,
   `P172-HMM-X-GAP`, `P172-CRF-Y-GAP`, and `P172-CRF-X-GAP` all have
   `H_ink=4px`.  They are visible sequence-continuation markers, hence
   nondecorative base math symbols under the stated 22px floor.  No exemption
   exists in §9.2.1 for an information-bearing ellipsis.

3. **Natural-script same-class ratio fails.**  In both panels, the four
   isolated `t` scripts measure 23px and the `t+1`/`T` scripts measure 26px.
   The measured ratio 0.885 is below [0.92, 1.08].  All script components are
   explicitly retained in `after_pixel_measurements.csv`; this is not masked
   by the taller base Y/X glyphs.

4. **Node inner-clearance fails despite zero overlap.**  Required text-to-own-
   border clearance is 5px.  Native 1:1 measurements are:

   | Text group | Measured px | Status |
   |---|---:|---|
   | HMM `Y_{t+1}` | 3.000 | FAIL |
   | HMM `X_{t+1}` | 2.000 | FAIL |
   | CRF `Y_{t+1}` | 2.828 | FAIL |
   | CRF `X_{t+1}` | 3.000 | FAIL |

   The four clearances are visibly corroborated in the named 100% ROI files.
   `OVERLAP_PIXEL_COUNT=0` does not waive a clearance floor.

5. **Role classification was kept conservative.**  The HMM/CRF strings are
   named panel titles, not serial `(a)/(b)` labels, so the panel-label
   [1.05,1.20] lower bound was not incorrectly imposed.  Their actual
   emphasis ratios lie in [0.90,1.25].  Caption PDF spans were split only to
   check mixed-script height floors; same-class label ratios are assessed at
   the semantic caption-line level, not falsely across fragments of one line.

   **Preliminary diagnostics explicitly excluded from the final failure set:**
   `P172-TITLE-HMM.LATIN` and `P172-TITLE-CRF.LATIN` each have a diagnostic
   ratio of 1.000, but the serial-panel-label lower bound is inapplicable;
   `P172-CAPTION-L1.CJK_2` has a fragment diagnostic ratio of 1.081, but is a
   component of one semantic caption line, not an independently sized label.
   All three are `PASS` in the final CSV.  The final result is therefore
   **22 component rows in six real failure classes**, not the preliminary
   25-row count.

## Geometry, clipping, and views

- Illegal text-text/text-graphic overlap: **0px**.  The nearest of all 300
  text-parent pairs is the two caption lines at 10px (requirement 4px).
- Cross-panel nearest reader text: 160px (requirement 8px).
- Text/figure physical-page edge minimum: 258px (requirement 6px).
- `CLIP_PIXEL_COUNT=0`.
- The condition label to brace is 6px (requirement 3px); HMM sequence marker
  to arrow is 8.246px; CRF sequence marker to factor border is 4px.  All
  non-node-border local object relations pass.  Full details are in
  `after_overlap_report.csv`.
- Grayscale preserves the essential directional and structural coding; page
  integration is good.  However the visibly tight `t+1` nodes, undersized
  source-font labels, and near-vanishing ellipses make visual harmony fail.

## Mathematical and textual review

The HMM panel correctly depicts `Y_t → Y_{t+1}` and `Y_t → X_t`; the CRF
panel correctly depicts undirected transition and observation factors, with
the observation row conditioned on bold `x`.  Empty/hatched circles, factor
squares, arrows, brace, and legend agree.  The caption's distinction between
HMM arrows and CRF undirected factors is correct.  The following reading
sentence correctly links a changed lower-case assignment `y_t` to local
observation and adjacent transition terms; upper-case figure nodes are random
variables, so it is not a notation contradiction.

## Required SA2 repair targets

Raise the condition annotation and all legend labels to at least 9.5pt
(10pt is the stable local baseline), enlarge/re-layout the four `t+1` circular
nodes until measured inner clearance is at least 5px, and replace the tiny
ellipsis notation with a full-height continuation marker that independently
clears the 22px floor.  Rework the sequence-label typography so actual natural-
script ink ratios satisfy [0.92,1.08] without invisible padding, hidden glyphs,
or a source-size drift.  A fresh official-page render and fully independent
SA1/SA3 review are required after any repair.

## Evidence files

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `after_visual_acceptance.md`
- Native page, crop, grayscale, and 1:1 ROI PNGs in this directory

This is an independent SA1 **FAIL**; no source-change authorization is implied.
