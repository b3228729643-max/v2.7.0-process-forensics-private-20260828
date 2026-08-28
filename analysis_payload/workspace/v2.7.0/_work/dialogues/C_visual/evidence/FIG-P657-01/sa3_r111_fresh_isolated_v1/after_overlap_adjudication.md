# FIG-P657-01 SA3 native-pixel overlap and clipping adjudication

Evidence opened before this judgment: `local_figure_native300dpi.png`, `text_foreground_mask_300dpi.png`, `graphics_vector_mask_300dpi.png`, `overlap_candidate_mask_300dpi.png`, `overlap_candidate_overlay_300dpi.png`, `object_denominator_overlay_300dpi.png`, `text_measurement_overlay_300dpi.png`, grayscale/page views, and R01--R06 native1x/nearest8x ROI pairs.

- OVERLAP_CANDIDATE_PIXEL_COUNT = 0. The independently constructed 300 dpi text-foreground and vector-graphics masks have an empty intersection; the opened candidate mask is entirely black and the opened overlay contains no red candidate pixel.
- MASK_CONTAMINATION_PIXEL_COUNT = 0. There is no candidate cluster requiring contamination classification.
- OVERLAP_PIXEL_COUNT = 0. Manual inspection of every one of the 171 frozen unordered object pairs confirms no illegal shared semantic foreground.
- PIXEL_ADJUDICATION_STATUS = CLEAR. No `TRUE_COLLISION`, `MASK_CONTAMINATION`, or `UNRESOLVED` cluster exists.
- CLIP_PIXEL_COUNT = 0. Full-page 300/200 dpi, local figure, caption ROI, and page-integration views show all node borders, arrowheads, labels, caption lines, and glyph strokes complete. The intentional context cuts at some ROI edges are crop design only; the official page and authoritative local-figure crop contain the complete objects.
- MIN_TEXT_CLEARANCE_PX = 6.58. This is the conservative smallest audited bbox clearance, between stacked text lines inside multi-line nodes, exceeding the 4 px text--text requirement. The smallest text--line/arrow bbox clearance is 13.70 px (T18 to O16 line), exceeding 3 px. The smallest node-text--border bbox clearance is 12.08 px (T04 inside O03), exceeding 5 px. Text to the authoritative local crop edge is at least 19.00 px, exceeding 6 px. This is a single-panel diagram; the adjacent-panel 8 px rule is not applicable.
- Arrow semantics are not conflated: R02 and R05 show thick filled conjugacy arrows, while R01/R03/R04/R05 show thin open special-case arrows. Intended relation-to-node boundary attachments are enumerated as `INTENDED_BOUNDARY_ATTACHMENT` in `manual_pair_judgments.md` and do not enter node text.

Manual adjudication conclusion: zero illegal overlap pixels, zero clipping pixels, all class-specific clearances satisfied, and no unresolved pixel question.
