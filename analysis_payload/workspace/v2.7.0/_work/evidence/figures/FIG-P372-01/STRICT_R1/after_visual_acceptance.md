# FIG-P372-01 — strict visual acceptance, SA1 R1

RESULT: **FAIL**

Candidate identification: frozen `main_full.pdf`, PDF physical page **405**, printed page **392**, figure **图 21.1**, label `fig:V3-C05-lattice`. The page was located from the current body context (chapter source lines 443–445: `\input`, label, and follow-up explanation) and then confirmed in the frozen candidate by its rendered caption.

## Required decision matrix

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = true
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 14.000
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
```

Any `false` is a hard stop under Goal §9.2.1. `SOURCE_FONT_PASS=false` and `ROLE_RATIO_PASS=false` therefore prohibit PASS and prohibit SA3. The unique next role is SA2.

## Evidence and method

- Full page: `after_full_page_200dpi.png`; direct Poppler render of the frozen PDF.
- Measurement source: `after_full_page_300dpi_measurement_raw.png`; direct PyMuPDF candidate-PDF render at exactly 300 dpi, 2481×3508 pixels, with no post-render resize.
- Required views: `after_figure_crop_300dpi.png`, `after_standalone_300dpi.png` (a no-scale direct PDF vector clip of the graph), and `after_grayscale_300dpi.png`.
- Text masks are constrained to real PDF `RAWDICT` character boxes and use local-background RGB difference ≥20/255. Native line, arrowhead, node-border, and node-fill paths come from real PDF `get_drawings()` paths and are independently replayed at 300 dpi; there is no mask dilation or same-colour flood-fill.
- `object_inventory.csv` records 89 real text components, 41 semantic text parents, and 123 independently represented native vector objects. `after_text_measurement_overlay_300dpi.png` plus `after_text_measurement_overlay_key.csv` maps every text measurement box to its ID.

## Hard-gate findings

1. Source font audit — FAIL

`after_font_audit.csv` has 89 reader-visible text-component rows. Seven 9.5pt title components pass. The other 82 fail: 21 tick components at 8.7pt, one ordinary annotation at 8.8pt, 27 node-label bases at 9.2pt, 27 natural scripts whose required base is only 9.2pt, and six caption font runs with locally unrecoverable effective size. No TikZ or external graphics scale is present (`GRAPHICS_SCALE=1.0000`); the failure is the declared/effective font choice itself.

2. Pixel-height audit — PASS

`after_pixel_measurements.csv` has 99 rows, including nine true parent-formula measurements for `t-1/t/t+1`, so a horizontal `+`/`−` stroke cannot distort a baseline-math measurement. All thresholded native-PDF 300dpi heights meet their applicable floors: CJK minimum 34px (≥30), Latin lowercase/Greek minimum 21px (≥17), uppercase/digit minimum 24px (≥24), base-math formula minimum 24px (≥22), and natural scripts minimum 19px (≥15). The six short horizontal operator components are traced individually and are assessed through their complete parent formula rather than misinterpreting a 3px horizontal stroke as a font-height failure.

3. Same-class and cross-panel ratios — PASS

`same_class_ratio_audit.csv` records every repeated same-role, same-script instance. Each same-panel max/min is ≤1.05 and every cross-panel median max/min is 1.00, within the 1.08 and 1.10 gates. The audit compares repeat instances of the same symbol/function (for example, `t` across all nine positions), not inherently different glyph outlines such as `+` versus `−`.

4. Role hierarchy and visual harmony — FAIL

The local mandatory base is ordinary node-label text (actual median 29px). Panel-label median is 38px, ratio **1.310**, exceeding the panel-label maximum 1.20. Ordinary annotation median is 34px, ratio **1.172**, exceeding the annotation maximum 1.10. See `role_ratio_audit.csv`. These direct H-ink ratios are not normalized away across scripts; under the strict protocol they fail. This also prevents a visual-harmony pass even though the three panels are structurally aligned.

5. Pixel overlap, bbox clearance, edges, panels, and clipping — PASS

`relation_clearance.csv` and `after_overlap_report.csv` contain every checked relation, including 820 TEXT–TEXT, 3,936 TEXT–GRAPHIC, 41 TEXT–IMAGE_EDGE, and 507 CROSS_PANEL_TEXT relations. The independent TEXT–TEXT bbox gate has minimum `BBOX_CLEARANCE_PX=17.000` (required ≥4); there are no intersecting text bboxes. The closest true text–graphic relation is `F_X_2` to `D021_NODE_BORDER`: bbox intersection is reported separately, actual mask-to-mask clearance is **14px** (required ≥5 for node-inner text), with zero overlap. Text-to-crop-edge minimum is **53px** (required ≥6); cross-panel bbox minimum is **147px** (required ≥8). All illegal overlap counts are zero and both PDF-page/crop clip checks are zero. The closest TEXT–TEXT and TEXT–GRAPHIC raw 1:1 ROIs, independent masks, overlap masks, coordinate overlays, and nearest points are saved as `relation_01_*` and `relation_02_*` artifacts.

## Non-visual checks

- Mathematics and text consistency pass. Forward highlights two transitions entering `q_2` at time `t`; backward highlights two transitions leaving `q_1`; Viterbi shows one winning path plus a backtrace arrow. This agrees with the caption and the immediate body explanation.
- Reading order passes: left-to-right panel headings, time labels, paths, common annotation, then the one-sentence caption are unambiguous.
- Grayscale passes: the faint transitions remain light/dashed and emphasized transitions remain solid/heavier; the panel headings carry the semantic distinction even without colour.
- Page integration passes visually in `after_full_page_200dpi.png`: graph, caption, follow-up paragraph, and example stay on the same page without a visible crop or collision.

## Required SA2 repair scope

Raise every general reader-facing source font in `fig_v3_c05_lattice.tex` to effective ≥9.5pt without global scaling: tick labels (line 17), state/observation labels (lines 8–9 and 18–20), and common annotation (lines 41–42). Restore the role hierarchy without reducing any effective font below 9.5pt, then rebuild the frozen candidate and repeat the complete source/pixel/ratio/overlap audit. Caption effective size must be auditable from the permitted source context before any later PASS.
