# FIG-P660-01 SA2 R168 visual acceptance

```text
HANDOFF_ID = C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1
FIGURE_ID = FIG-P660-01
PDF_PHYSICAL_PAGE_1_BASED = 709
PRINTED_PAGE_NUMBER = 696
FIGURE_NUMBER = 34.4

SA1_MODEL = NOT_RUN_BY_THIS_ROLE
SA1_REASONING = NOT_RUN_BY_THIS_ROLE
SA2_MODEL = gpt-5.6-sol
SA2_REASONING = xhigh
SA2_ESCALATED = false
SA3_MODEL = NOT_RUN_BY_THIS_ROLE
SA3_REASONING = NOT_RUN_BY_THIS_ROLE

SOURCE_FONT_PASS = true
PIXEL_HEIGHT_PASS = true
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = true
OVERLAP_CANDIDATE_PIXEL_COUNT = 458
MASK_CONTAMINATION_PIXEL_COUNT = 458
OVERLAP_PIXEL_COUNT = 0
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED
PIXEL_ARBITER_MODEL = NOT_USED
PIXEL_ARBITER_REASONING = NOT_USED
UNRESOLVED_CANDIDATE_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.923 vector-bbox minimum between the nearest adjacent vertex-line spans; native glyph ink is visibly separated
VISUAL_HARMONY_PASS = true
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
ALT_CAPTION_SEMANTICS_PASS = true
GLYPH_CODEPOINT_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
READABILITY_HARD_DEFECT = false
VISIBLE_IMBALANCE_HARD_DEFECT = false

R168_POLICY_APPLIED = true
SOURCE_CHANGE_REQUIRED = false
RESULT = NO_GENUINE_HARD_DEFECT
DISPOSITION = SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1
```

Basis: all manual booleans above were set only after opening the full-page/integration views, native crop, grayscale, overlays, masks, pair matrix, and both native1x and nearest8x evidence for R01–R11. The 8.7 pt/9.2 pt declarations, the approximately 0.923 px nearest adjacent vector-bbox gap, and small ink-height ratio differences are advisory under R168. Native evidence shows no missing glyph/tofu, wrong codepoint, wrong mathematics, unreadability, visible imbalance, true clipping, illegal overlap, or semantic/geometric error.
