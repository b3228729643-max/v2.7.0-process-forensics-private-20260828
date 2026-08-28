# P126 R19 static text/curve collision patch

HANDOFF_ID=A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-20260828

STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS

## Scope and identity

The only modified source is `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`. The authorized 4,686-byte source with SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405` became 4,809 bytes with SHA-256 `4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2`.

The exact Git boundary is one modified file, 2 additions, 2 deletions, empty index, and `git diff --check` PASS. In-memory replacement of the two new node option lists with their authorized predecessors reconstructs exactly 4,686 bytes and the authorized before SHA-256.

## Exact source changes

1. The existing `x^{(0)}` node retains its text, font, anchor, and q0 coordinate. It gains `xshift=4pt` plus a local opaque white background with `inner sep=.8pt`.
2. The existing digit 5 node retains its text, font, anchor, and q5 coordinate. Its x shift changes from -2pt to -6pt and it gains the same local opaque white background.

No contour, path, marker, arrow, coordinate, axis, legend, font declaration, caption, alt text, shared macro, chapter source, or build entry changed.

## Static geometry projection

The projection uses only the previously accepted decisive native-300-dpi ROIs as immutable pixels and translates the target masks by the exact point deltas. The four final projection views were opened after generation: native1x and nearest-neighbor 8x for each target. Yellow fill and orange outlines in those diagnostic PNGs are projection annotations only; the source requests a white borderless background.

For `x^{(0)}`, 4pt maps to 17 pixels at 300 dpi. The projected background is `[33,29,103,73]` in the 115 by 105 ROI. It has zero overlap with the protected q0-marker/vertical-update region and a 17-pixel gap to that region. Target ink has a 5-pixel minimum gap to remaining visible obstacles. The local background covers only neutral gray contour/antialias pixels at the crossing; the contour remains visible on both sides.

For digit 5, the -4pt delta maps to -17 pixels. The projected background is `[41,56,63,87]` in the 100 by 105 ROI. Its overlap with each protected region is zero. Projected gaps are 23.02 pixels to the incoming vertical update, 20 pixels to the outgoing horizontal update, 24 pixels to the q5 marker, 11 pixels to the x axis, and 15 pixels to the label-7 region. Target ink has a 5-pixel minimum gap to remaining visible obstacles. The shift moves the label away from the q5 marker and labels 6/7; labels 1/3/4 and their markers remain farther in coordinate and pixel space than the enumerated nearest protected regions.

Both local backgrounds are confined to their target labels. They do not cover dark text, axes, arrows, or markers, and the hidden pixels are limited to the gray contour under the label; the contour enters and exits continuously at the background edges.

## Boundary and request

This is a static projection, not rendered evidence and not a PASS. TeX/build, commit, fresh role, second UID, central-state write, and process management counts are all zero. A single controlled standalone/direct LuaLaTeX build slot is requested only after Main independently accepts this sealed static package.
