# Fresh isolated R110 SA1 report — FIG-P049-01

`HANDOFF_ID: A-R110-P049-SA1-FRESH-ISOLATED-20260827`

- `RESULT: FAIL`
- `FIGURE_ID: 图 3.1 / FIG-P049-01`
- `R110_LOCATION: physical page 48; printed page 35`
- `BLOCKERS: guide 1 misses P/c_3 and guides 1/2 cross at (3.22952321,2.00265997), producing ambiguous callout semantics.`
- `MATH_SEMANTICS: core function/contour order/P membership/gradient direction/tangent orthogonality/right-angle marker PASS; guide semantics FAIL.`
- `TEXT_CONSISTENCY: literal text and formulas PASS; note-to-target relation FAIL.`
- `READING_ORDER: numbered sequence is visible, but crossed leaders make steps 1 and 2 ambiguous — FAIL.`
- `SOURCE_FONT_AUDIT: legacy 9.5 pt false; R168 advisory only; no missing/tofu/wrong-codepoint/unreadability hard failure.`
- `PIXEL_HEIGHT_AUDIT: PASS after documented color-mask adjudication.`
- `SAME_CLASS_RATIO_AUDIT: PASS.`
- `ROLE_RATIO_AUDIT: PASS under R168.`
- `OVERLAP_CANDIDATE_PIXEL_COUNT: 10`
- `MASK_CONTAMINATION_PIXEL_COUNT: 10`
- `OVERLAP_PIXEL_COUNT: 0`
- `PIXEL_ADJUDICATION_STATUS: MASK_CONTAMINATION_CONFIRMED`
- `CLIP_PIXEL_COUNT: 0`
- `MIN_TEXT_CLEARANCE_PX: 7.991`
- `VISUAL_HARMONY: FAIL due to crossed/misdirected guide routing; otherwise readable and balanced.`
- `FONT_AND_DENSITY: R168 advisory only.`
- `LAYOUT: FAIL locally at callout leaders.`
- `GRAYSCALE: PASS.`
- `CAPTION: PASS; one clear reading conclusion, no clipping.`
- `PAGE_INTEGRATION: PASS.`
- `REQUIRED_FIXES: terminate guide 1 at P/c_3; reroute guides 1 and 2 with no crossing; rebuild and remeasure from a new candidate.`
- `EVIDENCE_USED: identity.json; locator.json; denominator_freeze.json; all_unordered_pairs.csv; text_element_measurements_300dpi.csv; text_subspan_measurements_300dpi.csv; geometry_semantics.json; machine_gate_adjudicated.json; after_overlap_adjudication.md; opened native 300-dpi, grayscale, contact sheet, and 8× ROIs.`
- `ROUTE: SA2`

No source, main PDF, Git, shared state, inventory, or other UID was modified. SA3 was not started and no local/final PASS is claimed.
