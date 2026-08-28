# Manual overlap and clearance adjudication

Reviewer: fresh isolated SA1 (`gpt-5.6-sol`, `xhigh`). This file was written after opening the original full-page and crop rasters, native grayscale, both overlays, all critical native1x images and their exact nearest8x companions. Independent source/PDF vector coordinates and the per-object semantic masks under `visual/masks/` were also checked.

## Mechanical observation and semantic prefilter

- Complete denominator: 30 objects; complete unordered-pair table: 435/435.
- Foreground-mask subset: 25 objects and 300/300 foreground pairs.
- The mechanical mask intersected 13 foreground pairs: 203 pairwise pixel instances, 195 unique page pixels.
- Twelve pairs (201 pairwise instances) are explicitly intended geometric contacts: axis joints, tick joints, Gaussian-curve crossings/tail convergence, boundary contacts, and the x=0 reference line crossing each curve. Those contacts do not enter the illegal-pair candidate denominator because the source semantics require them.
- The remaining prohibited-pair candidate is P251, T11-G04, 2 pixels. Native1x and nearest8x show that the two pixels belong only to the residual center tick below the white carrier; the bbox-derived T11 raster mask copied them into the text mask. The text ink and tick ink do not share a final visible pixel.

## Per-candidate manual decisions

| Pair ID | Objects | Mechanical pixels / clusters | Manual post-observation classification | Reason |
|---|---|---:|---|---|
| P251 | T11-G04 | 2 / 1 | MASK_CONTAMINATION | The text mask was made by thresholding the whole T11 vector bbox and therefore copied the adjacent residual tick fragment. Tight native1x/nearest8x shows the fragment below the colon/Chinese ink with visible white separation. |
| P300 | G01-G02 | 4 / 1 | EXPECTED_SEMANTIC_JUNCTION | Orthogonal coordinate axes meet at their origin by definition; no reader text is involved. |
| P301 | G01-G03 | 9 / 1 | EXPECTED_SEMANTIC_JUNCTION | The −4 tick is required to join the x axis. |
| P303 | G01-G05 | 9 / 1 | EXPECTED_SEMANTIC_JUNCTION | The 4 tick is required to join the x axis. |
| P319 | G02-G06 | 6 / 1 | EXPECTED_SEMANTIC_JUNCTION | The 0 tick is required to join the y axis. |
| P320 | G02-G07 | 9 / 1 | EXPECTED_SEMANTIC_JUNCTION | The 0.2 tick is required to join the y axis. |
| P321 | G02-G08 | 9 / 1 | EXPECTED_SEMANTIC_JUNCTION | The 0.4 tick is required to join the y axis. |
| P322 | G02-G09 | 12 / 1 | EXPECTED_DATA_BOUNDARY_CONTACT | The plotted solid density begins at the left plot boundary, which is the y-axis line; the contact is coordinate geometry, not an illegal collision. |
| P324 | G02-G11 | 10 / 1 | EXPECTED_DATA_BOUNDARY_CONTACT | The dashed density begins at the same left plot boundary; no text or arrowhead is obscured. |
| P372 | G06-G09 | 18 / 1 | EXPECTED_DATA_BOUNDARY_CONTACT | The near-zero solid tail meets the y=0 boundary/tick region at the finite plot limit; the density reading remains unambiguous. |
| P401 | G09-G11 | 85 / 3 | EXPECTED_DATA_INTERSECTION | The two Gaussian densities must cross as their relative height changes; solid/dashed encoding and the full curves make all crossings/tail convergence unambiguous. |
| P403 | G09-G13 | 15 / 1 | EXPECTED_REFERENCE_INTERSECTION | The x=0 reference line is defined to pass through the N(0,1) peak. |
| P416 | G11-G13 | 15 / 1 | EXPECTED_REFERENCE_INTERSECTION | The x=0 reference line is defined to pass through the N(0,2^2) peak. |

## Canonical collision and clearance fields

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 2` (only prohibited-pair candidates after semantic prefilter)
- `MASK_CONTAMINATION_PIXEL_COUNT = 2`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`
- `UNRESOLVED_CANDIDATE_COUNT = 0`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 8` (minimum confirmed visible text-to-graphic ink distance; T11 to the visible x-axis segment)
- Minimum visible text-to-text ink distance: 16 px.
- Minimum text bbox-to-figure-crop edge: 34 px.

Manual hard conclusion: no illegal visible-ink overlap, no clipping, and no R168 hard-fail clearance/occlusion condition.
