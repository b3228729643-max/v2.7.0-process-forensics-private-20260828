# Post-observation all-pairs ledger

## Denominator and exact row identity

The exact pair table is `machine/all_unordered_pairs_geometry.csv`, with one row for every unordered pair in canonical order `T01..T15,G01..G10`. It has pair sequence 1 through 300, no duplicate object pair, and `300 = 25*24/2`. The current manual review was performed after opening the full-page, native, crop, grayscale, object overlay, semantic overlay, and every critical native1x/NN8x ROI.

Every pair row is covered by the following disjoint adjudication partition.

| partition | exact pair-sequence IDs | count | post-observation classification |
|---|---|---:|---|
| text inside its intended node container | 15, 38, 82, 102, 122, 140, 174, 189, 204, 217, 234 | 11 | legal containment; text ink does not touch the node border; minimum inward text-to-border clearance is 21.800504 px |
| arrow origin intentionally attached to its source-node border | 260, 261, 270, 278 | 4 | legal semantic connector origin; no text is involved or obscured |
| arrow termination intentionally attached to its target-node border | 268, 276, 283, 289 | 4 | legal semantic connector termination; no text is involved or obscured |
| all other exact pair-sequence IDs in 1..300 | complement of the 19 IDs above | 281 | separate reader-visible objects; no illegal visible-ink overlap, clipping, or obstructed reading path observed |

The partition is exhaustive (`11+4+4+281=300`) and disjoint. It is also consistent with the objective bbox table: 13 bbox intersections comprise the 11 legal containments plus the 2 legal shared-node arrow origins; the other 287 bbox pairs have zero bbox intersection, including the six remaining intended connector endpoints whose antialiased strokes meet their source/target border without entering any text.

## Mandatory semantic-pair audit

| pair family | exact count | manual result |
|---|---:|---|
| TEXT-TEXT | 105 | no illegal ink intersection; minimum bbox gap 5.530037 px at T04-T05 |
| TEXT-GRAPHIC | 150 | 11 legal node containments and 139 non-contact pairs; no text/arrow contact; minimum text-arrow bbox gap 17.238004 px at T02-G06; minimum text-to-node-border inset 21.800504 px |
| GRAPHIC-GRAPHIC | 45 | eight intended arrow-node connector relations and 37 non-obstructing pairs; no illegal collision |

Semantic masking treats an arrow's intended attachment to its source/target node border as one legal connector relation, not as an illegal-overlap candidate. After that explicit relation map, the mandatory illegal-overlap candidate set is empty.

- OVERLAP_CANDIDATE_PIXEL_COUNT: `0`
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT: `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- CLIP_PIXEL_COUNT: `0`
- unresolved pair count: `0`

The actual reader-visible minimum clearances used for adjudication are 5.530037 px (text-text), 17.238004 px (text-arrow), and 21.800504 px (text ink bbox to its own node border). All were checked on the current 300 dpi native raster and the nearest-neighbor 8x ROIs, not on a rescaled preview.
