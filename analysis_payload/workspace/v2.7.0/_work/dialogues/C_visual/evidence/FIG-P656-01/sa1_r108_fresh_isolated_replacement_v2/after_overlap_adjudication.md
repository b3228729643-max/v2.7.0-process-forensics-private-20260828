# FIG-P656-01 overlap and clipping adjudication

## Frozen denominator

- Visible semantic objects: **48** = 25 text/formula objects + 23 graphic objects.
- All unordered pairs: **C(48,2) = 1128**. Every pair is present in `analysis/all_unordered_pairs.csv`; none was assigned a default boolean.
- Visible glyphs: **90** non-whitespace glyphs (98 extracted characters including 8 layout spaces).
- Independent masks: text ink is segmented independently from vector-derived node borders and arrow geometry. Node fill colors and the diagonal category-2 hatch are treated as node background under protocol 9.2.1-F; they are not illegal foreground against the internal digit. Tight per-object masks are under `masks/`; composite masks are under `render/`.

## Pair closure by evidence-backed family

1. **22 intended text-in-node containment pairs.** These are the 18 digit/circle pairs, count formula/count box, warning text/warning box, and the coefficient header and formula/coefficient box. Bounding boxes intersect by intended containment, while independent foreground masks intersect by 0 pixels. Independent-mask text-to-border clearance is 9.000 px minimum (warning); the other contained objects are 16.125--35.000 px.
2. **3 intended arrow-node attachment pairs.** These are the first arrow/count box and the second arrow with its source and target boxes. Source paths and the native 300 dpi 1x/8x ROIs show complete arrowheads, correct direction, and no text contact. Stealth tip back-off produces 7.55--7.80 px raster separation at target borders; this is clean endpoint geometry, not clipping.
3. **1103 positive-bbox-separation pairs.** Every pair has a strictly positive mapped PDF-bbox gap; the exact per-pair gap is recorded. Independent foreground intersection is also 0 for every row.

The three families sum to 1128. Mechanical independent-mask intersection is 0 pixels across all 1128 pairs. Therefore:

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`

## Required clearances and clipping

- Minimum text-text bbox gap: **6.000 px** (coefficient header to coefficient formula), threshold 4 px.
- Minimum text/formula-to-arrow independent-mask gap: **22.472 px**, threshold 3 px.
- Minimum internal text/formula-to-node-border independent-mask gap: **9.000 px**, threshold 5 px.
- Minimum text bbox to frozen standalone crop edge: **16.000 px**, threshold 6 px.
- Adjacent-panel clearance: not applicable; this is one panel.
- No semantic object mask lies outside the frozen figure crop; no semantic object bbox intersects the PDF page boundary. Native views show complete text, formulas, borders, arrows, and markers. `CLIP_PIXEL_COUNT = 0`.

## Nonvisible PDF artifacts

PyMuPDF exposed three pattern/clip extraction records (drawing indices 8, 15, 21; sequence numbers 26, 44, 59) with a spurious rectangle at PDF coordinates `(0, 838.802, 3.088, 841.890)`. They are not visible in the original 200/300 dpi page, lie outside the figure, and correspond to hatch-pattern machinery rather than semantic page objects. They are disclosed in `analysis/nonvisible_pdf_artifacts.json` and excluded from the visible-object denominator. They do not become overlap or clipping candidates.

## Manual inspection basis

The full page, figure-plus-caption, standalone, grayscale, object overlay, independent mask composite, and every native 1x/8x risk ROI were opened before this adjudication. The 8x files are nearest-neighbor magnifications of the frozen native 300 dpi pixels and were used only to inspect pixel topology; all measurements come from the 1x native raster.

