# FIG-P634-01 R110/R168 overlap and clearance adjudication

## Frozen scope

- Semantic object denominator: 47 objects in `ledgers/object_denominator.csv`.
- Complete unordered-pair denominator: 1,081 rows in `raw/all_unordered_pair_geometry.csv`.
- Final bbox/proximity screen: 34 pairs in `raw/machine_candidate_pair_geometry.csv`.
- Manual candidate disposition: 34 individually reasoned rows in `ledgers/manual_candidate_pair_adjudication.csv`.
- Text/formula denominator: 34 items; critical ROI denominator: 6.

The provisional mechanical run reported 35 pairs. Raster measurement corrected the two rounded-panel bounds, removing the false O31–O38 panel-border intersection. The finalized frozen candidate denominator is therefore 34, not 35; no semantic object was added or removed.

## Pixel evidence and classification

Foreground masks use dark rendered ink for TEXT/FORMULA, perimeter-restricted rendered ink for NODE_BORDER/PANEL_BORDER, and local rendered ink for LINE_ARROW. The caption prose object uses two explicit line components so its non-rectangular wrap is not replaced by one misleading rectangle. The resulting `raw/candidate_pixel_metrics.csv` has zero shared foreground pixels for every one of the 34 pairs.

- `BBOX_PROXIMITY_PAIR_COUNT = 34`
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = NO_PIXEL_CANDIDATES_ALL_PROXIMITY_PAIRS_MANUALLY_CLEARED`

The 34 bbox/proximity pairs fall into four visually checked families: intended border containment, font-line-box proximity without ink contact, close but separated text/formula relations, and the two-line caption envelope. None is a TRUE_COLLISION or an unresolved candidate. There is consequently no need to reclassify any pixel as MASK_CONTAMINATION; the foreground mask screen itself produces zero candidate pixels.

## Clearance and clipping

- Minimum measured empty foreground clearance among screened pairs: 8 px (panel-internal text to panel border).
- Formula/arrow empty clearances: 17 px for `x^[d]` to the equivalence arrow and 14 px for `x^(t)` to the record arrow.
- Slot text to slot-border empty clearances: 32–33 px.
- Close text-to-text empty clearances: 16–18 px.
- Caption label to prose foreground clearance after line-component modeling: 19 px.
- `CLIP_PIXEL_COUNT = 0`: the native full page, complete crop, overlays, and all critical ROIs show no clipped text, formula, arrowhead, border, caption, or figure edge.

The required hard thresholds are therefore met: no true illegal overlap, no unresolved pixel candidate, and no clipping.
