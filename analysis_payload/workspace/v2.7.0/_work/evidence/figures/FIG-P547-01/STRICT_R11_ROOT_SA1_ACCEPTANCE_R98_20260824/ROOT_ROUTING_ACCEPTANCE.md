# FIG-P547-01 root routing acceptance — R98

- Decision: `ROOT_ACCEPTS_SA1_PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL`
- Figure: FIG-P547-01 / 图 30.2 / physical page 591
- Candidate: `strict_current_r98_fullbook/main_full.pdf`
- Candidate SHA256: `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`
- Source SHA256: `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`
- Accepted input: `STRICT_R10_SA1_FRESH_R98_20260824`

## Integrity recount

- Manifest payload rows: 840; actual sealed files: 842 = 840 payload + `MANIFEST.csv` + `WSTOP.txt`.
- Missing, extra, size mismatch, hash mismatch, zero-byte, ADS, post-stop writes: all 0.
- `MANIFEST.csv` SHA256: `D8EF54140646818278B523E3534694A6015184472545D0DD94460E3802E9997B`.
- `WSTOP.txt` SHA256: `755436F4CC026001D218F0D4CCB27B84ABDAAD3F28307D64C854C668AC420D93`; WSTOP is latest.

## Root independent recount

- 193 glyph rows: all threshold PASS; every row opened at native 1x and nearest-neighbour 8x.
- 61 semantic objects = 21 text + 40 graphic; object IDs are unique.
- All unordered semantic-object pairs: `C(61,2)=1830`; unique pair IDs/keys, no self pair, no unknown object, no unconfirmed manual row, illegal-overlap sum 0.
- 71 vector primitives: unique indices, assignment multiplicity exactly 1; 37 internal primitive pairs all PASS.
- 14 source-anchored endpoint rows all PASS.
- Actually opened register: 337 = 193 glyph + 40 graphic + 94 critical-pair + 10 global views; not-opened count 0.
- 21 font rows and 40 line-width/arrow rows all PASS.

## Root native-pixel visual review

Root opened every one of the following at original image detail:

- 22 glyph-card sheets (native 1x raw boxes and nearest-neighbour 8x masks);
- 7 graphic-card sheets;
- 8 critical-pair sheets;
- full page/crop/standalone views in color and gray;
- protanopia, deuteranopia, and tritanopia simulations;
- 61-object bounding-box overlay and the 61x61 all-pairs matrix.

Observed result on the book figure itself: no illegal text-text, text-graphic, or graphic-graphic overlap; no clipping; no broken glyph; no abrupt or locally oversized font; no undersized meaningful glyph; and no ambiguous arrow endpoint. The node/arrow and arrow/bridge contacts shown in the critical cards are intentional source-anchored endpoint contacts, not acceptance exceptions.

Measured hard minima accepted by root: base text 9.8 pt, node text 10.2 pt, core formula 11.6–12 pt (ratio <= 1.18), minimum text/line 4 px, text-text clearance 20.26 px, node-border clearance 37.949 px, image-edge clearance 12 px, adjacent-panel clearance 30.017 px.

The evidence-sheet explanatory headings are a dense contact sheet and are not book output; their compact layout was not used to waive any actual-figure defect. The full figure, page context, object boxes, and critical-pair crops were inspected separately.

## Denominator reconciliation

The current fresh schema deliberately separates 193 glyph instances from the semantic denominator of 61 objects and its 1830 all-pairs set. The earlier local SA2 schema counted 193 glyph instances plus 65 graphic/path items as 258 objects and 33153 pairs. The denominator change is not an omission: the fresh evidence closes all 21 text semantic objects, all 40 graphic semantic objects, and maps all 71 vector primitives exactly once.

## Routing

SA1 is accepted only as an independent-role PASS. FIG-P547-01 must now receive a fresh isolated SA3 review using R98 and the source, with no access to prior P547 evidence, status, or root conclusions. This record does not constitute final figure acceptance and does not count the figure as complete.
