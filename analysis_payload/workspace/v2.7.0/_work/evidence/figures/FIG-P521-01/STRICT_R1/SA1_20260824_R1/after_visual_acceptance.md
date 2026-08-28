# FIG-P521-01 — SA1 Strict R1 acceptance

- SOURCE_FONT_PASS = false
- PIXEL_HEIGHT_PASS = false
- SAME_CLASS_RATIO_PASS = false
- ROLE_RATIO_PASS = false
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 9.0
- VISUAL_HARMONY_PASS = false
- FONT_VISUAL_HARMONY_PASS = false
- MATH_SEMANTICS_PASS = false
- TEXT_CONSISTENCY_PASS = false
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

RESULT: FAIL

Why: source effective font hard minimum fails; individual raw glyph/operator checks are recorded in CSV; the 8.8pt legend/plate role is below the role floor; and the plate/model semantics conflict with the adjacent PLSA description.