# FIG-P656-01 SA1 visual acceptance

- HANDOFF_ID = `C-FIG-P656-01-R108-SA1-FRESH-ISOLATED-REPLACEMENT-V2`
- SA1_MODEL = `gpt-5.6-sol`
- SA1_REASONING = `xhigh`
- SA2_MODEL = `NOT_INVOKED_BY_SA1`
- SA2_REASONING = `NOT_INVOKED_BY_SA1`
- SA2_ESCALATED = `false`
- SA3_MODEL = `PENDING_FRESH_ISOLATED_SA3`
- SA3_REASONING = `PENDING_FRESH_ISOLATED_SA3`
- SOURCE_FONT_PASS = `true`
- PIXEL_HEIGHT_PASS = `true`
- SAME_CLASS_RATIO_PASS = `true`
- ROLE_RATIO_PASS = `true`
- OVERLAP_CANDIDATE_PIXEL_COUNT = `0`
- MASK_CONTAMINATION_PIXEL_COUNT = `0`
- OVERLAP_PIXEL_COUNT = `0`
- PIXEL_ADJUDICATION_STATUS = `CLEAR`
- PIXEL_ARBITER_MODEL = `NOT_USED`
- PIXEL_ARBITER_REASONING = `NOT_USED`
- CLIP_PIXEL_COUNT = `0`
- MIN_TEXT_CLEARANCE_PX = `6.000` (text-text bbox; category-specific minima are 6.000/9.000/16.000/22.472 px)
- VISUAL_HARMONY_PASS = `true`
- MATH_SEMANTICS_PASS = `true`
- TEXT_CONSISTENCY_PASS = `true`
- GRAYSCALE_PASS = `true`
- PAGE_INTEGRATION_PASS = `true`

## Source font gate

The source sets the figure style and every node to 9.5 TeX pt and the heading to 9.9 TeX pt. There is no `scale`, `transform shape`, `resizebox`, or `scalebox`; cumulative graphics scale is 1.0. PDF spans of 9.46451 bp and 9.86301 bp map back using `TeX pt = PDF bp * 72.27 / 72` to 9.50000 pt and 9.90000 pt. The 6.62512 bp spans are natural 70% math scripts derived from the valid 9.5 pt baseline, not manually reduced formula text.

## Native 300 dpi pixels and R168 interpretation

The 18 token digits measure 26--27 px (same-role max/min 1.038); Chinese line elements measure 34--42 px; formula blocks measure 38--74 px. Ten natural script glyphs measure 19--23 px. All are above the applicable hard thresholds. Intrinsically shallow punctuation or horizontal-stroke glyphs in the raw 90-glyph table can have a small isolated ink height; under R168 this is an outline/taxonomy advisory, not evidence of a reduced-font text element. There is no tofu, wrong glyph, unreadability, or severe role imbalance.

## Manual visual and semantic result

All 48 objects and 12 critical IDs were manually adjudicated after opening the required views. Reading order is left-to-right: three ordered sequences, common count vector, support constraints/warning, then the multinomial coefficient. The three sequences independently yield `(3,1,2)`, `N=6`, and coefficient `6!/(3!1!2!)=60`. Arrows, borders, labels, and grayscale encoding are clear and unclipped. The two-line caption is long but readable and does not cause a hard visual imbalance under R168.

## SA1 result

`SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`

This is an SA1-only conclusion. It is not `A_LOCAL_PASS`, central pass, integration pass, or publication approval.

