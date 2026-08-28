# Accepted R100 failure to R7 local-SA2 regression ledger

The before evidence is the accepted fresh-SA1 R100 package. R7 is a direct standalone build, so it is independently re-rendered and audited; no R100 mask, PASS row, or screenshot is reused as current evidence.

| Gate | Accepted R100 before | R7 after | Decision |
|---|---:|---:|---|
| Object universe | 116 = 95 glyph + 21 graphic | 116 = 95 glyph + 21 graphic | PASS, identical ID set |
| Unordered pairs | 6,670/6,670 | 6,670/6,670 | PASS |
| Object machine failures | `FRM_TRIAL_005` | none | repaired |
| Pair machine failures | none | none | no regression |
| Empty masks | 0 | 0 | no regression |
| Illegal independent overlap px | 0 | 0 | no regression |
| Final raw overlap px | 0 | 0 | no regression |
| Clip px | 0 | 0 | no regression |
| Mask contamination px | 0 | 0 | no regression |
| `FRM_TRIAL_005` native height | 21px / floor 22px | 22px / floor 22px | repaired exactly |
| `FRM_TRIAL_005` pre/final area | 262/262px | 297/297px | complete; ownership loss 0 |
| `FRM_TRIAL_005` missing/foreign/clip | 0/0/0 | 0/0/0 | no regression |
| Independent text bbox clearance | 8px / floor 4px | 8px / floor 4px | PASS |
| Own-node text-border clearance | 18px / floor 5px | 17px / floor 5px | PASS, ample margin |
| Text-line/arrow clearance | 26px / floor 3px | 27px / floor 3px | PASS |
| Text-math-rule clearance | 70px / floor 3px | 71px / floor 3px | PASS |
| Text-other-node-border clearance | 5px / floor 3px | 5px / floor 3px | PASS |
| Formula-rule-own-border clearance | 118px / floor 5px | 118px / floor 5px | PASS |
| Low-profile punctuation | 0 / N/A | 0 / N/A | unchanged |

The fullbook and standalone wrapper place the same figure at a small global horizontal phase difference, so R7 does not claim byte-identical old/new raster masks. Instead every current object and every current pair is regenerated on R7's own native 300dpi grid, and all strict floors, overlap, ownership, clip, clearance, 1x/8x, four-view, semantic, and visual-harmony gates are rerun. The source diff proves that no coordinate, node dimension, edge, or non-target content was edited.
