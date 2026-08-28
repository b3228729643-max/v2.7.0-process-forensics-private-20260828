# FIG-P654-01 R16 SA2 static source patch

## Status and scope

`P654_SOURCE_PATCH_READY_REQUEST_BUILD_SLOT`

This is a static-only patch freeze. No TeX/latexmk process was started, no commit was created, no fresh role was dispatched, and no file outside the one authorized P654 figure source was modified.

- before: 3122 bytes, SHA-256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- after: 3279 bytes, SHA-256 `AC4187AA5C8706F1A87B3D1AE1F70CEA38F27FE218AAC0F6A139F102AB5FA17D`
- exact scope: one file, four changed source lines, `4 insertions / 4 deletions`
- `git diff --check`: PASS

## Root cause and expected closure

The frozen classification key and hard interval remain unchanged: `PANEL_ID + ROLE + SCRIPT_CLASS`, ratio `[0.92, 1.08]`. The patch changes rendered content before the next candidate; it does not split the taxonomy by element ID or exact glyph.

| R102 failure | Static root cause | Patch mechanism | Expected next-candidate effect |
|---|---|---|---|
| `G0005`, target bold `n`, 22/24 | trial formula used 10.7pt while the other main formulas use 11.6pt | trial `n` becomes 11.6pt/14pt | linear raster expectation `22×11.6/10.7=23.85→24px`; absolute H remains at least 22 and group ratio approaches 1.0 |
| `G0014`, `t` in `Beta`, 27/22 | the ascender glyph is a shape outlier inside the frozen ordinary lowercase node-body group | translate only `Beta` to the semantically identical Chinese `贝塔` | removes the Latin ascender outlier without changing the node, relation, or mathematical meaning; the replacement joins the existing CJK node-body class rather than creating an exact-glyph group |
| `G0042`, posterior `+`, 29/24 | 11.6pt math plus is taller than the frozen BASE_MATH median | binary operator becomes a 10pt text plus wrapped in `\mathbin` | linear expectation `29×10/11.6=25px`; expected ratio `25/24=1.0417`, while binary spacing and addition semantics remain |
| `G0061`, predictive numerator `+`, 29/24 | same as `G0042` | same 10pt `\mathbin` text plus | expected 25px and ratio 1.0417 |
| `G0066`, predictive denominator `+`, 29/24 | same as `G0042` | same 10pt `\mathbin` text plus | expected 25px and ratio 1.0417 |
| `G0067`, total-count `N`, 33/24 | uppercase cap height is a shape outlier inside frozen BASE_MATH | use the equivalent total-count notation `n_0`, parallel to `\alpha_0` | main lowercase `n` is expected near the 24px BASE_MATH median; subscript `0` follows the already-existing subscript script class, without taxonomy relaxation |

The estimates are static predictions only. A controlled official-candidate build and a completely fresh SA1 remain mandatory.

## Geometry, semantics, and regression risk

- All eight node IDs, node coordinates, style keys, text widths, minimum heights, inner separations, and all seven relation paths are byte-unchanged.
- Global figure font/style, chapter source, common macros, fonts, caption, label, and alt relationship description are unchanged.
- No `resizebox`, `scalebox`, `transform shape`, overall shrink, or sub-9.5pt font is introduced. The smallest new explicit font is 10pt.
- The target `n` grows only inside the existing 28mm × 12mm trial node. Its R102 absolute height was already 22px; the predicted 24px remains inside the same box and improves the frozen-group ratio.
- Each replacement plus becomes smaller while preserving `\mathbin` spacing, so it should not worsen overlap, clip, or border clearance.
- `Beta→贝塔` shortens the visible label inside the unchanged gamma node, so it should not worsen geometry. It changes the future glyph/object denominator and therefore all pairs must be rebuilt from zero; no R102 pair ledger may be reused.
- `N→n_0` adds a subscript glyph and may slightly alter formula width. The unchanged predictive node has 43mm text width and 30mm minimum height; nevertheless the new official candidate must remeasure all objects and all unordered pairs rather than assume the prior 110 unaffected objects remain identical.
- The source-level regression surface is confined to the six failure mechanisms and their within-node text layout. All other node and edge geometry is unchanged, but the next fresh audit must still rebuild the complete denominator because text-object identities and pair count may change.

## Static gates

- all raw braces: 64 open / 64 close
- figure begin/end: 1/1
- tikzpicture begin/end: 1/1
- source-level nodes with coordinates: 8
- source-level draw relations: 7
- explicit 10pt `mathbin` text pluses: 3
- explicit 11.6pt trial target: 1
- forbidden scaling constructs: 0
- modified business source files: 1, exactly the authorized P654 source

No build-slot assumption is made from process availability. The next action is to request an explicit controlled TeX slot from mainline.

