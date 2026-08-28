# FIG-P092-01 manual overlap adjudication

- Reviewer: `A-R114-P092-SA3-FRESH-ISOLATED-20260828`
- Denominator: 13 reader-visible IDs, 78 unordered text pairs.
- Native evidence opened: official 300 dpi full page and figure crop, 300 dpi grayscale, 300 dpi object overlay, plus native1x and nearest8x peak/left-endpoint/right-endpoint ROIs.
- Text-text result: every pair is recorded in `manual_pair_ledger.csv`; all 78 have disjoint visible ink and no illegal overlap.
- Text-graphic result: curve, markers, guides, axes, annotations, formula, ticks, and caption were inspected in the native views. No reader-visible ink is shared in a way that clips, occludes, changes a symbol, or impairs reading.
- Conservative color-mask proximity: the smallest text-to-blue-graphic separation reported by the mechanical color check is 1 px at the maximum label/peak region. The native1x and nearest8x ROI shows separation, not shared ink, and the label remains unambiguous. Under R168 the old micro-clearance number is advisory and cannot alone cause FAIL.
- Clip result: the official full page contains every arrowhead, marker, glyph, and caption character. `CLIP_PIXEL_COUNT=0` refers to the official page, not the deliberately bounded evidence crop.

Canonical adjudication:

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- `CLIP_PIXEL_COUNT = 0`
- `PIXEL_DISPUTE_REQUIRED = false`
