# FIG-P654-01 — fresh isolated SA1 visual acceptance on official R103

- Handoff: `A-R103-P654-SA1-FRESH-20260825`
- Reviewer instance: `/root/p654_r103_fresh_sa1`
- Candidate: official `R103`, physical page `704`
- PDF identity: 817 A4 pages, 4,967,184 bytes, SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- Native page: `595.276001×841.890015 pt`; 300 dpi `2481×3508 px`; 200 dpi `1654×2339 px`
- Figure crop: full-page integer `[292,250,2234,900]`, native `1942×650 px`
- Standalone crop: `[310,273,2218,900]`, native `1908×627 px`

## Source and object closure

The read-only source declares general/node/application text at 10.1pt and formula/count roles at 11.6pt, with no graphics scaling. Extracted PDF sizes are 10.062270/10.162395pt and 11.556670pt; the tiny metadata differences are R168 advisory-only and do not alter codepoints, geometry, or readability.

All visible content is closed: 93 glyphs, eight final-visible node borders, seven semantic relations, and one predictive fraction rule. All 21 figure-region PDF drawing/path records map to the 16 semantic graphic objects. Every ordinary mask PNG and object JSON has a unique safe filename.

## Actual four-view review

| View | Native dimensions | Manual result |
|---|---:|---|
| full page 200 dpi | 1654×2339 | PASS — figure scale and page hierarchy are natural; no crowding with caption or prose. |
| figure crop 300 dpi | 1942×650 | PASS — complete, sharp, collision-free and unclipped. |
| standalone 300 dpi | 1908×627 | PASS — all graph objects remain fully visible. |
| grayscale 300 dpi | 1942×650 | PASS — node hierarchy, seven relations, formula and labels remain legible. |

`FONT_VISUAL_HARMONY_PASS=true`. No glyph is tofu, substituted, unreadable, severely imbalanced, clipped, or overlapped. Gamma’s Latin face and the math fonts are visibly compatible with the CJK labels; formulas are emphasized without dominating the graph.

## Panel / role / script ledger

| Parent | Roles | Measured ink summary | D/E and harmony | Decision |
|---|---|---|---|---|
| trial | 10.1pt CJK + 11.6pt math n | CJK 37–38px; n 27px | cross-script N/A; both readable | PASS |
| gamma | 10.1pt CJK + Latin | CJK median 37px; G 29px; lowercase 21–22px | same-script ratios 0.973–1.027 | PASS |
| families | 10.1pt CJK | median 37px, 37–38px | ratio 1.000–1.027 | PASS |
| posterior | 10.1pt heading + 11.6pt formula label/math | heading 37–38px; 参数 43px; math 27px | 43/37=1.162, valid formula emphasis; coarse CJK taxonomy advisory only | PASS |
| predictive | 10.1pt CJK + 11.6pt fraction + natural scripts | CJK median 38px; base math 27px; scripts 24–26px | scripts complete/readable; fraction balanced | PASS |
| simplex | 10.1pt CJK | median 37px, 37–38px | ratio 1.000–1.027 | PASS |
| mom | 10.1pt CJK | median 37px, 37–38px | ratio 1.000–1.027 | PASS |
| lda | 10.1pt CJK | median 37px, 36–38px | ratio 0.973–1.027 | PASS |
| R7 label | 10.1pt CJK | 37px/37px | ratio 1.000 | PASS |

All protocol pixel floors pass: CJK ≥36px, Latin uppercase 29px, Latin lowercase 21px, base math/operators 27px, and natural scripts 24–26px. The original/overlay/mask-only views for T001–T093 were each inspected at 8× nearest; missing-stroke and foreign-pixel counts are both 0 for every row in `manual_glyph_reviewer.csv`.

## Geometry and complete pairs

- Full object denominator: `109`; complete unordered denominator: `C(109,2)=5886`.
- Illegal `OVERLAP_PIXEL_COUNT=0`; `CLIP_PIXEL_COUNT=0`.
- Independent text–text minimum 47.0416px (threshold 4).
- Text–relation minimum 24.2982px (threshold 3).
- Text–own-node-border minimum 18px (threshold 5).
- Text–other-node-border minimum 18px (threshold 3).
- Text–other-math-rule minimum 69px (threshold 3).
- The only 23 design pairs are nine same-formula rule relations and fourteen source-defined relation endpoints; all were opened in six 8× critical sheets and manually justified.

## Semantics

The seven source relations are present and unambiguous: trial→families, gamma→families, families→posterior, posterior→predictive, families–simplex interpretation, posterior–mom interpretation, and dashed predictive→lda application. Text extraction matches every node and the application label. Formula codepoints and layout are correct: posterior `参数 𝛼 + 𝑛`; predictive numerator `𝛼ᵢ + 𝑛ᵢ`, denominator `𝛼₀ + N`, with a separately accounted fraction rule. `N` is genuine U+004E and both plus signs are U+002B.

## R168 advisory ledger

1. A coarse CJK bucket would mix the 11.6pt formula word `参数` with the 10.1pt heading and yield 43/37=1.162; semantic-role separation makes the intended formula emphasis explicit. Under R168 this taxonomy/peer issue cannot be a hard failure.
2. Extracted font sizes differ from declarations by roughly 0.4–0.6%; metadata-only advisory.
3. Raw PDF character bboxes overlap for T002/T005 (9 candidate pixels) and T007/T008 (1 candidate pixel). Their final glyph masks use traceable connected-component ownership. The corresponding contact sheets show that the retained masks match the actual contours with no physical glyph collision or missing stroke.

## Execution note and verdict

The first non-TeX evidence-script run completed all evidence writes but returned a console-only GBK encoding error while printing mathematical Unicode. The script was changed only to print JSON with ASCII escapes and then rerun; it never generated or overwrote reviewer, visual, boolean, decision, or note fields (`manual_fields_generated_by_machine=false`). No TeX engine was invoked.

All machine hard gates and all actual manual gates pass. Verdict: **PASS**. Required route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`.
