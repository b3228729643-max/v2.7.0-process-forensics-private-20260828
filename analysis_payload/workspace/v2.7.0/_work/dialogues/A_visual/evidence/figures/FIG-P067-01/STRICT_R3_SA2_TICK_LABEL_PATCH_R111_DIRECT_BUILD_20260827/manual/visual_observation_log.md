# Visual observation log

Observer `/root` actually opened the following final R3 artifacts before writing the ledgers at `2026-08-27T06:50:08.2201269Z`:

- `standalone_300dpi.png`
- `figure_native1x_300dpi.png`
- `figure_grayscale_300dpi.png`
- `atomic_bbox_overlay_300dpi.png`
- `critical_y_ticks_native1x_300dpi.png`
- `critical_y_ticks_nearest8x.png`
- all three `glyph_roi_sheet_*` images
- all three `path_roi_sheet_*` images

Observed result: the three adjacent lower y labels read top-to-bottom as `0.35`, `0.3`, `0.15`, with visible white separation. The former overprint is absent. The 1px rounded bbox gaps are R168-advisory, not hard failures, because foreground intersection is zero and both native and 8x views are plainly readable. All PMF/CDF semantics, markers, endpoints, guides, notes, axes, grayscale encoding, and page integration pass.

