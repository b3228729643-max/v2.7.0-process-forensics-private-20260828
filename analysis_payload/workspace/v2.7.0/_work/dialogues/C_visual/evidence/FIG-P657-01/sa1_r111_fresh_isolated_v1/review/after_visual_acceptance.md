# FIG-P657-01 fresh isolated SA1 visual acceptance

SA1_MODEL = gpt-5.6-sol  
SA1_REASONING = xhigh  
SA1_INSTANCE = sa1_fig_p657_r111_fresh_isolated_v1  
HANDOFF_ID = C-FIG-P657-01-R111-SA1-FRESH-ISOLATED-V1  
SA2_MODEL = NOT_RUN_BY_SA1  
SA2_REASONING = NOT_RUN_BY_SA1  
SA2_ESCALATED = false  
SA3_MODEL = NOT_RUN_BY_SA1  
SA3_REASONING = NOT_RUN_BY_SA1  

SOURCE_FONT_PASS = true  
PIXEL_HEIGHT_PASS = true  
SAME_CLASS_RATIO_PASS = true  
ROLE_RATIO_PASS = true  
OVERLAP_CANDIDATE_PIXEL_COUNT = 0  
MASK_CONTAMINATION_PIXEL_COUNT = 0  
OVERLAP_PIXEL_COUNT = 0  
PIXEL_ADJUDICATION_STATUS = CLEAR  
PIXEL_ARBITER_MODEL = NOT_USED  
PIXEL_ARBITER_REASONING = NOT_USED  
CLIP_PIXEL_COUNT = 0  
MIN_TEXT_CLEARANCE_PX = 7  
MIN_TEXT_GRAPHIC_CLEARANCE_PX = 15  
MIN_NODE_TEXT_BORDER_CLEARANCE_PX = 12  
VISUAL_HARMONY_PASS = true  
MATH_SEMANTICS_PASS = true  
TEXT_CONSISTENCY_PASS = true  
GLYPH_CODEPOINT_PASS = true  
GRAYSCALE_PASS = true  
PAGE_INTEGRATION_PASS = true  

## Manual conclusion

`RESULT: PASS`

All six distribution nodes, five special-case arrows, two conjugacy arrows, two legend samples, three row headings, and two caption objects are present and correct. The complete 20-object denominator yields 190 manually decided unordered pairs: 175 clear separations, 14 legal node–relation attachments, and one bbox-only caption false positive with disjoint native ink. No real collision, clipping, tofu, wrong codepoint, unreadability, severe size imbalance, semantic error, or geometry ambiguity was found. The 8.8/9.2/9.4 pt source declarations were treated as advisory exactly as required by R168; native visual evidence is readable and coherent.

SA1 disposition: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

