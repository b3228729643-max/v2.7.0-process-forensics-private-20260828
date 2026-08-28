# SA1 final visual acceptance

- RESULT: `PASS`
- ROUTE_STATUS: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
- FIGURE_ID: `FIG-P049-01`
- HANDOFF_ID: `A-R111-P049-SA1-FRESH-ISOLATED-20260827`
- REVIEWER_INSTANCE: `/root/p049_r111_fresh_sa1`
- SA1_MODEL: `gpt-5.6-sol`
- SA1_REASONING: `xhigh`
- SA2_MODEL: `NOT_READ_OR_INFERRED_BY_ISOLATED_SA1`
- SA2_REASONING: `NOT_READ_OR_INFERRED_BY_ISOLATED_SA1`
- SA2_ESCALATED: `NOT_READ_OR_INFERRED_BY_ISOLATED_SA1`
- SA3_MODEL: `NOT_STARTED_BY_SA1`
- SA3_REASONING: `NOT_STARTED_BY_SA1`
- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `true`
- OVERLAP_CANDIDATE_PIXEL_COUNT: `0` real-illegal candidate pixels after direct all-pair visual adjudication; conservative bbox candidate pairs are separately retained as 94 intersections and 125 within-8-px cases
- MASK_CONTAMINATION_PIXEL_COUNT: `0` canonical illegal-overlap pixels reassigned as mask contamination
- OVERLAP_PIXEL_COUNT: `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- PIXEL_ARBITER_MODEL: `NOT_USED`
- PIXEL_ARBITER_REASONING: `NOT_USED`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `3.17` for independent simultaneously visible text/path objects (`G-065/P-002`); same-string glyph adjacency and background-occluded paths are not independent simultaneously visible objects
- VISUAL_HARMONY_PASS: `true`
- MATH_SEMANTICS_PASS: `true`
- TEXT_CONSISTENCY_PASS: `true`
- GRAYSCALE_PASS: `true`
- PAGE_INTEGRATION_PASS: `true`
- MISSING_GLYPH_COUNT: `0`
- TOFU_GLYPH_COUNT: `0`
- WRONG_CODEPOINT_COUNT: `0`
- ACTUALLY_UNREADABLE_ELEMENT_COUNT: `0`
- OBVIOUS_IMBALANCE_COUNT: `0`
- GEOMETRY_OR_SEMANTIC_ERROR_COUNT: `0`

## Direct-strict denominator

- Nonempty visible glyph atoms, figure body plus caption: `135`.
- Foreground PDF path/paint atoms: `17`; all `751` constituent path primitives are retained in their machine payloads.
- Explicit non-semantic white label backing exclusions: `11`.
- Frozen denominator: `N=152`.
- Complete unordered relation denominator: `C(152,2)=11,476`; exactly `11,476` unique ordered-canonical pair rows, no self-pairs and no unrecognized IDs.
- Per-ID manual ledger: `152/152` populated by SA1 after visual inspection; no blank reviewer/observed/decision/note/PASS field.

## R168 ruling

The 9.2/9.4 pt declarations and the approximately 0.075-degree tangent endpoint rounding are advisory differences. They do not produce any R168 hard failure. All hard-gate categories are clear: no missing/tofu/wrong codepoint, no math-meaning error, no actual unreadability or obvious imbalance, no real clipping, no illegal overlap, and no material geometry/semantic error.

This is an SA1 role result only. It does not claim `A_LOCAL_PASS`, integrated pass, or final pass, and it does not start SA3.
