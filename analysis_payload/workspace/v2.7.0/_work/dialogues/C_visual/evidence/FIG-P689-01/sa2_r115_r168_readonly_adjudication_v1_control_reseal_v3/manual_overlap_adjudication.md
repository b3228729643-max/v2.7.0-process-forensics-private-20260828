# Manual visible-ink overlap and clipping adjudication

This adjudication was written only after all required native, grayscale, overlay, and native1x/nearest8x ROI views were opened. The exact denominator is 31 objects and 465 unordered pairs. `manual_pair_ledger.txt` contains one post-observation verdict token for every pair; its verdict-free comparator is `pair_index_no_verdict.csv`.

## Legal compositional contacts or underlays (13 pairs)

- `G03--G04`: the two semantic fill regions meet at their shared decomposition boundary.
- `G03--G05`, `G04--G05`: pale semantic fills intentionally extend beneath the evidence bar outline; fills are background, not competing foreground ink.
- `G03--G06`, `G04--G06`: the divider is intentionally drawn over both semantic backgrounds.
- `G03--T03`, `G04--T04`: labels are intentionally printed over their pale semantic background fills; neither fill is foreground ink.
- `G05--G06`: divider endpoints intentionally join the outline.
- `G08--G09`: x and y axes meet at the origin.
- `G09--G10`, `G09--G11`: the first data value at update 0 is intentionally located on the y-axis; curve/marker contact expresses its coordinate.
- `G09--G12`: the upper-bound reference begins at the y-axis.
- `G10--G11`: solid staircase and circular marks intentionally coincide as line+mark double encoding of one series.

These contacts are semantically required and do not obscure, replace, or corrupt any independent reader-visible foreground.

## Critical clear pairs

- `G12--T08`: their geometric boxes are conservative and overlap, but the actual dashed-line ink occupies crop rows 110--112 and the first orange text ink begins at row 141 in the shared 300 dpi crop, leaving 28 fully blank rows. ROI02 native1x and nearest8x confirm no contact.
- `G10/G11--T09`: the solid marked staircase remains well above and to the left of the local-point annotation; ROI03 native1x and nearest8x show white separation throughout.
- `G08--T10..T16` and `G08--T17`: all tick labels and the axis title are separated from axis/tick ink; ROI04 confirms the smallest labels are intact.
- `G05/G06--T03/T04`: both bar labels remain inside their regions without meeting outline or divider ink; ROI01 confirms the junctions.
- `T18--T19`: caption number and caption body are adjacent but have separate ink; ROI07 confirms no collision.
- `G01--G02` and all cross-panel content pairs: ROI08 confirms a clear inter-panel gutter and complete rounded borders.

All other matrix cells are visibly remote or clearly separated in the native image and overlays.

## Canonical counts

- `OVERLAP_CANDIDATE_PIXEL_COUNT=0` after complete manual source-coordinate and native-pixel adjudication; legal compositional contacts above are not illegal-overlap candidates.
- `MASK_CONTAMINATION_PIXEL_COUNT=0`.
- `OVERLAP_PIXEL_COUNT=0` confirmed illegal visible-ink pixels.
- `PIXEL_ADJUDICATION_STATUS=CLEAR`.
- `CLIP_PIXEL_COUNT=0` confirmed clipped visible pixels.
- `OBSERVED_MIN_TEXT_CLEARANCE_PX=12` (conservative manual minimum among title/border and tick/axis neighborhoods; R168 treats the legacy numeric threshold as advisory, and every such neighborhood is actually readable and non-touching).

No pair is `UNRESOLVED`.
