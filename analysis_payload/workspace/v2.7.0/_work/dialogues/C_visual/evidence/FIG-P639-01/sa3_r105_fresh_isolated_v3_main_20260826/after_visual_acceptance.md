# FIG-P639-01 R105 fresh isolated SA3 visual acceptance

## Verdict

`PASS`

Under the current R168 adjudication, the point-size, micro-height, same-color calibration, and 1.08 ratio observations are advisory. The actual visible hard gates all pass.

## Candidate identity and closure

- Official PDF: 817 pages, 4,967,209 bytes, SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`.
- Physical page 689 / printed page 676; native 300 dpi page grid `2481 x 3508`; figure crop `[380,1350,1695,720]`.
- Four required views, five 100%-coverage glyph contact sheets, and five critical 8x pair overlays were actually opened before the corresponding manual ledgers were written.
- Visible-object denominator: `N=80` = 72 visible non-space glyphs + 8 graphic/path objects.
- All unordered pairs: `C(80,2)=3160`; actual pair rows `3160/3160`.
- Empty masks 0; `CLIP_PIXEL_COUNT=0`; true illegal `OVERLAP_PIXEL_COUNT=0`.
- Five raw intersections totaling 81 pixels are designed graph geometry: axis origin/endpoints and the two mean guides terminating on their own curves. Each has separated raw masks, 1x/8x evidence, and an individual manual row.
- Minimum independent text-text / text-graphic / note-text-to-border / text-to-crop-edge clearances are 13 / 16 / 19 / 23 px.

## Actual hard gates

| Hard gate | Result | Evidence |
|---|---|---|
| Missing/tofu/wrong glyph | PASS | none in any opened view or 72/72 glyph sheets |
| Mathematical semantics | PASS | `1-rho^2=0.64`, `rho*b=0.45`, `rho*a=0.60`; caption and curves agree |
| Actual unreadability | PASS | every plotted label, tick, axis title, and note is readable at native crop inspection |
| Visually gross imbalance | PASS | `FONT_VISUAL_HARMONY_PASS=true`; no disruptive scale, crowding, or hierarchy problem |
| Crop | PASS | no visible object is clipped; minimum text-edge clearance 23 px |
| True illegal overlap | PASS | final-visible separated raw masks yield illegal overlap 0 |

Grayscale differentiation and page integration independently pass. The solid/dashed encodings remain distinct in grayscale, and the figure sits naturally between the introducing sentence and caption.

## R168 advisory disclosure

- Source sizes are 8.5 pt for ticks and 9.2 pt for the other plotted text roles.
- Both minus signs measure 4 px, both equals signs 13 px, and low-stroke CJK `一` 4 px under the legacy per-glyph classification.
- Two color-specific commas and the black note decimal point lack a second same-color peer calibration glyph.
- Including low-stroke `一` gives the note-CJK role group an 8.5 extreme ratio.
- PDF-extracted 8.966/9.166 bp differences are also advisory.

These observations are fully preserved in the raw CSVs and contact sheets; none constitutes an independent hard FAIL under current R168.

## Final matrix

| Gate | Result |
|---|---|
| Identity / four-view opening | PASS |
| Denominator / all unordered pairs | PASS |
| Mask mapping and purity | PASS |
| Missing/tofu/wrong glyph | PASS |
| Math semantics and caption consistency | PASS |
| Actual readability / visual balance | PASS |
| Crop / true illegal overlap | PASS |
| Grayscale / page integration | PASS |
| R168 micro-typography observations | ADVISORY |
| Overall SA3 | **PASS** |

