# FIG-P467-01 — STRICT_R1 SA1 visual acceptance

- Frozen candidate: `main_full.pdf`, physical PDF page **509**, printed page **496**, **图26.1**.
- All 300 dpi measurements use the direct, unresized `pdftoppm` raster from the frozen candidate. The standalone view is a non-resampled crop of that same final PDF.
- Reader-visible glyphs measured: **76**; independent text objects: **7**; independent PDF vector objects: **54**.

## Required matrix

- SOURCE_FONT_PASS = false (failed glyphs: 47)
- PIXEL_HEIGHT_PASS = false (failed glyphs: 3)
- SAME_CLASS_RATIO_PASS = true
- ROLE_RATIO_PASS = true
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 20.000 (text-text bbox 20.000; text-graphic foreground 54.197)
- VISUAL_HARMONY_PASS = false
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

## Strict result

RESULT: FAIL

### Deterministic hard failures

- TikZ default reader text is `9.2pt` (source line 3), panel-title text is `9.4pt` (line 19), and the annotation is `9.0pt` (line 48). Each is below the required 9.5pt effective size; the title superscript is naturally derived from the already-invalid 9.4pt base.
- Per-glyph 300 dpi measurements and independent punctuation/math sub-strings are in `after_pixel_measurements.csv`; no parent formula/line bbox is used as a substitute.

### Non-font findings

- All TEXT–TEXT and TEXT–GRAPHIC pair records are in `after_overlap_report.csv`; independent geometry/data contacts are preserved separately in `intentional_geometry_intersections.csv` and excluded from text-collision counts.
- The visual semantic sequence is left-to-right: unit circle → V^T orthogonal rotation → Σ axial scaling → U orthogonal rotation. Source coordinates preserve these transformations and match adjacent text/caption.
- Full-page 200 dpi, full-page native 300 dpi, standalone native 300 dpi, and grayscale native 300 dpi were inspected. The line/arrow structure remains distinguishable in grayscale, and the page integration is stable; neither can override font hard failures.

## Required next role

SA2. Increase all reader-facing figure text to a true effective >=9.5pt (including title base and annotation), preserve natural script derivation from a compliant base, recompile a new official candidate, and regenerate this entire evidence set before a new SA1 review. Do not use global scaling as a workaround.
