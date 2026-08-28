# FIG-P654-01 — R103 fresh isolated SA3 visual acceptance

- HANDOFF_ID: `A-R103-P654-SA3-FRESH-ISOLATED-20260825`
- role instance: `/root/p654_r103_fresh_sa3`
- candidate: official R103 `main_full.pdf`, physical page 704
- frozen identity: 817 A4 pages; 4,967,184 bytes; SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- source SHA-256: `2EF1663B13A7982ACD5835217D0BB317FBF44146B08BE19F439430A2B42FABE7`
- reviewer: `SA3-FRESH-ISOLATED`

## Manual opening coverage

Actually opened: `full_page_200dpi`, `figure_crop_300dpi`, `standalone_300dpi`, `grayscale_300dpi`, the native-coordinate text/object overlay, all 7 glyph contact sheets, all 3 graphic contact sheets, the 1x and 8x-nearest pair matrices, the seven-relation overlay, and all 14 critical 1x/8x ROI packs. The 93 glyph and 21 graphic decisions were written after those observations; no machine script generated or overwrote reviewer, decision, note, or manual booleans.

## Independent denominators and hard gates

- `GLYPH_COUNT=93`; `GRAPHIC_COUNT=21`, including `MATH_RULE_COUNT=1`; `TOTAL_OBJECT_COUNT=114`.
- `ALL_UNORDERED_PAIR_COUNT=C(114,2)=6441`; manual merged pair-class coverage sums to exactly 6441.
- `RELATION_COUNT=7/7`: R1–R4 directed solid main chain, R5–R6 undirected thin explanatory links, R7 directed dashed application link.
- `EMPTY_MASK_COUNT=0`.
- `OVERLAP_PIXEL_COUNT=0` for all independent pairs; all nonzero/zero-clearance reviewed contacts are node–edge or same-edge shaft–arrowhead design composition.
- `CLIP_PIXEL_COUNT=0`; minimum text-to-body-crop edge clearance is 56 native px.
- hard-clearance failures: 0. Independent minima include GLYPH–NODE_BORDER 17px (hard gate 5px), GLYPH–LINE_ARROW 29.463px (3px), GLYPH–ARROWHEAD 26.019px (3px), and GLYPH–GLYPH 46.096px (4px).

## Font and semantic manual decisions under R168

- `FONT_VISUAL_HARMONY_PASS=true`.
- Source effective sizes are 10.1pt for ordinary/annotation labels and 11.6pt for formula blocks, with no graphics scaling, `tiny`, `scriptsize`, or `scriptstyle` override.
- All 93 glyphs meet their numeric native-pixel category thresholds. The one D-ratio outside `[0.92,1.08]` is uppercase `G` grouped with lowercase Latin in a coarse taxonomy; under R168 this taxonomy micro-ratio is advisory only. Actual `Gamma` is clearly readable and visually normal.
- `TOFU_OR_MISSING_GLYPH=false`; `WRONG_CODEPOINT_OR_GLYPH=false`; `ACTUAL_UNREADABLE=false`; `SEVERE_VISIBLE_IMBALANCE=false`.
- The denominator uses genuine uppercase `N` U+004E, not Greek nu; α, n, natural subscripts and both plus signs have the intended codepoints and readable shapes. The unique fraction rule is separately mapped and pure.
- `MATH_SEMANTICS_PASS=true`: posterior parameter is `α+n`; predictive probability is `(α_i+n_i)/(α_0+N)`.
- `OBJECT_CONTENT_PASS=true`: all 8 nodes and all 7 source relations are present with correct direction/style.
- `TEXT_FIGURE_CONSISTENCY_PASS=true`: the caption and reading-order paragraph agree with the rendered dependency chain.
- `GRAYSCALE_PASS=true`; `PAGE_INTEGRATION_PASS=true`.
- `REAL_CROP=false`; `ILLEGAL_OVERLAP=false`.

## Sealed decision candidate

`SA3_VERDICT=PASS`

`ROUTE=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This SA3 role does not write `A_LOCAL_PASS`, central inventory, state, source, or PDF.
