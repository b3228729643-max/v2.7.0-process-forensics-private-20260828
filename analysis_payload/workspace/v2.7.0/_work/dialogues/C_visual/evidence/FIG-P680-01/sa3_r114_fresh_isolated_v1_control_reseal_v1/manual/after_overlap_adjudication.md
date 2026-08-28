# Post-observation overlap adjudication

HANDOFF_ID: `C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-V1`  
UID: `FIG-P680-01`

The frozen semantic denominator contains 14 reader-visible objects and 91 unordered pairs. All 91 pair IDs were observed in the native-300 figure/object overlay; arrow-critical pairs were additionally opened at native 1× and nearest-neighbor 8×.

The only touching semantic-object pairs are P008, P009, P031, P033, P042, P044, P060, and P068. Each is an intended connector endpoint meeting the boundary of its source or destination node. In every native and 8× view, the arrow shaft/head remains separated from the node text. These legal topological contacts are not illegal visible-ink overlap candidates.

Every other pair is visibly disjoint. The machine text-arrow table contains 60/60 zero-bbox-intersection cases; its minimum text-arrow gap is 19.05 px at 300 dpi. The machine node-interior table places every contained text line clear of its node border; the minimum measured text-to-border clearance is 23.21 px. The closest two independent caption text lines retain an approximately 10.83 px bbox gap and do not share visible ink.

- OVERLAP_CANDIDATE_PIXEL_COUNT (illegal candidate set): `0`
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT (true illegal visible-ink overlap): `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- UNRESOLVED: `0`
- CLIP_PIXEL_COUNT: `0`

Manual conclusion: no true illegal visible-ink collision, no clipped arrowhead, and no unresolved candidate is present.
