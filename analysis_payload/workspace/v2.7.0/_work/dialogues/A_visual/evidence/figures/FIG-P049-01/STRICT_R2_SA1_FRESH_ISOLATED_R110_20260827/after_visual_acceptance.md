# FIG-P049-01 SA1 visual acceptance

- `RESULT = FAIL`
- `FIGURE_ID = 图 3.1`
- `CANONICAL_UID = FIG-P049-01`
- `SA1_MODEL = gpt-5.6-sol`
- `SA1_REASONING = xhigh`
- `SA2_MODEL = NOT_USED`
- `SA2_REASONING = NOT_USED`
- `SA2_ESCALATED = false`
- `SA3_MODEL = NOT_RUN`
- `SA3_REASONING = NOT_RUN`
- `SOURCE_FONT_PASS = true` under R168; the legacy 9.5 pt gate is false but the current 9.2/9.4 pt differences are advisory and produce no unreadability or wrong glyph.
- `PIXEL_HEIGHT_PASS = true`
- `SAME_CLASS_RATIO_PASS = true`; contour base glyphs are 20/20/20 px after color adjudication and derived subscripts are 19/19/20 px.
- `ROLE_RATIO_PASS = true` under R168; the 9.2 versus 9.4 pt role difference is minor and not visually imbalanced.
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 10`
- `MASK_CONTAMINATION_PIXEL_COUNT = 10`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`
- `PIXEL_ARBITER_MODEL = NOT_USED`
- `PIXEL_ARBITER_REASONING = NOT_USED`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 7.991`
- `VISUAL_HARMONY_PASS = false` because two numbered callout leaders cross and the first leader lands in the wrong semantic region.
- `MATH_SEMANTICS_PASS = false` for the whole visual because guide 1 contradicts its target claim; the underlying function, contours, gradient, tangent, and right-angle construction pass.
- `TEXT_CONSISTENCY_PASS = false` at the note-to-target relation; literal labels/formulas/codepoints otherwise match current source and neighboring text.
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true`
- `ROUTE = SA2`

Blockers:

1. Move guide 1 so that it terminates unambiguously at P or the `c_3` contour at P.
2. Reroute guides 1 and 2 so their polylines do not cross or merge; preserve clear separation from the gradient arrow and right-angle marker.
3. Regenerate native 300-dpi/1×/8× evidence and repeat the complete denominator/pair and semantic gates.
