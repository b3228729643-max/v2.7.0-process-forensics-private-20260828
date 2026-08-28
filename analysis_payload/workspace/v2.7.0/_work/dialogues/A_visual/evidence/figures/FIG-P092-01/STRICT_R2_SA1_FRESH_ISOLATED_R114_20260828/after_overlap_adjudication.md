# FIG-P092-01 overlap and clipping adjudication

- Reviewer identity: `A-R114-P092-SA1-FRESH-ISOLATED-20260828` / `/root/p092_r114_fresh_sa1`
- Official artifact: R114 physical PDF page 96, rendered directly at 300 dpi.
- Frozen denominator: 21 reader-visible objects.
- Frozen unordered pairs: 210, each reviewed in `manual_pair_ledger.csv` after opening native/full/crop/grayscale/overlay/native1x/nearest8x evidence.

Manual pair classification is complete: 194 pairs are visually separate; 11 are deliberate structural/data/reference contacts; 2 use white annotation backgrounds to keep glyph ink separate from the nearby entropy curve; and 3 are close but visibly separate in the nearest-neighbor 8x view. No pair contains illegal shared reader-visible ink.

The deliberate contacts are axis-axis, tick-marker registration, curve-marker registration, and guide/curve/marker registration at the mathematical reference point. They encode the geometry rather than obscure it. The certainty labels use an opaque white backing, so the curve does not pass through their glyph ink. The maximum annotation, horizontal guide, and symmetry formula retain visible gaps from adjacent objects in the 8x replication.

No glyph, curve segment, arrowhead, guide stroke, marker, axis stroke, tick, caption component, or page boundary is clipped. No unresolved candidate remains.

- `ILLEGAL_VISIBLE_INK_OVERLAP = 0`
- `TRUE_CLIPPING = 0`
- `UNRESOLVED_PAIR_COUNT = 0`
- `ADJUDICATION_STATUS = CLEAR`
- `MANUAL_VERDICT = PASS`

R168 was applied: historical numeric/microgrid thresholds were not treated as hard-fail gates. The conclusion rests on the current PDF's actual visible ink, readability, geometry, and meaning.
