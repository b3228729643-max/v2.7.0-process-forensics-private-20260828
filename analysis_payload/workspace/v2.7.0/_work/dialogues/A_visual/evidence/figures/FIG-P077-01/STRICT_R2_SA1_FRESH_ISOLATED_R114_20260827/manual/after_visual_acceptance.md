# Fresh isolated SA1 visual acceptance

- `RESULT = PASS`
- `FIGURE_ID = FIG-P077-01`
- `HANDOFF_ID = A-R114-P077-SA1-FRESH-ISOLATED-20260827`
- `SA1_MODEL = gpt-5.6-sol`
- `SA1_REASONING = xhigh`
- `SOURCE_FONT_PASS = true` under R168 current-PDF hard criteria
- `PIXEL_HEIGHT_PASS = true` under R168 current-PDF hard criteria
- `SAME_CLASS_RATIO_PASS = true` under R168 current-PDF hard criteria
- `ROLE_RATIO_PASS = true` under R168 current-PDF hard criteria
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 2`
- `MASK_CONTAMINATION_PIXEL_COUNT = 2`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`
- `PIXEL_ARBITER_MODEL = NOT_USED`
- `PIXEL_ARBITER_REASONING = NOT_USED`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 8`
- `VISUAL_HARMONY_PASS = true`
- `MATH_SEMANTICS_PASS = true`
- `TEXT_CONSISTENCY_PASS = true`
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true`
- `VISIBLE_OBJECT_DENOMINATOR = 30`
- `VISIBLE_OBJECTS_MANUALLY_REVIEWED = 30`
- `UNORDERED_PAIR_DENOMINATOR = 435`
- `UNORDERED_PAIRS_MANUALLY_REVIEWED = 435`
- `UNRESOLVED_COUNT = 0`

Manual basis: the current PDF shows two normalized zero-mean Gaussian densities with the correct widths and peaks, a correct x=0 reference, a unit-area conclusion, correct caption and neighboring text consistency, intact glyphs, no clipping, no illegal visible-ink collision, and stable grayscale/page hierarchy. Legacy numeric size/ratio values were treated only as advisory exactly as R168 requires; no R168 hard-fail condition is present.

Only authorized return token: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.
