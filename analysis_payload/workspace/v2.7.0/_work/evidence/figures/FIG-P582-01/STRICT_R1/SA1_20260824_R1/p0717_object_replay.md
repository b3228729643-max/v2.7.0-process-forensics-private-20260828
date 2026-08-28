# P0717 object-level replay and purity distinction

`P0717` is `E014` (`↓`) versus `E016` terminal `0` in `.380`, on physical PDF page 630 / printed page 617. The pair package is `roi_packages_r2_geometry_isolated/P0717_E014_E016/`.

Its `mask_A_1x.png` is the independently replayed arrow object (`E014`); `mask_B_1x.png` is the independently replayed numeric-value object (`E016`). The 1× files use the native final-PDF 300dpi grid. `intersection_1x.png` has exactly 3 pixels. `original_raw_1x.png`, both object masks, their intersection, and their overlay were each opened at 1× and as the supplied 8× nearest-neighbour views. The crop is figure-relative `[1243,169,1327,249]`, 84×80 px.

“Cannot safely isolate” would mean that final visible ink could not be assigned completely to one object through a PDF glyph/CID/path replay or a geometrically traceable draw-order separation, leaving either a missing target stroke or a foreign non-target pixel. That condition does **not** apply here: both object replays are independently complete and pure. `glyph_final_mask_integrity.csv` records `MASK_PURITY_COMPLETENESS_PASS=true`, `FINAL_FOREIGN_GLYPH_PIXEL_PX=0`, and `REAL_SHARED_COLLISION_PX=3` for G0029 and G0036.

The three shared final-visible pixels are therefore preserved as a real relation collision and are not trimmed, painted white, or recast as evidence contamination. This yields `EVIDENCE_INTEGRITY_PASS=true` and independently yields P0717 `OVERLAP_PIXEL_COUNT=3`, minimum clearance `0px`, and the figure hard failure.
