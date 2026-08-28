# Manual overlap adjudication

Reviewer: SA1 fresh isolated v1. Evidence opened: all 16 critical contact sheets, their native-1x originals, and nearest-neighbor-8x overlays. The frozen denominator is 177 visible objects and all 15,576 unordered pairs; 154 machine-selected critical relations were manually adjudicated per ID in `manual_critical_relation_ledger.csv`.

Fourteen pairs have at least one common foreground pixel. None is an illegal semantic collision. Nine are graph-edge endpoint joins to node borders, one is the arrow-shaft/arrowhead join, three are graph edges intentionally crossing dashed Markov-blanket boundaries, and one is a single antialias pixel between adjacent `k` and `o` glyph masks inside the intact word `Markov`. The last contact does not obscure either letter and is normal internal typography rather than a collision between independent semantic objects.

The remaining independent critical relations are disjoint. The nearest independent text pair is 33.0151 native pixels apart; nearest text-to-node-border ink clearance is 15 pixels; nearest text-to-line clearance is 20 pixels. No text, formula, or annotation path is intersected illegally. Manual hard-overlap result: PASS.
