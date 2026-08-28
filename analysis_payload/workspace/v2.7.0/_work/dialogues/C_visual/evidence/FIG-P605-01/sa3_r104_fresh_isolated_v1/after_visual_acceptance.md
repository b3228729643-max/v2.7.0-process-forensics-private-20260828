# FIG-P605-01 / R104 / SA3 visual acceptance

## Candidate identity

The official R104 candidate is the 817-page A4 PDF at the path recorded in `IDENTITY.json`; its byte size and SHA-256 exactly match the task. I independently located the current figure on physical page 658 (printed page 645) by matching both panel titles and the current caption. No prior SA1/old evidence, inherited page number, prior denominator, conclusion, or hash was read.

## Views actually reviewed

I opened the direct official-PDF renders `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, and `grayscale_300dpi.png`, plus the 300 dpi measurement overlay, all 13 glyph contact sheets, every one of 23 graphic-object contact files, and all 13 pair-candidate 1×/8× quint views. Detailed view-level records are in `manual_view_review.csv`.

The figure has a clear left-to-right comparison. Panel titles are prominent without overpowering the diagram. Kernel nodes, formulae, explanatory cards, arrows, and caption are readable at whole-page scale and crisp at native 300 dpi. The two panels remain distinguishable in grayscale through shape, direction, and layout even when color is removed. The caption integrates naturally with the page and does not collide with the figure or the following section heading.

## R168 font disposition

The figure source uses 9.2 pt for ordinary nodes and 9.8 pt bold for panel titles, with no `resizebox`, `scalebox`, `scale`, or `transform shape`. The 9.2 pt value is below the legacy 9.5 pt source threshold, and 17 individual low-profile/natural-script measurements are legacy calibration or pixel-threshold advisories. I did not convert these into a hard failure: every affected glyph was individually opened and is actually readable, its Unicode/codepoint is correct, and there is no tofu, wrong glyph, missing stroke, clipping, illegal overlap, or obvious severe size imbalance. This is the R168-required treatment.

## Hard visual gates

- `FONT_VISUAL_HARMONY_PASS=true`
- `ACTUAL_UNREADABLE_COUNT=0`
- `TOFU_OR_WRONG_CODEPOINT_COUNT=0`
- `SEVERE_FONT_IMBALANCE_COUNT=0`
- `OVERLAP_CANDIDATE_PIXEL_COUNT=224`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `CLIP_PIXEL_COUNT=0`
- `MIN_TEXT_TEXT_CLEARANCE_PX=41`
- `MIN_TEXT_LINE_ARROW_CLEARANCE_PX=20.1`
- `MIN_TEXT_NODE_BORDER_CLEARANCE_PX=16`
- `MIN_TEXT_PANEL_BORDER_CLEARANCE_PX=27`
- `MATH_SEMANTICS_PASS=true`
- `BODY_CONSISTENCY_PASS=true`
- `GRAYSCALE_PASS=true`
- `PAGE_INTEGRATION_PASS=true`

Conclusion: `C_LOCAL_PASS_ONLY`. This is an isolated SA3 local conclusion, not a global acceptance. Central inventory/state and the source remain untouched; the result waits for mainline handling.

