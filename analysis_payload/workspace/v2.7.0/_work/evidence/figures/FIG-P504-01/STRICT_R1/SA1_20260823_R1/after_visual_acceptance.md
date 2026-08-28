# FIG-P504-01 SA1 STRICT_R1 visual acceptance

RESULT: FAIL

Frozen PDF: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf
Figure source (read-only): D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C05\fig_v4_c05_two_geometries.tex
Adjacent text (read-only): D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第04册_无监督学习与矩阵分解\chapters\V4-C05.tex
Location: physical PDF page 550; printed page 537; 图 28.1.

SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.00
VISUAL_HARMONY_PASS = false
FONT_VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = false
TEXT_CONSISTENCY_PASS = true
READING_ORDER_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

Hard failures:
1. 11 of 14 semantic reader-visible objects are declared/effective 9.4pt or 9.2pt, below the 9.5pt floor.
2. 13 raw individual glyphs fail their specific 300dpi class floor; 78 glyph rows fail the combined source-plus-pixel gate; see after_pixel_measurements.csv.
3. R_TITLE and R_W2 have zero raw-ink intersection after independent masks, but their PDF/vector bboxes have 0.00px separation. This is a text-text bbox-clearance failure (required >=4px), not an overlap-pixel failure.
4. K=2 with the two displayed in-plane orthogonal bases u1,u2 makes U2 U2 transpose x the identity in the drawing, but the panel also draws a separate projected point and residual. This is a rank/dimension semantic error.

Mask method: text ink is isolated by direct frozen-PDF vector bboxes, while graphics are independently rasterized from PDF vector paths. The local-20/255 masks use no dilation; their intersections and all text-text masks are therefore not polluted by painter order. FONT_VISUAL_HARMONY_PASS is false: the undersized source text, pixel-floor failures, role-ratio failure and 0px bbox clearance mean no permissible font-size reduction/adjustment can be accepted in this candidate. No source, shared style, wrapper, inventory, or central status file was modified.

Four required views:
- after_full_page_200dpi.png
- after_full_page_300dpi.png
- after_figure_crop_300dpi.png
- after_standalone_300dpi.png
- after_grayscale_300dpi.png

NEXT_ROLE: SA2
