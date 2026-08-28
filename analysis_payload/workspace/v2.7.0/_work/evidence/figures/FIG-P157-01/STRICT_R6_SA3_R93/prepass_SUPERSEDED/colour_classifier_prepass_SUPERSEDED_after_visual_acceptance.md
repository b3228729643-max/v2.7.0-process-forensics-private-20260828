# FIG-P157-01 — SA3 strict R6 / R93 visual acceptance

- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`
- Independently located PDF physical page: **170**; printed page: **157**; caption and figure number: **图 10.1**.
- Render method: final PDF → PyMuPDF native `300 dpi` PNG; no spatial resize. Full-page view is `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R6_SA3_R93\after_full_page_200dpi.png`. The 300 dpi crop/standalone/grayscale views are co-located in this directory.
- Text masks: native `rawdict` span/character boxes, no bbox padding; pixels must be on the local background→PDF-font-color blend line and differ from local background by at least 20/255. Vector masks: native `get_drawings()` geometry, z-order occlusion of later opaque fills, color-blend test, and individual mask output. Crop-only presentation pad is fixed at 2 px and never used for any mask/metric.

| Gate | Result | Measured basis |
|---|---:|---|
| SOURCE_FONT_PASS | `true` | Figure source plus current shared `figure-style-v2.3.0.tex` and `statlearnbook.sty` restore every declared font and cumulative scale. |
| PIXEL_HEIGHT_PASS | `true` | all measured visible CJK and digit spans meet their respective 30 px / 24 px minima; see `after_pixel_measurements.csv`. |
| SAME_CLASS_RATIO_PASS | `true` | one panel; per-role, same-script ratios in `after_pixel_measurements.csv`. |
| ROLE_RATIO_PASS | `true` | base is REGION_LABEL/CJK (no tick or node-body role exists); axis/direct/key roles checked by table. |
| OVERLAP_PIXEL_COUNT | `72` | all non-exempt independent mask pairs; intentional curve-leader/selection/axis construction contacts separately labelled. |
| CLIP_PIXEL_COUNT | `0` | actual final PDF media-box boundary check in `after_edge_clip_report.csv`. |
| MIN_TEXT_CLEARANCE_PX | `14.000` | native-mask nearest-pixel measurement; pair coordinates and raw/overlay/mask evidence in `after_overlap_report.csv`. |
| VISUAL_HARMONY_PASS | `true` | full page, figure crop, standalone and grayscale views checked; curves retain primary weight and text is not the first focal layer. |
| MATH_SEMANTICS_PASS | `true` | train derivative is negative; validation quadratic minimum `(5.25,1.08)`; leader source coordinate evaluates to `0.654629`. |
| TEXT_CONSISTENCY_PASS | `true` | caption, all direct labels, selection label, and adjacent reading instruction agree. |
| GRAYSCALE_PASS | `true` | solid training line, dashed validation line, vertical reference and filled marker remain distinguishable. |
| PAGE_INTEGRATION_PASS | `true` | figure, caption, explanatory paragraph, and following example remain separated and readable on the final page. |

## Result

`RESULT: FAIL`

The result above follows the complete final audit. The prior incomplete prepass was preserved under `prepass_SUPERSEDED/` and is not a result for this candidate.

## Directed repair / rerun action

No source-font repair is required if every gate above is true. If a future candidate changes shared figure/caption styles, rerun this complete audit from the newly frozen PDF.
