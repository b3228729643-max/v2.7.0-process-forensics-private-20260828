# after overlap adjudication — FIG-P610-01 / R104 / SA3

- reviewer_type: `AI_SA3_VISUAL_REVIEW`
- human_certification: `false`
- reviewed raster: `full_page_fitz_reference_300dpi.png` with confirmation against `full_page_native_300dpi.png`
- actual semantic objects: 38
- complete unordered pairs: 703/703 unique
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- unresolved clusters: 0

The isolated semantic-mask ledger has zero shared foreground pixels for every one of the 703 unordered pairs, so there is no positive candidate cluster to classify as `TRUE_COLLISION`, `MASK_CONTAMINATION`, or `UNRESOLVED`. This zero-candidate result was not accepted solely from the count: the 26 closest pairs (all blank clearances <=20 px) were individually compared in native 1x, nearest-neighbour 8x, grayscale, vector/source geometry, and mask evidence; their per-ID observations are recorded in `manual_critical_pair_review.csv`.

The closest text-related pairs are:

1. `TXT_R_REJECT__G_R_OUT_NODE_2_DOUBLE`: 13.560220 px blank clearance, zero overlap.
2. `TXT_R_REJECT__G_R_PROPOSAL_CONNECTOR_2`: 13.866069 px blank clearance, zero overlap.

The closest non-text connected pair is `G_R_OUT_NODE_2_DOUBLE__G_R_PROPOSAL_CONNECTOR_2`: 3 px true white gap, zero overlap. The 8x view confirms the endpoint does not touch the double border. Under R168, the designated 5 px main-line gap is advisory and cannot independently cause FAIL; it is therefore recorded as an advisory, not reclassified as a collision.
