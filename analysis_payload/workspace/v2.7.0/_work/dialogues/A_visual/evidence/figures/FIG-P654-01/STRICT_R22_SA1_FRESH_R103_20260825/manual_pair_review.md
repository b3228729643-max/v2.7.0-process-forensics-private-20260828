# Manual pair review — FIG-P654-01 / R103 / physical page 704

Reviewer: `/root/p654_r103_fresh_sa1`  
Review time: `2026-08-25T17:50:23+08:00`  
Coordinate system: direct official-PDF 300 dpi crop `[292,250,2234,900]`, native `1942×650`; all critical panels are 8× nearest-neighbour presentations of native 1× masks.

## Complete denominator

- Objects: `93 GLYPH + 8 NODE_BORDER + 7 RELATION + 1 MATH_RULE = 109`.
- I opened `overlays/complete_pair_matrix.png` and visually traced the full symmetric matrix.
- Unordered pairs: `C(109,2)=5886`; the diagonal is excluded from the denominator.
- Machine class totals independently sum to 5886: 3680 independent text–text, 651 text–relation, 91 text–own-node-border, 653 text–other-node-border, 84 text–other-math-rule, 598 intra-parent glyph integrity, 42 independent border–relation, 64 remaining graphic pairs, 9 same-formula rule pairs, and 14 relation-endpoint pairs.
- Matrix colors observed: ordinary PASS cells green, the 23 semantic design pairs blue, diagonal gray; no red hard-failure cell and no amber near-threshold cell was present.

## Critical class A — fraction rule

I opened critical sheets 01–03 and reviewed all nine pairs `T057–T065 ↔ G016` individually. The numerator and denominator glyphs are intact, the rule is a separate pure path, and every pair has intersection 0. Native clearances are 16px for the base glyphs/operators, 6px for each italic `i` subscript, and 29px for subscript `0`. These are correct components of the same formula, with no glyph damage or semantic ambiguity.

## Critical class B — seven relation endpoints

I opened critical sheets 03–06 and reviewed all fourteen node-border endpoint pairs. `G009–G015` correspond one-to-one to the seven source relations. Intersections of 3–10 pixels occur only where a source path intentionally begins on a node border; four arrow-tip arrivals retain 3px raster clearance because of the rendered arrowhead geometry. No relation intersects unrelated text, marker, node, or relation.

Pairs reviewed: `G001–G009`, `G002–G010`, `G003–G009`, `G003–G010`, `G003–G011`, `G003–G013`, `G004–G011`, `G004–G012`, `G004–G014`, `G005–G012`, `G005–G015`, `G006–G013`, `G007–G014`, `G008–G015`.

## Non-design hard classes

All non-design pairs pass. Native class minima are: independent text–text 47.0416px (threshold 4), text–relation 24.2982px (threshold 3), text–own-node-border 18px (threshold 5), text–other-node-border 18px (threshold 3), and text–other-math-rule 69px (threshold 3). Illegal overlap pixel count is 0.

## Manual conclusion

`PAIR_MATRIX_MANUAL_PASS=true`. The complete denominator is closed; the 23 blue cells are justified same-formula or source-endpoint design relations, and there is no real clipping, collision, or unclassified interaction.
