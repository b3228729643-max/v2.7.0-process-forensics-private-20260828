# FIG-P157-01 R111 draw-order, occlusion, clearance, and clipping audit

Candidate: `main_full.pdf`, physical PDF page 170 / printed page 157. All pixel statements below use the direct native 300 dpi page grid (2481×3508), with no raster resize.

## Authored and emitted order relevant to occlusion

The current source was read directly. The region fills are authored at lines 30--32, training curve `O-G001` at lines 33--34, validation curve `O-G002` at lines 35--37, vertical reference at lines 38--39, marker at lines 40--41, and training leader at lines 42--43. The emitted PDF order establishes `O-G001` before `O-G002`; the current content-group replay records that order independently in `r111_curve_raw_recheck_v2/R111_CURVE_RAW_RECHECK.json`.

The text node backgrounds for E002, E003, and E004 are source-declared at lines 47--52 with `fill opacity=.90`; they are semitransparent halos, not true opaque erasers. Therefore they were explicitly excluded from the final-visible subtraction rule. Later true-opaque external objects were individually enumerated and may be subtracted from the corresponding curve raw mask only; their union intersects the `O-G001`/`O-G002` raw intersection by 0 pixels.

For the curve pair, each mask was replayed against the identical prefix/background in the same coordinate system. No peer curve was removed, and no dilation, erosion, resampling, or difference-based edge deletion was applied. This prevents the earlier invalid “removal contribution” approach from contaminating either curve's boundary.

| Relation | Draw-order conclusion | Final-visible raw-mask result |
| --- | --- | --- |
| `O-G001` training versus `O-G002` validation | training is emitted before validation; they remain semantically independent | 139 px intersection, clearance 0 → FAIL |
| later true-opaque external objects versus pair intersection | later opaque objects do not cover the pair intersection | 0 px removed from the 139 px intersection |
| semiopaque halos `O-H001..O-H003` | opacity .90 means no false opaque clearing is permitted | excluded from subtraction |
| nine actual contact/connection ROIs | reviewed in the dedicated 1×/8× manual ledger | P0156/157/160/167/169/181/182/188 intentional; P0155 unapproved |

The 139 px is the only canonical count. The unverified 516 px assertion is retracted because it was not established by the R111 method. The earlier 37 px removal-contribution number is also retracted because subtracting/re-rendering relative to the peer curve changes edge ownership and is not a pair of independent raw final-visible masks.

## Clip and clearance closure

`R111_CLIP_FINAL_ADJUDICATION.csv` closes 20 object rows: every crop-edge and PDF-page foreground count is 0, and every text row passes the required 6 px crop-edge condition. The smallest text-to-crop clearance is 29 px (E011), above 6 px.

`R111_MANDATORY_RELATION_FINAL_ADJUDICATION.csv` has 154/154 mandatory relations PASS. Across text-related pair rows, the observed minimum final clearance is 16 px (E003 to `O-G009`), above the 3 px text-to-graphic requirement; all text-text and text-graphic illegal-overlap counts are 0. The zero-clearance connections in the graphic-only rows are enumerated as intentional endpoint connections, except P0155.

## Gate result

- `DRAW_ORDER_EVIDENCE_PASS=true`: order, opacity treatment, and raw-mask provenance are reproducible.
- `CLIP_PASS=true`, `CLIP_PIXEL_COUNT=0`, `MIN_TEXT_CLEARANCE_PX=16`.
- `INDEPENDENT_CURVE_OVERLAP_HARD_GATE=false`: P0155 is an unapproved final-visible collision and remains a figure hard failure.
