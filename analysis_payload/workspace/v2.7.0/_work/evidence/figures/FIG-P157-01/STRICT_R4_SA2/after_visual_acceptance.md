# FIG-P157-01 — SA2 strict R4 local-candidate visual acceptance

RESULT: PASS

## Local candidate and method

- Standalone object: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R4_SA2\build\standalone_wrapper.pdf`; 1 A4 page; 38442 bytes. Local context page: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R4_SA2\build\page_wrapper.pdf`.
- Source audit inputs: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex` plus unchanged `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C10.tex` for semantic/text consistency only.
- Render evidence is direct `pdftoppm` output at native 300 dpi (`2481×3508`) and 200 dpi, with no post-render resize/resampling.
- A single coordinate panel (`P01`) contains three semantic background regions, not multiple panels. Cross-panel typography and inter-panel clearance are therefore N/A rather than unmeasured.
- `H_INK_PX` is the median of the relevant native vector character glyph heights after applying the required >=20/255 local-contrast foreground test. The complete bboxes, glyph-height samples and pair matrix are in the CSV evidence.
- The only source delta is T04 `选择复杂度`: `(axis cs:5.25,-.02)` → `(axis cs:5.25,-.07)`; anchor, text, style, font, scale, curves, points, axes and every other label are unchanged.

## Strict matrix

| gate | result | evidence |
| --- | --- | --- |
| SOURCE_FONT_PASS | true | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | true | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | true | all same-role/script values in `[0.92,1.08]` |
| ROLE_RATIO_PASS | true | REGION_LABEL CJK base = 37.00px; role bounds recorded per element |
| OVERLAP_PIXEL_COUNT | 0 | `after_overlap_report.csv`, full TEXT–TEXT/TEXT–GRAPHIC matrix |
| CLIP_PIXEL_COUNT | 0 | native semantic-object foreground at the A4 outer border |
| MIN_TEXT_CLEARANCE_PX | 13.04 | text-text min 14.00px; text-graphic min 13.04px; figure-edge min 28.00px |
| T04_G06_TARGET_CLEARANCE_PX | 19.0000 | independent T04/G06 masks; target >=8px; hard gate >=3px |
| VISUAL_HARMONY_PASS | true | full 200dpi, 300dpi crop and grayscale review |
| MATH_SEMANTICS_PASS | true | curve equations and extrema vs labels/caption/body |
| TEXT_CONSISTENCY_PASS | true | caption and V1-C10.tex:259 checked item-by-item |
| GRAYSCALE_PASS | true | solid blue training curve / dashed teal validation curve / filled marker + vertical reference remain distinct in grayscale |
| PAGE_INTEGRATION_PASS | true | local 200dpi full page: context, figure, caption and following paragraph remain cleanly sequenced |

## Hard-failure check

No hard failures.

## T02 mandatory remeasurement — `验证误差：先降后升`

T02 native text bbox: `[267.665,170.027,360.054,181.022]` pt; mapped 300dpi bbox: `[1115,708,1501,755]`. Its source is `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex:47-48`; native text foreground is retained in `masks/semantic_text_foreground_mask_300dpi.png`, and the 1:1 evidence is `roi/T02_validation_annotation_1to1_300dpi.png`.

| T02 counterpart | counterpart native bbox (pt) | foreground overlap px | min foreground clearance px | nearest text → graphic pixel (300dpi) | result |
| --- | --- | ---: | ---: | --- | --- |
| G01_TRAINING_CURVE | [97.414,99.876,530.814,259.557] | 0 | 163.12 | [1124, 745] → [1073, 901] | PASS |
| G02_VALIDATION_CURVE | [97.414,86.855,530.814,229.565] | 0 | 163.12 | [1124, 745] → [1073, 901] | PASS |
| G03_REFERENCE_LINE | [324.949,229.565,324.949,282.822] | 0 | 225.97 | not retained (not a focused curve pair) | PASS |
| G04_GOLD_MARKER | [321.950,226.566,327.948,232.565] | 0 | 196.73 | not retained (not a focused curve pair) | PASS |
| G05_TRAINING_LEADER | [407.295,238.442,415.963,250.523] | 0 | 348.31 | not retained (not a focused curve pair) | PASS |
| G06_X_AXIS_ARROW | [97.414,280.876,530.815,284.768] | 0 | 422.52 | not retained (not a focused curve pair) | PASS |
| G07_Y_AXIS_ARROW | [95.468,68.318,99.360,282.822] | 0 | 709.00 | not retained (not a focused curve pair) | PASS |

`G01` and `G02` are separately derived source-colour foreground masks, never a shared graphics bbox. Their masks and 1:1 nearest-pixel overlays are `masks/G01_training_curve_foreground_mask_300dpi.png`, `masks/G02_validation_curve_foreground_mask_300dpi.png`, `roi/T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png`, and `roi/T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png`. The curve bboxes are recorded only for traceability; pass/fail uses the mandated semantic foreground-pixel intersection and nearest foreground clearance.

## Text/curve/selection consistency

- Source curve at lines 33–34 is solid blue and is monotonically decreasing: it agrees with `训练误差：单调下降`, the caption, and V1-C10.tex:259.
- Source curve at lines 35–37 is dashed teal with a U-shaped formula minimized at x=5.25: it agrees with `验证误差：先降后升`, the caption, and V1-C10.tex:259.
- Lines 38–41 place a gray dashed vertical reference and gold filled point at `(5.25,1.08)`. Lines 49–52 label the point as minimum validation error and the x-coordinate as selected complexity. V1-C10.tex:259 explicitly states that the solid line is training error, dashed line is validation error, and the gold point plus vertical reference jointly mark the selected complexity. All four descriptions agree.
- Caption line 61 contains exactly one reader conclusion: training error generally decreases as model complexity increases whereas validation error may first decrease then rise. The procedural detail remains in the following prose, not the caption.

## Visual / layout decision

Reading order is y-axis / x-axis context → two curves → gold minimum + vertical selection → underfit/appropriate/overfit labels → caption. Solid/dashed/marker/reference distinctions survive grayscale, the label plates preserve the curve reading path, and no label obscures a data point, extremum or arrowhead. Local full-page review shows a stable fit: the caption has clear separation from surrounding prose, with no orphaning, clip, collision or abnormal whitespace.

## Required artifacts

- `standalone_300dpi.png`, `local_page_300dpi.png`, `full_page_200dpi.png`
- `figure_crop_300dpi.png`, `grayscale_300dpi.png`
- `roi/*.png` (native 1:1 critical ROIs)
- `masks/semantic_text_foreground_mask_300dpi.png`, `masks/semantic_graphics_mask_300dpi.png`
- `masks/G01_training_curve_foreground_mask_300dpi.png`, `masks/G02_validation_curve_foreground_mask_300dpi.png`, `masks/T04_selection_key_text_mask_300dpi.png`, `masks/G06_x_axis_arrow_foreground_mask_300dpi.png`
- `roi/T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png`, `roi/T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png`, `roi/T04_to_G06_x_axis_nearest_segment_1to1_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_text_measurement_overlay_300dpi.png`

