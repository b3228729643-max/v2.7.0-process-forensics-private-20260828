# FIG-P608-01 R105 fresh isolated SA1 visual acceptance

- Reviewer: `R105-SA1-FRESH-ISOLATED`
- Handoff ID: `A-R105-P608-SA1-FRESH-ISOLATED-20260826`
- Candidate: official R105 full-book PDF, physical page 661.
- Manual viewing order completed: full page, native color crop, native standalone crop, native grayscale crop, all 25 glyph/math-rule contact sheets, all 12 nearest relationship counterevidence pairs, and all four endpoint/crop-edge counterevidence views.

## Manual conclusions

- `FONT_VISUAL_HARMONY_PASS=true`. The 9.6 pt base/ticks/annotations and 10.8 pt labels/titles form a coherent hierarchy. Natural scripts remain clear. No text is visibly tiny, imbalanced, crowded, or disproportionately loud.
- `GLYPH_MAPPING_PASS=true`. All 68 visible glyph masks and all 6 visible math-rule component masks match their original contours, are complete at the 20/255 foreground threshold, and contain no visible foreign pixels. The per-row manual observations are in `manual_glyph_reviewer_ledger.csv`.
- `MATH_SEMANTICS_PASS=true`. Both custom two-stroke equality signs are complete 23 px aggregates and unmistakably read as equals signs. Both overlines are present, centered, and associated with the intended retained-mean symbols.
- `OVERLAP_PASS=true`. The complete 83-object, 3,403-pair ledger has no hard-relation raw-mask intersection. The 12 nearest hard-gate pairs were opened at 1x and 8x; every intersection panel is blank.
- `CLEARANCE_PASS=true`. Minimum text/graphic clearance is 14 px against a 3 px gate; minimum independent text/text clearance is 24 px against a 4 px gate; minimum cross-panel reader-element clearance is 154 px against an 8 px gate. Minimum glyph-to-crop-edge clearance is 23 px against a 6 px gate.
- `CLIP_PASS=true`. Object clip count is zero. The four endpoint/edge views show intact labels, first/final markers, curves, axis lines, and arrowheads.
- `GRAYSCALE_PASS=true`. Patterned warm-up regions, data paths, target line, markers, and annotations remain distinguishable without color.
- `PAGE_INTEGRATION_PASS=true`. On the 200 dpi full page, Figure 32.8 has natural scale and spacing and does not disturb the surrounding reading path.
- `CONTENT_PASS=true`. The t=6..20 running means independently recalculate to the plotted/source values and finish at 2.0000; the warm-up boundary, target 2, and diagnostic-only caveat agree with the figure meaning.

## R168 application

No missing/tofu/wrong codepoint, wrong math semantics, unreadability, severe typographic imbalance, clipping, or real illegal overlap was observed. Low-profile punctuation peer ratios are exactly 1.000 for height and area. Any micro-ratio or taxonomy subtlety would be advisory under R168 and does not alter the hard conclusion.

## SA1 disposition

`PASS`. This is not an `A_LOCAL_PASS` claim. The only authorized next route is a separate future fresh isolated SA3 review.
