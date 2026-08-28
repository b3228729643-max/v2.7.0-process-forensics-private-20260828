# Overlap and clipping adjudication

- Denominator: 15 objects, 105/105 unordered pairs manually reviewed.
- Pair ledger: `after_overlap_report.csv`.
- Critical native/nearest evidence: ROI01 through ROI06.
- OVERLAP_CANDIDATE_PIXEL_COUNT: `0` after semantic-layer-aware construction.
- MASK_CONTAMINATION_PIXEL_COUNT: `0`.
- OVERLAP_PIXEL_COUNT: `0` illegal visible-ink pixels.
- PIXEL_ADJUDICATION_STATUS: `CLEAR`.
- CLIP_PIXEL_COUNT: `0`.
- UNRESOLVED_PAIR_COUNT: `0`.

Five source-declared marker/chord contacts, P015-P019, are intended geometry: the chord ends at or runs through the five markers. They are not text collisions and are explicitly recorded as `LEGAL_INTENDED_CONTACT`, not suppressed as mask contamination.

The only visually close label/boundary situation is P010. O11 has an opaque white backing in the current source. The native and nearest ROI02 show that the backing interrupts the region boundary before composition; no visible boundary ink crosses the Chinese or mathematical glyph ink. Automated color-separated visible-ink gaps are 8.000 px for E11A and 9.440 px for E11B. This is a directly verified clear case, not an unresolved candidate.

Other critical measured gaps are 49.210 px (x label to x junction), 47.795 px (y label to y junction), 44.222 px (z formula to chord), 23.000 px (y label to Chinese region label), 15.000 px (conclusion formula to border), and at least 25 px from caption ink to the note border. These legacy numerical measurements are advisory under R168; their role here is to support the hard visual finding of no illegal visible-ink overlap or true clipping.
