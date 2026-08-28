# Pair review scope

The denominator was rebuilt from the official R103 PDF as 37 independent visible objects: 16 text objects and 21 graphic objects. `machine/all_unordered_pairs.csv` enumerates every unordered pair exactly once, giving `C(37,2) = 666` rows.

- 120 text-text pairs: exact isolated masks report zero intersection for every row.
- 336 text-graphic pairs: exact isolated masks report zero intersection for every row; the minimum raw mask clearance over all text relations is 10.198px.
- 210 graphic-graphic pairs: 42 rows have nonzero exact-mask intersection and 168 do not.

The 624 zero-intersection rows remain machine facts with `manual_decision=UNSET_BY_MACHINE`; no bulk or default human PASS was injected. Each of the 42 nonzero-intersection rows has its own exact 8x nearest-neighbor card and an individually authored decision and semantic note in `manual_critical_pair_review.tsv`. Their 1,731 total intersecting pixels are all assigned to intended coordinate-frame crossings, contour/guide/trajectory crossings, state-marker endpoint connections, or the long/short principal-axis crossing. No reviewed intersection covers text, hides an arrow direction, creates an unintended node, or changes mathematical meaning.
