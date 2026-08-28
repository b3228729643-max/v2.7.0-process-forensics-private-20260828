# FIG-P683-01 visible-ink overlap adjudication

Manual post-observation result: CLEAR.

All 465 unordered pairs were reviewed after opening the native 300 dpi full page, figure+caption crop, semantic/object/text overlays, grayscale crop, and every selected native1x/nearest8x ROI. No text-text, text/formula-arrow, text/formula-marker, text/formula-node-border, text/formula-panel-border, legend-data, annotation-data, or arrowhead-text illegal visible-ink collision was observed.

The following declared topology contacts are legal semantic geometry, not illegal overlap candidates:

- A01 terminates on O01 and crosses O06 to enter the M plate.
- A02 connects O01 to O02 and crosses O05 to enter the nested N_m plate.
- A03 connects O02 to O03 within O05.
- A04 terminates on O04 and crosses O07 to enter the K plate.
- A05 connects O04 to O03 and necessarily crosses O07, O06, and O05.

Each arrowhead stops at its destination node boundary. None enters node-label ink. Plate-boundary crossings occur away from plate-label ink and are required to express dependencies across replication scopes. The smallest reader-visible text-to-arrow gap is T01–A01 at 4 native 300 dpi pixels, above the 3 px text/formula-to-line criterion; all node-label-to-node-border clearances visibly exceed 5 px. Caption lines retain at least 11 px bbox separation. No foreground reaches the figure crop or physical page edge.

OVERLAP_CANDIDATE_PIXEL_COUNT=0
MASK_CONTAMINATION_PIXEL_COUNT=0
OVERLAP_PIXEL_COUNT=0
PIXEL_ADJUDICATION_STATUS=CLEAR
CLIP_PIXEL_COUNT=0
MIN_TEXT_CLEARANCE_PX=4
