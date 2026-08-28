# FIG-P640-01 — fresh isolated R104 SA1 review

- HANDOFF_ID: `C-FIG-P640-01-R104-SA1-FRESH-ISOLATED-V1`
- reviewer instance: `/root/sa1_fig_p640_r104_fresh_isolated`
- reviewer_type: `AI_SA1_VISUAL_REVIEW`
- human_certification: `false`
- model / reasoning: `gpt-5.6-sol` / `xhigh`
- source and PDF access: read-only
- result: `FAIL`
- return token: `SA1_FAIL_REQUEST_FRESH_ISOLATED_SA2`

## Independent mapping

The current source label `fig:V5-C04-mixing-rho-comparison` and caption anchor “二元正态系统 Gibbs 的轮末解析自相关为” were matched directly against the authorized R104 PDF. The independent mapping is:

- figure number: 33.7
- physical PDF page: 690
- printed page: 677

No old P640 evidence, old SA/root/handoff/report/result, central state/inventory, Git history, other UID evidence, or chat conclusion was read.

## Denominators and completed review

- logical reader-text IDs: 30/30 manually reviewed in `sa1_manual_element_object_review.csv`
- actual semantic objects: 40/40 manually reviewed (30 text + 10 vector)
- extracted R104 glyph rows: 263/263 inventoried; 242 are non-space
- complete unordered actual-object pairs: 780/780 inventoried in `machine_all_unordered_pairs.csv`
- bbox-intersection pairs: 16/16 individually adjudicated in `sa1_manual_candidate_pair_adjudication.csv`
- overlap mask candidates after semantic filtering: 1 cluster, 55 native pixels
- clip checks: standalone crop boundary, full-page boundary, labels, arrows, marker and caption inspected; no clipped foreground found
- views: full page 200/300 dpi; figure crop; standalone-equivalent native 300 dpi; grayscale; native 1x and nearest-neighbor 8x critical crops; text overlay; clip guard; separated axis/marker masks and overlap overlay

The 764 non-intersecting unordered pairs retain their exact per-pair gaps in the mechanical pair inventory. They were not assigned a templated PASS. The 16 geometrically intersecting pairs received explicit, pair-specific manual decisions.

## Hard blocker

`CAND_001 / PAIR_0779` is a true illegal overlap between `GFX_B_AXIS_AND_TICKS` and `GFX_B_POINT_MARKER`.

The open marker for `(.99,.010)` is centered only about 3.1 native pixels above the x-axis while its radius is about 7.5 pixels, and it is also placed at the positive-x arrow tip. Separate vector-derived 300 dpi masks share **55 pixels**. The 8x overlay shows the gray axis arrow/stroke intruding into the gold marker ring. This contact is not mathematically required: the data point can remain at x=.99 while the axis endpoint/arrow is moved or suppressed. It is therefore `TRUE_COLLISION`, not mask contamination and not a 1–2 px raster advisory.

## R168 font and clearance review

- No missing glyph, tofu, wrong codepoint, unreadable text, or severe font-scale imbalance was found.
- Source base sizes are 9.6 pt for ticks/titles/legend/annotations and 9.8 pt for axis labels; graphics scale is 1.0.
- The two nested rho-squared superscripts in the panel-(b) fraction render at 14 px. They are visibly legible; the one-pixel legacy-threshold shortfall is advisory under R168.
- The first `N` in the limit note has about 1.0–1.414 px clearance from the curve in the peer-glyph reconstruction. Native 1x/8x inspection finds no shared ink. This is recorded as an R168 raster advisory, not a hard failure.

## Mathematical, object and text consistency

- Panel (a) uses `(.95^2)^k = .9025^k`, `(.70^2)^k = .49^k`, and `(.20^2)^k = .04^k`; all equal 1 at k=0 and decay at the displayed rates.
- Panel (b) plots `(1-rho^2)/(1+rho^2)`, with f(0)=1, f(.5)=.6, and f(.99)=0.0100499975, consistent with the `(.99,.010)` label.
- The limit is correctly stated from the legal side `|rho| -> 1^-` and matches the adjacent prose's `|rho|<1` boundary.
- Caption, panel variables, line encodings, legend values, and adjacent V5-C04 derivation agree.
- Grayscale preserves solid / dashed / dash-dot distinctions.

## Result matrix

- SOURCE_FONT_PASS = true (R168)
- PIXEL_HEIGHT_PASS = true (R168; one 14 px script advisory)
- SAME_CLASS_RATIO_PASS = true (R168)
- ROLE_RATIO_PASS = true (R168)
- OVERLAP_CANDIDATE_PIXEL_COUNT = 55
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 55
- PIXEL_ADJUDICATION_STATUS = TRUE_COLLISION_CONFIRMED
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 1.0 (R168 advisory; not the hard blocker)
- VISUAL_HARMONY_PASS = false
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

## Required SA2 fix

Preserve the actual point coordinate `(.99,0.0100499975)` but prevent the marker from touching the positive-x axis arrow/stroke. Suitable local repairs include extending the x-axis beyond .99 while keeping the .99 tick and marker at their true coordinate, or removing/repositioning the positive-x arrowhead. Re-render the full page and all native 300 dpi evidence, rebuild masks/pairs, and submit a new fresh SA1 instance. No source modification was performed by this SA1.

RESULT: FAIL

RETURN: `SA1_FAIL_REQUEST_FRESH_ISOLATED_SA2`
