# FIG-P654-01 R16B SA2 static source patch R2

## Status

`P654_SOURCE_PATCH_READY_REQUEST_BUILD_SLOT_R2`

R16B is the corrected static freeze after mainline review. R16 remains immutable historical static material and is not the build candidate. No TeX/latexmk process was started, no commit was created, and no fresh role was dispatched.

- authoritative before: 3122 bytes, SHA-256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- R16B after: 3334 bytes, SHA-256 `0A7CAAA49978AA6193BA4DC4CB90845981599DFC161F5A8BD6B9143A1EA4C2EB`
- scope against authoritative before: one file, four changed lines, `4 insertions / 4 deletions`
- `git diff --check`: PASS

## Mainline correction closure

1. The predictive denominator again uses the chapter-authoritative literal `N`. It is rendered as a local math atom at the lowest allowed 9.5pt:

   `\mathord{\hbox{\fontsize{9.5pt}{11.5pt}\selectfont$N$}}`

   No undefined `n_0` remains. The meaning remains exactly the current chapter definition `N=Σ_i n_i`.

2. All three plus signs remain mathematical plus glyphs and binary operators:

   `\mathbin{\hbox{\fontsize{10pt}{12.2pt}\selectfont$+$}}`

   Count is exactly 3. `\text{+}` count is zero, so the formula does not switch these glyphs to the body-text font family.

The previously accepted trial `n` 11.6pt change and `Beta→贝塔` semantic translation are retained. No other R16 source change remains.

## Six-ID expected mechanism

- `G0005`: trial `n` grows from 10.7pt to 11.6pt; static raster estimate `22×11.6/10.7≈24px`, retaining absolute H≥22 and moving to the frozen 24px median.
- `G0014`: the ordinary Latin ascender `t` is removed by the semantically identical `Beta→贝塔` translation; the replacement follows the existing CJK node-body class, with no exact-glyph taxonomy split.
- `G0042`, `G0061`, `G0066`: each 11.6pt mathematical plus is locally rendered at 10pt while remaining `mathbin`; linear estimate `29×10/11.6≈25px`, expected ratio `25/24=1.0417`.
- `G0067`: the same literal mathematical `N` is retained and locally reduced from the enclosing 11.6pt formula size to the source minimum 9.5pt as a `mathord`. This is an 18.1% source-size reduction and is the maximum allowed shrink under the 9.5pt gate. Its actual native height and the simultaneously recentered frozen-group median must be measured in the controlled candidate; no static PASS is claimed.

The frozen `PANEL_ID + ROLE + SCRIPT_CLASS` mapping and interval `[0.92,1.08]` remain unchanged. No manual override, element-ID split, exact-glyph split, or threshold change is present.

## Static scope and risk

- All node names, coordinates, text widths, minimum sizes, inner separations, seven relations, global styles, caption, label, and alt relationship description remain unchanged.
- Three pluses use the same math glyph family as the authoritative formula and keep binary spacing.
- `N` remains the exact symbol used by the surrounding chapter; no new notation or definition is introduced.
- Smallest new explicit font is exactly 9.5pt; scaling constructs remain zero.
- Trial `n` may grow about 2 native pixels inside its unchanged 28mm × 12mm node; three pluses and `N` shrink locally. These changes are expected to reduce, not increase, within-node overlap and border risk.
- `Beta→贝塔` changes the glyph denominator while shortening the label. Consequently the next candidate must rebuild all object IDs, all unordered pairs, taxonomy, and manual ledgers; none of the R15 denominator or pair evidence may be reused.
- The remaining non-target objects retain their source tokens and all figure geometry, but the official build must still remeasure the complete denominator because PDF text segmentation and pair identities may change.

## Static assertions

- braces: 68 open / 68 close
- changed business files: 1, exactly the authorized P654 source
- R2 math plus pattern: 3
- text plus pattern: 0
- literal mathord `N` at 9.5pt: 1
- undefined `n_0`: 0
- forbidden resize/scale/transform constructs: 0
- TeX/latexmk invocations: 0
- commit/fresh role: 0/0

The build slot is still owned by C-P602. R16B makes no process-availability assumption and awaits an explicit mainline grant.

