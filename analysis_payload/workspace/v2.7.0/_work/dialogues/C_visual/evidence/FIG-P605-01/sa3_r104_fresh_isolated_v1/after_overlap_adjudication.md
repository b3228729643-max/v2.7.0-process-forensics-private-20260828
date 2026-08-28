# FIG-P605-01 / R104 / SA3 overlap adjudication

- Reviewer: SA3 fresh isolated
- HANDOFF_ID: `C-FIG-P605-01-R104-SA3-FRESH-ISOLATED-V1`
- Official PDF: `main_full.pdf`, physical page 658 (printed 645)
- Native measurement grid: 300 dpi, 2481×3508 px page
- Atomic foreground objects: 173
- Complete unordered pair denominator: 14,878 = C(173,2)
- Machine candidate pairs: 13
- Candidate intersection pixels: 224
- Confirmed mask-contamination pixels: 0
- Confirmed illegal-overlap pixels: 0

I opened every candidate’s `ORIGINAL / A MASK / B MASK / INTERSECTION / OVERLAY` evidence at native 1× and 8× nearest-neighbour. The four text candidates are internal kerning/anti-alias seams inside the natural roman subscripts `sys` and `rand`; all constituent letters remain complete and independently readable. Six candidates are line-to-own-arrowhead seams. Two are node-border-to-outgoing-line anchors, and one is the diamond-to-branch anchor. These are the intended geometric connections represented by the source, not intersections between independent semantic foreground objects.

No candidate involves text/formula against an unrelated line, marker, border, arrowhead, panel edge, or another independent text object. The full adjudication is row-specific in `manual_candidate_pair_review.csv`; every row references its own 1× and 8× ROI bundle.

Under R168, the 1–4 px same-formula seams are advisory typography detail, and the structural seams are legal design connections. Therefore:

- `OVERLAP_CANDIDATE_PIXEL_COUNT=224`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `PIXEL_ADJUDICATION_STATUS=PASS`

