# FIG-P077-01 — SA2 R168 read-only acceptance

Reviewer: `SA2-R168`  
Handoff: `A-R114-P077-SA2-R168-READONLY-20260827`  
Candidate: official R114, physical PDF page 79 (sole independent caption search hit)  
Observation basis: full-page 200 dpi, full-page native 300 dpi, native figure crop, grayscale crop, object-ID overlay, and five native1x/nearest8x critical ROI pairs were all opened before these fields were written.

## Manual gating fields

- `LEGACY_SOURCE_FONT_THRESHOLD_RESULT = ADVISORY_BELOW_9_5` — source declares 8.8 pt ticks, 9.2 pt direct/area labels, and 9.4 pt axis labels. Under the assigned R168 rule these values alone cannot cause hard FAIL or source return.
- `R168_HARD_READABILITY_FAIL = false` — every visible label is crisp and unambiguous in native 300 dpi and nearest-neighbor critical ROIs.
- `PIXEL_HEIGHT_PASS = true` — threshold-20/255 machine observations are 26–27 px for digit ticks, 21 px for italic x, 46–47 px for direct-label rows, 36 px for the area row, and 35–39 px for caption runs; vertical 密度 is fully formed.
- `SAME_CLASS_RATIO_PASS = true` — six numeric ticks measure 26–27 px (max/min 1.038); the two direct-label rows measure 46–47 px (max/min 1.022).
- `ROLE_RATIO_PASS = true` — source role ratios are coherent (axis label 9.4/8.8=1.068; direct and annotation 9.2/8.8=1.045), and native pixels show no role dominating the graph.
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0` — native foreground inspection found no shared visible text/line, text/curve, text/marker, text/border, legend/curve, annotation/curve, or arrowhead/text pixels. Bounding-box containment in the overlay is not an ink candidate.
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 3.3` — narrowest observed text-to-visible-line clearance is at O11 where the x-axis re-emerges from the opaque annotation background; 0.79 pt × 4.168 px/pt ≈ 3.3 px. The hidden line under the white node is background-masked and is not visible semantic foreground.
- `VISUAL_HARMONY_PASS = true` — the solid/dashed hierarchy remains distinct in grayscale; the graph is balanced and the labels do not displace its mathematical subject.
- `MATH_SEMANTICS_PASS = true` — N(0,1) peaks at 1/sqrt(2pi), N(0,2^2) peaks at 1/(2sqrt(2pi)), both are centered at zero, and the area-one statement is correct.
- `TEXT_CONSISTENCY_PASS = true` — graph labels, caption, and following reading paragraph agree on center, variance/scale, peak, and normalization.
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true` — figure, caption, preceding proof, following reading guidance, and next heading have stable spacing with no clipping or obvious imbalance.
- `MISSING_TOFU_WRONG_CODEPOINT = false`
- `TRUE_HARD_DEFECT = false`

## R168 decision

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

The advisory legacy font declarations do not supply a hard-return fact. No R114 missing/tofu/wrong-codepoint or mathematical-meaning error, unreadability, obvious imbalance, true clipping, illegal ink overlap, or geometry/semantic error was observed.
