# Manual all-pairs and overlap adjudication

## Denominator and completeness

The frozen denominator is the 22 visible semantic objects in `object_denominator_frozen.csv`. `all_unordered_pairs_machine.csv` contains every unique unordered pair `O_i,O_j` with `i<j`: 231 rows, equal to `22*21/2`. Background-container/content relations are explicitly marked so allowed fill containment is not mislabeled as illegal foreground collision.

## Machine screen reviewed manually

- Independent-object collision-mask overlap pixels: 0 for every one of the 231 pairs.
- Objects touching the figure/caption crop edge: 0.
- Objects with a bbox outside the full PDF page: 0.
- Near-threshold foreground gaps were recomputed from the separated final-raster masks in `near_threshold_mask_gaps_machine.csv`:
  - `P-O02-O03`: about 11.37 blank pixels between density-formula ink and brace.
  - `P-O13-O14`: about 29.59 blank pixels between log-partition ink and arrow.
  - `P-O14-O15`: about 15.12 blank pixels between arrow and derivative ink.
  - `P-O15-O16`: 7 blank pixels between derivative ink and blue result border.
  - `P-O20-O22`: 21 blank pixels between caption-label ink and second caption line.
- Every remaining rule-bearing pair has a conservative logical-bbox clearance above 20 px or is an explicit parent/content containment with ample visible padding.

## Sole numeric-risk adjudication

`P-O15-O16` was the only machine logical-bbox trigger because the PDF logical box for the derivative's subscript descender lies only 1 px above the result-container logical box. This is not a visible-ink collision. I opened `closest_pair_numeric_risk_overlay_300dpi.png`, `R03_right_derivation_native1x.png`, and `R03_right_derivation_nearest8x.png`. The separated masks give 8 px foreground-center distance and 7 fully blank pixels. The subscript is legible, the blue border is continuous, and neither semantic foreground occludes the other. Under R168 this bbox-outline difference is advisory, not a hard failure.

## Canonical manual decision

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0` (no separated-mask pixel-sharing candidate).
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`.
- `OVERLAP_PIXEL_COUNT = 0`.
- `PIXEL_ADJUDICATION_STATUS = CLEAR`.
- `CLIP_PIXEL_COUNT = 0`.
- `MIN_TEXT_CLEARANCE_PX = 7` for the closest independently collidable foreground pair after exact mask recomputation.
- `UNRESOLVED_CANDIDATE_COUNT = 0`.

No all-pairs row remains unknown or unclassified.
