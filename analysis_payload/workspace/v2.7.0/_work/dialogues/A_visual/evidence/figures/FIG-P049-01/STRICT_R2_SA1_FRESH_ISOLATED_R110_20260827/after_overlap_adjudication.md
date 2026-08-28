# FIG-P049-01 overlap adjudication

- Observation completed: `2026-08-27T06:00:58+08:00`
- Native evidence actually opened: `02_graphic_native_300dpi.png`, `05_graphic_grayscale_native_300dpi.png`, `rois/09_gradient_tangent_right_angle_roi_native_8x.png`, `rois/10_guide_lines_and_notes_roi_native_8x.png`, `rois/11_contours_labels_formula_roi_native_8x.png`, and `rois/13_c2_overlap_roi_native_8x.png`.
- Candidate cluster: `PAIR-0115`, `G_CONTOUR_C3` versus `T_CONTOUR_C2`, 10 pixels at associated-crop coordinates `(270..277, 307..314)`.
- Native pixel evidence: all 10 candidate pixels are pale blue contour antialias samples. Their RGB values range from `(128,154,179)` to `(220,227,234)`. Residual to the blue contour color ray is `0.163..0.790`, while residual to the dark text color ray is `7.660..27.972`.
- Source/vector evidence: the candidate coordinates lie inside the PDF span rectangle for the `c_2` base glyph, but on the nearby outer blue contour. The automatic text mask used the whole span rectangle and accepted those colored contour antialias pixels; this is not shared visible ink.
- 8× visual evidence: `rois/13_c2_overlap_roi_native_8x.png` shows a clean white gap between the blue outer contour and the dark `c_2` glyph. The grey `c_2` contour is also separate.
- Corrected direct-300-dpi base-glyph measurement: after separating pixels by the final PDF text and contour color rays, the `c` ink height is 20 px; the derived subscript `2` is 19 px. Both meet their script-class thresholds (17 px and 15 px).

Adjudication:

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 10`
- `MASK_CONTAMINATION_PIXEL_COUNT = 10`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`
- No unresolved pixel cluster remains.

Separate non-pixel semantic finding: guide lines 1 and 2 truly intersect as vector paths. That is recorded as a guide-routing semantic failure, not as a text/graphic illegal-pixel collision.
