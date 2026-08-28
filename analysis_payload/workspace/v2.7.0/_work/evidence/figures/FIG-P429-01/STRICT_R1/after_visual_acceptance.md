# FIG-P429-01 — STRICT_R1 visual acceptance

Candidate independently located at **physical PDF page 466**; printed page **453**.

Native rendering evidence: `full_page_200dpi.png`, `figure_crop_300dpi.png`, `grayscale_300dpi.png`, `text_measurement_overlay_300dpi.png`, and raw `page_466_raw_300dpi.png`. No view was resized or screenshot-derived.

`standalone_300dpi.png` is absent by design: see `standalone_300dpi_UNAVAILABLE.md`. It is a hard missing-evidence condition.

Geometry disposition: exactly eight applicable text-to-line/arrow pairs fail.  Each has native 1:1 `raw_roi`, independent `text_mask` and `vector_mask`, `separated_masks`, `overlay`, and `overlap_mask` evidence in `after_overlap_report.csv`.  Verdicts require both draw-order-independent PDF glyph/vector intersection and final native-raw foreground; no dilation or broad bbox was used.  External annotation-to-neighbouring-node-border pairs are `N/A`, not failures; the 5px rule is applied only to text inside its own node.  `after_edge_clip_report.csv` inventories all 68 text/vector objects and reports zero page/crop clipping.

SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = true
OVERLAP_PIXEL_COUNT = 466
CLIP_PIXEL_COUNT = 0
MIN_TEXT_TEXT_CLEARANCE_PX = 8.00
MIN_TEXT_GRAPHIC_CLEARANCE_PX = 0.00
MIN_TEXT_NODE_BORDER_CLEARANCE_PX = 12.25
MIN_TEXT_LINE_ARROW_CLEARANCE_PX = 0.00
MIN_TEXT_MARKER_CLEARANCE_PX = 15.57
MIN_TEXT_PAGE_EDGE_CLEARANCE_PX = 258.00
MIN_TEXT_CROP_EDGE_CLEARANCE_PX = 27.00
MIN_CROSS_PANEL_TEXT_CLEARANCE_PX = 212.00
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## Measured role hierarchy

- PANEL_LABEL: 1.1935 (required [1.05, 1.20])
- ANNOTATION: 1.0000 (required [0.95, 1.10])
- NODE_LABEL: 1.0968 (required [0.95, 1.10])
- EVIDENCE_NOTE: 1.0323 (required [0.95, 1.10])

Axis, tick, legend, and formula-block roles are absent in this figure. Inline variables (`X`, `z`, `x`) and the relation arrow are individually measured instead.

## Result

RESULT = FAIL

Blocking conditions: visible source fonts of 9.0pt, 9.2pt, and 9.4pt are below 9.5pt; any measured pixel-floor failure is listed in `after_pixel_measurements.csv`; and the independent standalone 300-dpi evidence is unavailable under this read-only task.
