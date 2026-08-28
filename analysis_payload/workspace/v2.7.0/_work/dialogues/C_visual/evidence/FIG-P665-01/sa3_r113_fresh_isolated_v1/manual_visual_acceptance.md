# FIG-P665-01 independent SA3 visual acceptance

`SA3_MODEL = gpt-5.6-sol`

`SA3_REASONING = xhigh`

`HANDOFF_ID = C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1`

`SOURCE_FONT_PASS = true` — R168 applied. The 9.2 pt general source setting and 8.5 pt brace note are recorded as numeric advisories, but final native pixels show no unreadability, severe imbalance, missing glyph, or other hard defect.

`PIXEL_HEIGHT_PASS = true` — measured ink heights are 28–56 px for ordinary single-line elements and 87 px for the stacked derivative; all opened native1x/nearest8x views remain clear. Formula scripts are visibly distinct and not lost.

`SAME_CLASS_RATIO_PASS = true` — comparisons use matching role and script class. The two main formula rows are both 48 px; Chinese box headers are both 31 px; box formulas are 35/37/38 px around median 37; caption lines are 46/54 px around median 50, exactly within the inclusive 0.92–1.08 band.

`ROLE_RATIO_PASS = true` — both panel titles measure 37 px, main inline/result/warning formula bodies are visually aligned around 38 px (larger union heights only where legitimate scripts or fraction stacking add vertical extent), and no ordinary label dominates the mathematical structure.

`OVERLAP_CANDIDATE_PIXEL_COUNT = 0`

`MASK_CONTAMINATION_PIXEL_COUNT = 0`

`OVERLAP_PIXEL_COUNT = 0`

`PIXEL_ADJUDICATION_STATUS = CLEAR`

`PIXEL_ARBITER_MODEL = NOT_USED`

`PIXEL_ARBITER_REASONING = NOT_USED`

`CLIP_PIXEL_COUNT = 0`

`MIN_TEXT_CLEARANCE_PX = 7`

`VISUAL_HARMONY_PASS = true` — two panels are balanced; the left decomposition and right derivation have comparable weight; blue result and red warning roles are distinct without overwhelming the formulas.

`MATH_SEMANTICS_PASS = true` — independent derivation is in `manual_math_semantics_recompute.md`.

`TEXT_CONSISTENCY_PASS = true` — figure, caption, and necessary current V5-C05 prose agree on the sufficient statistic, log-partition derivative, and noncommutation warning.

`GRAYSCALE_PASS = true` — opened native grayscale preserves titles, borders, arrow, warning, and both mathematical paths; meaning is not color-only.

`PAGE_INTEGRATION_PASS = true` — the full physical page 713 was opened at native 300 dpi; figure/caption width, surrounding equation, theorem, whitespace, header, and footer integrate without clipping, overlap, orphaning, or severe imbalance.

`READING_ORDER_PASS = true` — left decomposition, right derivative chain, then caption forms a stable path; `reading_order_overlay_300dpi.png` records it.

`CODEPOINT_PASS = true` — zero actual tofu, missing glyph, or wrong-codepoint defect after machine extraction and manual nearest8x inspection.

`UNRESOLVED_COUNT = 0`

`VERDICT = SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`
