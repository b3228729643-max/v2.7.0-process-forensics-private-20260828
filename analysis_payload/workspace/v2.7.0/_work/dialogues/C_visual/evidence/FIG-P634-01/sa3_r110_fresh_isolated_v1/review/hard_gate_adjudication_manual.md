# SA3 hard-gate adjudication — FIG-P634-01

## Fixed route

- `OWNER_DIALOGUE = C_visual`
- `HANDOFF_ID = C-FIG-P634-01-R110-SA3-FRESH-ISOLATED-V1`
- `SA3_MODEL = gpt-5.6-sol`
- `SA3_REASONING = xhigh`
- `FORK_TURNS = none`
- `SA3_ROLE = independent second blind reviewer`

## Evidence coverage actually opened

- Physical page 684 at native 300 dpi.
- Physical page 684 at 200 dpi for the protocol whole-page comparison.
- Complete figure plus full caption at native 300 dpi.
- Figure-only native 300 dpi crop.
- Native 300 dpi grayscale crop.
- Object, semantic-class, and text/formula overlays.
- Five critical native1x ROIs and their five nearest-neighbour8x counterparts.

## Denominators and manual coverage

- Visible objects: 46/46 manually adjudicated by ID.
- Complete unordered pairs preserved: 1,035/1,035 in the frozen denominator.
- Relevant/close pairs manually adjudicated: 38/38 selected from the complete denominator.
- Text/codepoint spans: 47/47 manually adjudicated by ID.
- Critical ROIs: 5/5 manually adjudicated at both scales.
- Views: 18/18 manually recorded as actually opened.

## Required hard-gate fields

- `SOURCE_FONT_PASS = true`
- `PIXEL_HEIGHT_PASS = true`
- `SAME_CLASS_RATIO_PASS = true`
- `ROLE_RATIO_PASS = true`
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- `PIXEL_ARBITER_MODEL = NOT_USED`
- `PIXEL_ARBITER_REASONING = NOT_USED`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 5`
- `VISUAL_HARMONY_PASS = true`
- `MATH_SEMANTICS_PASS = true`
- `TEXT_CONSISTENCY_PASS = true`
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true`

`OVERLAP_CANDIDATE_PIXEL_COUNT` is zero for independent visible foreground objects after class-aware inspection. The bbox denominator deliberately includes legal containment pairs such as text inside node or panel borders; those are not pixel-overlap candidates. Each such relevant containment was manually checked in the original raster and the nearest-neighbour ROI, and the minimum text-to-node-border ink clearance is 5 px.

## R168 advisory

The 21 px ink height of mathematical italic U+1D465 `x` is recorded as an advisory raster/font-outline/taxonomy edge. It is a lowercase x-height glyph above the 17 px class floor and is clearly readable. It does not qualify as a hard failure under R168.

## Result

`RESULT = SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

No hard blocker, new regression, unresolved candidate, or required source change was found.
