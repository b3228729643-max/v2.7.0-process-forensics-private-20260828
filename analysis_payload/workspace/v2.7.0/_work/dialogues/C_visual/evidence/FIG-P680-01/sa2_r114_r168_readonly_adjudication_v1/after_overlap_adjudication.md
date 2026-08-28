# After-overlap adjudication

This manual adjudication was written only after opening the current R114 native raster, both overlays, and every critical native1x/nearest-neighbor8x ROI.

The frozen denominator has 25 objects and 300 unordered pairs. The machine geometry records 13 bbox intersections: 11 are text wholly contained inside its intended node, with a measured minimum inward text-to-border clearance of 21.800504 px; two are G06/G07 at the shared-node border, where each learning-dependency arrow intentionally originates. Six additional arrow-target relations are visually tangent to their intended target borders. None involves text ink.

Mandatory illegal-combination checks:

- TEXT-TEXT: no visible-ink contact; minimum bbox gap 5.530037 px.
- TEXT/FORMULA-LINE_ARROW: no contact; minimum bbox gap 17.238004 px.
- TEXT/FORMULA-NODE_BORDER: no contact; minimum inward clearance 21.800504 px.
- ARROWHEAD-TEXT: no contact in native1x or NN8x ROIs.
- Caption and figure boundaries: no clipping or spill.

The intended arrow-to-node boundary attachments are semantic connections, not illegal overlaps and not mask contamination. With that relation map applied before candidate extraction, there are no illegal-overlap candidate pixels or unresolved clusters.

- OVERLAP_CANDIDATE_PIXEL_COUNT = 0
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = CLEAR
- CLIP_PIXEL_COUNT = 0
- UNRESOLVED_CLUSTER_COUNT = 0

