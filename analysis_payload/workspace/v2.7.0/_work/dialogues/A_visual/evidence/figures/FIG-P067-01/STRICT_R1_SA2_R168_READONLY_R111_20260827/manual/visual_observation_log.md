# FIG-P067-01 SA2 visual observation log

- Reviewer: `/root/p067_r111_r168_sa2`
- Observed at (UTC): `2026-08-27T05:54:13.7521987Z`
- Candidate: official R111 PDF, independently located by a unique live-caption hit on physical page 69.
- Views actually opened at native evidence paths: `full_page_200dpi.png`, `figure_body_native_crop_300dpi.png`, `figure_caption_native1x_300dpi.png`, `figure_caption_grayscale_300dpi.png`, `atomic_bbox_overlay_300dpi.png`, `figure_caption_nearest8x.png`, `critical_bottom_y_ticks_native1x_300dpi.png`, `critical_bottom_y_ticks_nearest8x.png`, all four `glyph_roi_sheet_*.png`, and all three `path_roi_sheet_*.png`.

Observed result: the discrete masses are 0.15, 0.30, 0.35, 0.20 and sum to 1; the cumulative levels are 0.15, 0.45, 0.80, 1.00; the staircase is monotone and the filled/open markers correctly encode the right-continuous post-jump/pre-jump values. The common abscissae align across panels, both annotations and the caption agree with the source/body context, grayscale retains the structural encoding, and no clipping or missing/tofu/wrong-codepoint glyph is visible.

One present hard defect is confirmed. In the lower PMF panel, the y-tick labels `0.35` and `0.3` visibly overprint. Their native 300 dpi word boxes are `(521,563,590,600)` and `(539,582,590,619)` pixels; the shared rectangle is 51 by 18 pixels and contains 327 foreground pixels. The nearest-neighbour 8x view preserves the same geometry as 58,752 shared-box pixels and 20,928 foreground pixels. The two numerical labels are not distinguishable as separate rows without effort, so this is an actual readability and illegal-overlap failure, not a taxonomy, source-size, or micropixel-only objection.

