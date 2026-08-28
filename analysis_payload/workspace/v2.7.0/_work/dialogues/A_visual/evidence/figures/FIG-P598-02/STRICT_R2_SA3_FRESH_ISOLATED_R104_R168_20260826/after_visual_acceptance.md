# FIG-P598-02 strict R104/R168 SA3 visual acceptance

## Candidate identity

- Figure UID: `FIG-P598-02`
- Role: fresh isolated SA3
- HANDOFF_ID: `A-R104-P598-02-SA3-FRESH-ISOLATED-20260826`
- Frozen PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- Physical page: 650 of 817
- PDF bytes: 4,967,222
- PDF SHA-256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- Page size: 595.276 × 841.890 pt (A4)
- Native 300 dpi grid: 2481 × 3508 px
- Lower-resolution whole-page context: 1654 × 2339 px at 200 dpi
- Figure-plus-caption crop: integer page pixels `[283,266,2243,942]`, 1960 × 676 px
- Figure-only crop: integer page pixels `[458,266,2072,801]`, 1614 × 535 px

## Complete denominator

- Visible non-whitespace glyphs: 137
- Foreground graphics: 26, including three card borders, two node borders, four kernel arrow components, baseline, curve, dashed divider, hatch pattern, seven retained-sample dots, widehat rule, fraction rule, and four inter-card flow-arrow components.
- Total objects: 163, all unique, all nonempty, all with ordinary safe PNG masks.
- All unordered pairs: `163×162/2 = 13,203`; actual ledger rows 13,203; duplicates 0.
- Final-visible shared pixels across all pairs: `OVERLAP_PIXEL_COUNT=0`.
- Crop clipping across all objects: `CLIP_PIXEL_COUNT=0`.

## Hard geometry gates

| Gate | Measured minimum | Required | Result |
|---|---:|---:|---|
| Different-parent text/text bbox | 28 px | 4 px | PASS |
| Text to node/card border raw ink | 17.0278 px | 5 px | PASS |
| Text to line/arrow/marker raw ink | 20.0238 px | 3 px | PASS |
| Text to crop edge | 24 px | 6 px | PASS |
| Any object to crop edge | 17 px | no clipping | PASS |

The zero-clearance relations in `REL11`–`REL14` and `REL16` are intentional component continuity or mathematical/plot composition. Paint-order-separated final-visible masks have zero shared pixels. Each relation was opened at 1× and 8× nearest-neighbour and manually adjudicated.

## Typography under R168

The source declares 9.2 pt general nodes, 9.4 pt bold headings, and 8.6 pt notes/segment labels, with no graphics scaling or transform-shape reduction. Native glyph measurements and the historical thresholds remain in `after_pixel_measurements.csv`; five rows are below the old numeric advisory and seven are low-profile punctuation. Under the assigned R168 rule these fine size/taxonomy/ratio and 1–2 px matters are advisory.

No hard R168 font failure was observed: no missing glyph, tofu, wrong codepoint, wrong mathematical meaning, genuinely unreadable content, obvious severe visible imbalance, real clipping, or real overlap. The headings, formulas, annotations, scripts, punctuation, widehat, fraction rule, and caption are visually complete and readable in color and grayscale.

`FONT_VISUAL_HARMONY_PASS=true`

## Semantic and relationship checks

- Three ordered cards are present and labeled `1 构造核`, `2 运行链`, `3 遍历平均`.
- Exactly two rightward flow arrows connect 1→2 and 2→3.
- Step 1 contains `πK=π`, distinct `x/y` states, two opposed transition arrows, and `保持目标分布 π`.
- Step 2 contains a continuous chain curve, visible hatched warm-up region, dashed divider, baseline, `warm-up`, and `保留段`.
- Step 3 contains seven retained-sample dots, `\widehat I_{m,n}=\frac1n\sum_{t=m+1}^{m+n}h(X_t)`, and `只用保留样本`.
- Caption meaning agrees and ends with estimation of `E_π[h(X)]`.
- Curve, pattern, dashed divider, dots, cards, arrows, widehat, fraction line, caption, crop, clearances, continuity, grayscale, and full-page integration all pass visual inspection.

## Evidence actually opened

- Five view rows in `manual_view_reviewer.csv` plus the labeled overlay and two matrices.
- All 19 final object contact sheets covering every one of the 163 objects.
- Both all-pair matrices.
- All 16 critical/relationship overlays.
- Every object has its own manual reviewer row; every relationship has its own manual reviewer row. No script generated or overwrote the reviewer, boolean, decision, or note fields.

## Final decision

`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`
