# Independent overlap and clipping adjudication

Candidate identity: official R109, physical page 661 / printed page 648, Figure 32.9.

## Denominator

- Semantic text/formula elements: 26 (`S001`-`S026`).
- Semantic graphic objects: 6 (`G001`-`G006`).
- Complete visible-object denominator: 32 objects.
- Complete unordered-pair set: 496 pairs (`32*31/2`), recorded in `unordered_pairs.csv`.
- Explicit manual per-ID judgments: 32/32 objects and 496/496 pairs, recorded separately from machine output.

## Adjudication

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0` for prohibited independent-foreground pair classes after native-pixel, outline, source-coordinate, and all-pair review.
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`.
- `OVERLAP_PIXEL_COUNT = 0`.
- `PIXEL_ADJUDICATION_STATUS = CLEAR`.
- `CLIP_PIXEL_COUNT = 0`.
- `MIN_TEXT_CLEARANCE_PX = 7` from the conservative native-300-dpi external-ink estimate; the closest cases are adjacent text objects and still exceed the 4-pixel text-text threshold. Text-to-line, text-to-border, image-edge, and cross-panel requirements are also satisfied in the opened native view.

The machine bbox table flags 37 coarse rectangle intersections, but none is a native-pixel collision between prohibited independent foregrounds. The causes are intentionally broad semantic bboxes around axes/data, containment inside the right rounded panel, and background coverage. Four non-illegal structural relations are recorded explicitly in `manual_pair_judgments.csv`: two background overlays, one stem-to-axis contact, and one cutoff-boundary-to-axis contact. These are expected chart construction, not text/semantic collisions.

No candidate is `UNRESOLVED`; no pixel-dispute arbitration is required.

