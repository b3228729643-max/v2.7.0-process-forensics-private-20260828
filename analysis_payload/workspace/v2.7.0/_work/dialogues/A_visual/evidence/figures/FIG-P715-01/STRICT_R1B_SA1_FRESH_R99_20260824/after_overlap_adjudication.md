# FIG-P715-01 — native-pixel critical-pair adjudication

Candidate: frozen official R99, physical PDF page 763 / printed page 750. All measurements below use the native 300 dpi page grid. `all_pairs.csv` is the complete unordered denominator: **N=298**, **C(N,2)=44,253**, with 20 individually opened critical-pair ROIs.

## Method and scope

Each listed image in `critical_pairs/` was actually opened in the native-1× upper view and nearest-neighbour-8× lower view. Red/blue are the two final-visible raw masks; yellow is their native intersection. Counts always come from the 1× masks. The 8× panes were visual confirmation only and did not contribute pixels or distances.

`TEXT_TEXT_BBOX_GATE` is applied only where the strict protocol explicitly requires the independent text/vector-bbox clearance floor. It is never counted as raw-ink overlap. Thus the three `TRUE_CLEARANCE_FAILURE` rows below have zero raw intersection and remain distinct from the sixteen `TRUE_COLLISION` rows.

## Result

- 19 non-whitelisted critical pairs fail.
- 16 are genuine raw-mask collisions, totalling **943** native 300-dpi intersection pixels.
- 3 are clearance-only failures: `PAIR13583`, `PAIR14857`, and `PAIR14859`.
- `PAIR28512` is a nearest/control relation that passes all applicable gates.
- There is no mask-contamination adjudication or waiver: `MASK_CONTAMINATION_PIXEL_COUNT=0` and the real collisions remain real independent-object collisions.

| Pair | Adjudication | Why it fails or passes | Evidence |
|---|---|---|---|
| PAIR09761 | TRUE_COLLISION | `G0035` ordinary note intersects node-J border, 82px | `critical_pairs/PAIR09761_G0035_P0004.png` |
| PAIR13583 | TRUE_CLEARANCE_FAILURE | text-to-panel raw clearance 4px < 6px; no raw overlap | `critical_pairs/PAIR13583_G0050_P0001.png` |
| PAIR14125 | TRUE_COLLISION | independent formula glyphs intersect, 3px | `critical_pairs/PAIR14125_G0053_G0060.png` |
| PAIR14857 | TRUE_CLEARANCE_FAILURE | masks 1px apart and text bbox clearance 0px < 4px | `critical_pairs/PAIR14857_G0056_G0063.png` |
| PAIR14859 | TRUE_CLEARANCE_FAILURE | masks separated 31.06445px, but independent-text bbox clearance 0px < 4px | `critical_pairs/PAIR14859_G0056_G0065.png` |
| PAIR15100 | TRUE_COLLISION | independent formula glyphs intersect, 2px | `critical_pairs/PAIR15100_G0057_G0065.png` |
| PAIR28512 | PASS_CONTROL | masks separated; bbox clearance 7px >= 4px | `critical_pairs/PAIR28512_G0121_G0133.png` |
| PAIR31998 | TRUE_COLLISION | right note / matrix-P border, 70px | `critical_pairs/PAIR31998_G0141_P0034.png` |
| PAIR32154 | TRUE_COLLISION | right note / matrix-P border, 120px | `critical_pairs/PAIR32154_G0142_P0034.png` |
| PAIR32309 | TRUE_COLLISION | right note / matrix-P border, 95px | `critical_pairs/PAIR32309_G0143_P0034.png` |
| PAIR32310 | TRUE_COLLISION | right note / matrix-P border, 73px | `critical_pairs/PAIR32310_G0143_P0035.png` |
| PAIR32464 | TRUE_COLLISION | right note / matrix-P border, 120px | `critical_pairs/PAIR32464_G0144_P0035.png` |
| PAIR32617 | TRUE_COLLISION | right note / matrix-P border, 85px | `critical_pairs/PAIR32617_G0145_P0035.png` |
| PAIR32618 | TRUE_COLLISION | right note / matrix-P border, 83px | `critical_pairs/PAIR32618_G0145_P0036.png` |
| PAIR32770 | TRUE_COLLISION | right note / matrix-P border, 45px | `critical_pairs/PAIR32770_G0146_P0036.png` |
| PAIR32921 | TRUE_COLLISION | right note / matrix-P border, 36px | `critical_pairs/PAIR32921_G0147_P0036.png` |
| PAIR33071 | TRUE_COLLISION | right note / matrix-P border, 30px | `critical_pairs/PAIR33071_G0148_P0036.png` |
| PAIR33220 | TRUE_COLLISION | right note / matrix-P border, 55px | `critical_pairs/PAIR33220_G0149_P0036.png` |
| PAIR35742 | TRUE_COLLISION | independent formula glyphs intersect, 22px | `critical_pairs/PAIR35742_G0168_G0172.png` |
| PAIR36003 | TRUE_COLLISION | independent formula glyphs intersect, 22px | `critical_pairs/PAIR36003_G0170_G0176.png` |

This is a geometrical strict-gate failure independent of the CJK `一` pixel-height failure. No source was edited and no LaTeX build was started.
