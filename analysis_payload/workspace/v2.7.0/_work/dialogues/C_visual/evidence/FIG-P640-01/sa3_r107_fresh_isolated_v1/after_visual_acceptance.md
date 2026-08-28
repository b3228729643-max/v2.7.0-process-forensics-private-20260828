# FIG-P640-01 independent SA3 visual acceptance

HANDOFF_ID = C-FIG-P640-01-R107-SA3-FRESH-ISOLATED-V1  
REVIEWER = SA3-R107-FRESH-ISOLATED-V1  
SA1_MODEL = NOT_READ_BY_STRICT_ISOLATION  
SA1_REASONING = NOT_READ_BY_STRICT_ISOLATION  
SA2_MODEL = NOT_READ_BY_STRICT_ISOLATION  
SA2_REASONING = NOT_READ_BY_STRICT_ISOLATION  
SA2_ESCALATED = NOT_READ_BY_STRICT_ISOLATION  
SA3_MODEL = gpt-5.6-sol  
SA3_REASONING = xhigh  
SA3_FORK_TURNS = none  
OFFICIAL_ROUND = R107  
PHYSICAL_PAGE = 690  
PRINTED_PAGE = 677  
FIGURE = 33.7  
SOURCE_FONT_PASS = true  
PIXEL_HEIGHT_PASS = true  
SAME_CLASS_RATIO_PASS = true  
ROLE_RATIO_PASS = true  
FONT_VISUAL_HARMONY_PASS = true  
OVERLAP_CANDIDATE_PAIR_COUNT = 12  
OVERLAP_CANDIDATE_PIXEL_COUNT = 5843  
MASK_CONTAMINATION_PIXEL_COUNT = 5843  
OVERLAP_PIXEL_COUNT = 0  
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED  
PIXEL_ARBITER_MODEL = NOT_USED  
PIXEL_ARBITER_REASONING = NOT_USED  
CLIP_PIXEL_COUNT = 0  
MIN_TEXT_CLEARANCE_PX = 7.280  
VISUAL_HARMONY_PASS = true  
MATH_SEMANTICS_PASS = true  
TEXT_CONSISTENCY_PASS = true  
GRAYSCALE_PASS = true  
PAGE_INTEGRATION_PASS = true  
LOCAL_PASS_COUNTED = false  
GLOBAL_PASS_COUNTED = false  
SA3_REVIEW_OUTCOME = CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE

## Independent findings

The official PDF identity is exactly 817 pages, 4,967,249 bytes, SHA256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`. The page header, caption, PDF text layer, current figure source and adjacent current chapter independently identify physical page 690 / printed 677 / Figure 33.7.

The current source and rendered geometry agree: panel A plots `rho^(2k)` using squared magnitudes `.9025`, `.49` and `.04`; panel B plots `(1-rho^2)/(1+rho^2)` only through `.99`, labels the actual endpoint `(.99,.010)`, and states the one-sided boundary limit. No displayed value asserts that the excluded boundary `|rho|=1` is inside the plotted domain.

The semantic denominator is frozen as `15 TEXT + 10 GRAPHIC + 1 GRAPHIC_MATH_RULE + 2 BACKGROUND = N=28`. The complete unordered denominator is `C(28,2)=378`, and all 378 machine pair rows are present. Forty-two mandatory/critical relations each have native-1x and 8x evidence plus a manual row. The sole drawing-based math rule is the B-title fraction bar; it is nonempty, separately identified, five native pixels from glyph ink, and correctly included in N and all pairs.

All 145 visible glyphs have unique raw masks, native and 8x triptychs, and coverage across 29 contact sheets; every sheet and cell was opened. Manual rows record `missing_stroke_px=0` and `foreign_pixel_px=0` for every glyph, while the machine cross-mask table is empty. No tofu, wrong glyph/codepoint, wrong formula semantics, actual unreadability, visibly severe size imbalance or real clipping is present.

The source uses explicit base sizes of 9.6pt for ticks/titles/legend/annotations and 9.8pt for axis labels, without figure-wide scaling. Thirty-four shape/taxonomy-based raw-height readings fall below the protocol's nominal category thresholds, principally natural scripts, rotated projected shapes, equality/arrows/minus, fullwidth colons and fraction-style digits. Under the supplied R168 authority these numeric/taxonomy differences are advisory because the actual glyphs are complete, pure, readable, correctly encoded and visually balanced. The per-ID glyph and peer-role ledgers preserve these measurements rather than hiding them.

The final detector denominator contains 12 raw-overlap pairs totaling 5843 pixels. All are manually classified `MASK_CONTAMINATION`: four opaque-background composition/edge candidates, seven intended analytic curve/axis/data coincidences, and one intended curve-marker connection. Canonical illegal `OVERLAP_PIXEL_COUNT=0`; unresolved count is zero. The provisional 5993 checkpoint is reconciled explicitly in `denominator_reconciliation.md`: final glyph ownership reduced the two background-to-own-text candidates by 100 and 50 pixels while the other ten retained 2391 pixels.

Applicable clearances pass: independent text-to-text bbox minimum is 7.280px; text-to-curve minimum is 8.944px; text-to-axis minimum is 14px; legend text-to-swatch minimum is 13px; same-formula fraction-rule-to-glyph clearance is 5px. The one-pixel B axis-to-endpoint-marker gap is non-text boundary-approach geometry and correctly distinguishes `.99` from the excluded boundary.

All nine review views pass. In grayscale, panel A retains solid/dashed/dash-dot separation and panel B remains distinct from axes. On the full page and page-integration crop, the figure is subordinate to the chapter hierarchy, the caption is aligned with the graphic, and surrounding prose continues naturally. Neither panel is crowded; data geometry retains primary visual weight.

This is a non-authoritative SA3 candidate outcome only. It does not count a local or global pass, modify source/build/central state, or replace main-thread acceptance.
