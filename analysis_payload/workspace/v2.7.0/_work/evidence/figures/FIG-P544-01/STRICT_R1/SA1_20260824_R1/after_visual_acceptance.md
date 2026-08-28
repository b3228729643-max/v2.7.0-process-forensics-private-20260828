# FIG-P544-01 SA1 STRICT_R1 visual acceptance

RESULT: FAIL

Frozen PDF: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf
Figure source (read-only): D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_dependency_graph.tex
Adjacent text (read-only): D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C01.tex
Location: physical PDF page 588; printed page 575; 图 30.1.

SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 6
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.00
VISUAL_HARMONY_PASS = false
FONT_VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = false
TEXT_CONSISTENCY_PASS = false
READING_ORDER_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

Hard failures:
1. 3 of 11 semantic reader-visible elements use the explicit 8.8pt legend/edge style, below the 9.5pt floor. The ordinary 9.4pt picture default is overridden by the global every-node small style, yielding 10.0pt effective node text.
2. 8 individual raw glyphs fail their own 300dpi pixel floor; 30 glyph rows fail the combined source-plus-pixel gate.
3. LEGEND_DASHED and its dashed-arrow/arrowhead mask have exactly 6 illegal raw 300dpi intersection pixels and 0.00px clearance; see the critical-pair raw ROI, both masks, intersection mask and overlay.
4. The fixed-point node prints π=πP, but V5-C01's stated row-vector convention is ρ★=ρ★A; P=Aᵀ is only the column-vector convention and requires p★=Pp★. The diagram mixes orientation and variable conventions.
5. The structural node says ‘返性’ instead of the chapter's ‘正常返’, and the merged long-run node obscures that nonperiodicity is needed for stepwise convergence but not for the time-average theorem.

Mask method: direct frozen-PDF raw foreground uses local background delta >=20/255 with no dilation. Text comes from vector character bboxes; node borders and arrows are independently rasterized from frozen-PDF vector paths, excluding fills. All pair intersection conclusions are therefore free of bbox dilation and paint-order contamination.
FONT_VISUAL_HARMONY_PASS is false: a permissible font adjustment/reduction requires every source-size, glyph-pixel, ratio, clearance and full-page gate to stay true; this candidate does not meet those conditions.
Single-panel applicability: cross-panel and panel-border pair checks are explicitly not applicable; line/arrow, text-text, node-border, edge and clip checks are recorded in the CSV evidence.

Required native views:
- full_page_200dpi.png
- full_page_300dpi.png
- figure_crop_300dpi.png
- standalone_300dpi.png
- grayscale_300dpi.png

NEXT_ROLE: SA2
