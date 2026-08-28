# SA2 decision — FIG-P067-01

- HANDOFF_ID: `A-R111-P067-SA2-R168-READONLY-20260827`
- Canonical instance: `/root/p067_r111_r168_sa2`
- Reviewer model / effort: `gpt-5.6-sol / xhigh`
- Decision: `FAIL_TO_MAIN_SOURCE_SCOPE`
- Hard defects: 1 confirmed relationship cluster, `REL006`.
- OVERLAP_CANDIDATE_PIXEL_COUNT: 327 native 300 dpi foreground pixels inside the shared word-box region.
- MASK_CONTAMINATION_PIXEL_COUNT: 0.
- OVERLAP_PIXEL_COUNT: 327, using the frozen native-composite convention for the two isolated semantic tick-label objects inside their shared word-box region.
- PIXEL_ADJUDICATION_STATUS: `TRUE_COLLISION_CONFIRMED`.
- CLIP_PIXEL_COUNT: 0.
- MIN_TEXT_CLEARANCE_PX: `-18` for `0.35` versus `0.3`, meaning 18 pixels of vertical bbox penetration rather than positive clearance.
- SOURCE_FONT_PASS: `advisory_only_under_R168`; no source-size-only failure asserted.
- PIXEL_HEIGHT_PASS: false for the complete figure because REL006 creates unreadable composite ink; otherwise no independent unreadability finding.
- SAME_CLASS_RATIO_PASS: false for final acceptance because two same-role PMF y-ticks cannot be separately read in their current spacing.
- ROLE_RATIO_PASS: true apart from the blocked same-role relationship.
- VISUAL_HARMONY_PASS: false due to the visibly congested upper two PMF y-ticks.
- MATH_SEMANTICS_PASS: true.
- TEXT_CONSISTENCY_PASS: true.
- GRAYSCALE_PASS: false for final acceptance because REL006 persists unchanged in grayscale.
- PAGE_INTEGRATION_PASS: true.

Narrow source-scope request: in `fig_v1_c04_cdf.tex`, adjust only the lower PMF y-axis tick presentation so the `0.30` and `0.35` labels have real separation (for example remove one redundant adjacent tick label or provide explicit nonoverlapping tick-label placement) while retaining the four mass values, the CDF cumulative levels, right-continuous open/closed markers, both axis meanings, and the caption. Rebuild and submit a new current-PDF native 300 dpi crop and 8x nearest-neighbour ROI for fresh SA1. No source change was made by this SA2.

