# FIG-P600-01 — SA1 R101 fresh acceptance matrix

- SA1_MODEL = gpt-5.6-sol
- SA1_REASONING = xhigh
- SA2_MODEL = NOT_USED
- SA2_REASONING = NOT_USED
- SA2_ESCALATED = false
- SA3_MODEL = NOT_USED
- SA3_REASONING = NOT_USED
- SOURCE_FONT_PASS = true (R168; 8.6/9.2pt metadata advisory only, all 133 glyphs actually readable)
- PIXEL_HEIGHT_PASS = true (R168; reader-visible elements and all glyph cards show no actual unreadability)
- SAME_CLASS_RATIO_PASS = true (R168 visual judgment; x/y ink-height difference is glyph anatomy, not scaling)
- ROLE_RATIO_PASS = true (R168 visual judgment; heading is intentionally auxiliary and not obviously imbalanced)
- OVERLAP_CANDIDATE_PIXEL_COUNT = 10
- MASK_CONTAMINATION_PIXEL_COUNT = 10
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED
- PIXEL_ARBITER_MODEL = NOT_USED
- PIXEL_ARBITER_REASONING = NOT_USED
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 4.79 (O21/O22 text-bbox gap; text–line minimum 30.96px; contained text–border minimum 7.54px)
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = false (S07)
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

RESULT = **FAIL**. The hard blocker is not font metadata or a raster micro-difference. Current adjacent chapter text says Figure 32.4 draws “paired flows and the rejection self-loop separately,” while the closed 22-object inventory contains no rejection self-loop. Figure source, figure caption, formula semantics, geometry, overlap, clipping, grayscale, and page layout otherwise pass this fresh SA1.

Repair authority needed: a chapter-text/source single writer, not the figure-source writer. After that writer corrects the sentence (or deliberately changes the figure/caption as a coordinated semantic redesign), a future globally granted TeX slot and a new frozen official candidate are required before fresh re-review.
