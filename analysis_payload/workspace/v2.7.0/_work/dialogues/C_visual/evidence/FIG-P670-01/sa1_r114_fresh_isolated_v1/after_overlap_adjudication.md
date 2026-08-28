# After-overlap adjudication

Reviewer: SA1, gpt-5.6-sol, xhigh

Actual opened evidence: native full-page 300 dpi, native figure crop 300 dpi, grayscale 300 dpi, final semantic-object overlay, native 1x ROI, nearest-neighbor 8x ROI.

Frozen denominator:

- Visible semantic objects: 16 (`OBJ01` through `OBJ16`).
- Required unordered pairs: `16 * 15 / 2 = 120`.
- Manual object rows present: 16/16.
- Manual unordered-pair rows present: 120/120.
- Pair-ID and object-key difference against the mechanical combination index: 0.

Focused adjudications:

- `PAIR019` (`OBJ02`/`OBJ06`) and `PAIR077` (`OBJ07`/`OBJ09`) have intersecting rectangular envelopes because each arrow object combines a high label with a lower arrow shaft. The intersection lies in empty space; the original 300 dpi visible inks are disjoint. These are bbox-envelope false positives, not pixel-mask contamination and not collisions.
- `PAIR055` and `PAIR056` are the intended incoming/outgoing arrow endpoint connections at the observation-node border. Neither arrow touches node text; the connection is required by the diagram semantics and is not an illegal overlap.
- The probability bars, formulas, titles, count rows, takeaway box, caption label, and three caption lines have separated visible ink. Close vertical neighbors retain clear whitespace and do not obscure reading order.

Canonical result:

- BBOX_ENVELOPE_CANDIDATE_COUNT=2
- OVERLAP_CANDIDATE_PIXEL_COUNT=0
- MASK_CONTAMINATION_PIXEL_COUNT=0
- OVERLAP_PIXEL_COUNT=0
- UNRESOLVED_PAIR_COUNT=0
- PIXEL_ADJUDICATION_STATUS=CLEAR
- CLIP_PIXEL_COUNT=0
- MIN_TEXT_CLEARANCE_PX=9

`MIN_TEXT_CLEARANCE_PX=9` is a conservative 300 dpi mapping of the smallest relevant PDF-bbox gap; under R168 it is supporting evidence rather than a stand-alone numeric gate. Native pixels show no unreadability, obscuration, or illegal visible-ink contact.

