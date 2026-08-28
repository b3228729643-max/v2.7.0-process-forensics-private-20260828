# FIG-P049-01 manual visual ledger

Manual observation was completed at `2026-08-27T06:00:58+08:00`, only after opening the final contact sheet and the native final views/ROIs listed below.

## Opened evidence

- `12_final_review_contact_sheet.png`
- `02_graphic_native_300dpi.png`
- `05_graphic_grayscale_native_300dpi.png`
- `rois/09_gradient_tangent_right_angle_roi_native_8x.png`
- `rois/10_guide_lines_and_notes_roi_native_8x.png`
- `rois/11_contours_labels_formula_roi_native_8x.png`
- `rois/13_c2_overlap_roi_native_8x.png`

## Manual observations

- Glyphs and codepoints: all axis labels, contour labels, point/vector labels, Chinese notes, formulas, caption, subscripts, superscript transpose, and the gradient symbol are present and visually correct. No tofu, replacement glyph, missing glyph, or wrong codepoint is visible.
- Readability and balance: the figure and caption are readable at native 300 dpi and remain distinguishable in grayscale. The 9.2/9.4 pt source values and minor raster-height differences are advisory under R168; they do not create unreadability or obvious type-size imbalance here.
- Clipping: no text, curve, axis arrowhead, vector arrowhead, marker, caption, or formula is clipped. `CLIP_PIXEL_COUNT=0`.
- Text/graphic collision: the only automatic candidate is the 10-pixel `c_2` color-mask contamination adjudicated in `after_overlap_adjudication.md`; true illegal overlap is zero. After excluding that false cluster, the minimum measured text-related foreground clearance is `7.991 px` (`G_GUIDE_2` to `T_NOTE_2`), above the applicable 3 px threshold.
- Core geometry: three ordered concentric ellipses, point P on the outer contour, the gradient arrow, tangent line, and right-angle marker are all visually present. The gradient/tangent construction is legible and the marker is not clipped.
- Page integration: the graphic, caption, and following paragraph form a stable page block with no abnormal blank region, collision, or orphaned caption.
- Hard visual/semantic failure: the leader for note 1 does not terminate at `P` or its outer contour, and the leaders for notes 1 and 2 cross each other before reaching their targets. The crossing makes the first two callouts ambiguous and sends note 1 toward the gradient-callout region. This is a real guide-routing/semantic error under R168, not a font or antialias advisory.

Manual result: `FAIL`.
