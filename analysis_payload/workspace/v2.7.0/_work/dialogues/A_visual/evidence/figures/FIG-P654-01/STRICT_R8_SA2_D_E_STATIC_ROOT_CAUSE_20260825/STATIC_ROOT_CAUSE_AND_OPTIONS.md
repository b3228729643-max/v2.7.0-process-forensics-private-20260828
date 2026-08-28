# P654 R8 D/E static root cause and options

## Decision

`TAXONOMY_STATIC_PASS_SOURCE_UNCHANGED`

The R7A root remains permanently rejected and read-only. This R8 result does not revise R7A, submit source, authorize TeX, dispatch a fresh role, or claim local/final pass. It establishes only that the eight R7A D/E failures are caused by an over-broad frozen grouping key, not by a source point-size mismatch: the old key mixes typographically non-comparable Latin height tiers and baseline math lower variables, operators and uppercase variables.

With a single predeclared global taxonomy applied to all 95 glyph/formula elements, the complete denominator is `95/95`, the mapping is one-to-one, and all 10 `PANEL_ID + SEMANTIC_ROLE + TYPOGRAPHIC_CLASS` groups satisfy the per-element hard interval `[0.92,1.08]`. The source-level same-role and hierarchy gates also have zero failures. Therefore no additional business-source edit is recommended at this static stage.

## Frozen identities and non-TeX boundary

- Sole source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- Source bytes/SHA-256: `3,122` / `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- Frozen R7A pixel input: `machine_reuse/after_pixel_measurements.csv`, `41,097` bytes, SHA-256 `DBB1DA8362077C0062BC2B4CC06A9F21DB7768E4770D4CA01FD1F95B801E9A4C`
- Current Git scope: exactly one modified business file, the source above, with the already-existing `1 insertion / 1 deletion` trial-`n` change; `git diff --check` errors `0`.
- Static capture found `latexmk/lualatex/luatex/luahbtex = NONE`. R8 launched none of them, wrote nothing to the source or R7A root, and created no commit.
- Machine-readable capture: `NO_TEX_AND_GIT_SCOPE.json`.

## Authority and D/E interpretation

The strict protocol requires:

1. same-panel, same-script, same-semantic-role element/class ratios to their group median in `[0.92,1.08]`;
2. same-role source size `max/min <= 1.03` and absolute difference `<=0.25pt`;
3. role hierarchy ranges relative to node-base text;
4. no cross-script comparison and no exact-glyph, post-measurement or manual-note escape.

The R7A `ROLE` column is a node/location identifier (`GAMMA`, `POSTERIOR_FORMULA`, etc.), while the already-frozen source role ledger identifies the actual semantic typography roles: `NODE_BASE`, `FORMULA_BLOCK`, `TRIAL_INLINE_FORMULA`, and `ANNOTATION`. R8 assigns semantic roles only from the frozen location role plus frozen script class, not from `ELEMENT_ID`; it then applies a global typographic-height taxonomy using only pre-measurement character categories and the frozen script class. Neither assignment reads `H_INK_PX`, area or a prior decision. Exact inputs, definitions and forbidden split keys are frozen in `TAXONOMY_POLICY.json`.

## Reproduction of the R7A failure

R8 first recomputed the unmodified frozen R7A key `PANEL_ID + FROZEN_LOCATION_ROLE + FROZEN_SCRIPT_CLASS`. It reproduces exactly 8 hard failures:

| Frozen group | Heights (px) | Median | Failure count | Failure reason |
|---|---|---:|---:|---|
| `GAMMA / LATIN_GREEK_LOWER` | 22, 21, 21, 22, 22, 27, 22 | 22 | 1 | lower-case `t` has an ascender and is not an x-height glyph |
| `POSTERIOR_FORMULA / BASE_MATH_OPERATOR_OR_GLYPH` | 24, 29, 24 | 24 | 1 | `+` is mixed with baseline lower variables |
| `PREDICTIVE_FORMULA / BASE_MATH_OPERATOR_OR_GLYPH` | 24, 29, 24, 24, 29, 33 | 26.5 | 6 | lower variables, binary operators and uppercase `N` are mixed |

This is a real failure of the frozen R7A grouping and cannot be manually overridden. Complete row-level reproduction is in `FROZEN_R7A_GROUP_RECOMPUTE.csv`.

## Predeclared taxonomy

### Semantic roles

- `NODE_BASE`: all ordinary 10.1pt node-label glyphs.
- `FORMULA_BLOCK`: every visible glyph in both 11.6pt displayed formulas, including CJK prefix, baseline math and natural scripts.
- `TRIAL_INLINE_FORMULA`: the 10.7pt trial inline formula.
- `ANNOTATION`: the 10.1pt application edge annotation.

These are source constructs, not node IDs or pixel-derived groups.

### Typographic height classes

- `CJK_FULL`.
- `LATIN_FULL_HEIGHT_CAP_OR_ASCENDER`: uppercase/digit plus the predeclared lowercase ascender set `b,d,f,h,k,l,t`.
- `LATIN_LOWER_X_HEIGHT`: lowercase without ascender/descender.
- `LATIN_LOWER_DESCENDER`: predeclared `g,j,p,q,y` class; no actual P654 member.
- `MATH_BASE_LOWER_VARIABLE`.
- `MATH_BASE_BINARY_RELATION_OPERATOR`.
- `MATH_BASE_UPPER_VARIABLE`.
- `NATURAL_TEX_SCRIPT`.

The Latin full-height tier is used because D/E compares native ink height. It does not weaken absolute hard thresholds: the original frozen glyph threshold class remains present in every element row. It also avoids creating a one-element `t` group: actual heights `G=29`, `B=28`, `t=27` have median `28` and ratios `0.964286..1.035714`.

No class uses an exact glyph identity. The actual uppercase-math class contains only `N` because this figure has one uppercase baseline variable, but the class definition applies to every uppercase mathematical variable and was fixed before inspecting values. It is explicitly marked as an actual singleton, so it is not presented as empirical dispersion evidence. Its independent absolute threshold and its enclosing 11.6pt source-role uniformity remain mandatory and pass. The same treatment applies to the trial inline lower-variable class, whose singleton arises from a distinct source-semantic role rather than a post-hoc split.

## Complete denominator result

| Semantic role / typographic class | Count | Heights (px) | Median | Ratio range | Result |
|---|---:|---|---:|---|---|
| annotation / CJK full | 2 | 35, 35 | 35 | 1.000000 | PASS |
| formula block / CJK full | 2 | 40, 40 | 40 | 1.000000 | PASS |
| formula block / binary operator | 3 | 29, 29, 29 | 29 | 1.000000 | PASS |
| formula block / lower variable | 5 | 24, 24, 24, 24, 24 | 24 | 1.000000 | PASS |
| formula block / upper variable | 1 | 33 | 33 | 1.000000 | PASS, declared singleton |
| formula block / natural script | 3 | 26, 26, 24 | 26 | 0.923077..1.000000 | PASS |
| node base / CJK full | 69 | 34..36 | 35 | 0.971429..1.028571 | PASS |
| node base / Latin cap-or-ascender full height | 3 | 29, 28, 27 | 28 | 0.964286..1.035714 | PASS |
| node base / Latin lower x-height | 6 | 22, 21, 21, 22, 22, 22 | 22 | 0.954545..1.000000 | PASS |
| trial inline / lower variable | 1 | 22 | 22 | 1.000000 | PASS, declared singleton |

Totals: `95` elements, `95` unique IDs, `10` nonempty groups, `0` unmapped, `0` duplicate assignments, `0` hard-ratio failures.

Complete element mapping and ratios are in:

- `TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.csv`
- `TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.json`
- `TYPOGRAPHIC_GROUP_SUMMARY.csv`
- `TYPOGRAPHIC_GROUP_SUMMARY.json`
- `STATIC_RECOMPUTE_SUMMARY.json`

## Source uniformity and hierarchy option

No source patch is statically required:

| Source semantic role | Elements | Effective pt | Same-role ratio / delta | Result |
|---|---:|---:|---|---|
| node base | 78 | 10.1 | 1.000000 / 0.00pt | PASS |
| formula block | 14 | 11.6 | 1.000000 / 0.00pt | PASS |
| trial inline formula | 1 | 10.7 | 1.000000 / 0.00pt | PASS |
| annotation | 2 | 10.1 | 1.000000 / 0.00pt | PASS |

Relative to the 10.1pt node base, formula block=`1.148515` in `[1.00,1.18]`, trial inline=`1.059406` in `[1.00,1.18]`, annotation=`1.000000` in `[0.95,1.10]`. Full ledgers are `SOURCE_SAME_ROLE_SIZE_LEDGER.csv` and `SOURCE_ROLE_HIERARCHY_LEDGER.csv`.

A per-glyph source resize is rejected: it would make one glyph pass by changing its point size, violate same-role `<=0.25pt`, and risk altering the already-closed geometry. Replacing `N`, `+`, `t`, or the mathematical notation is also rejected because it changes exact semantics/variables to solve a taxonomy error. The narrowest protocol-compliant option is therefore taxonomy-only: freeze this global rule set in the next evidence generator, rebuild the complete denominator from the next authorized candidate, and subject the new native 300dpi measurements and manual evidence to a fresh root audit.

## Required next route

`P654_TAXONOMY_STATIC_FREEZE_READY_REQUEST_BUILD_SLOT`

No TeX is run or authorized by this report. Mainline must explicitly grant the next build slot. A future build/evidence round must regenerate all required native 300dpi/N=116/C=6670/1x/8x/manual/manifest evidence; R7A machine or manual conclusions cannot be promoted as the new result merely because this static taxonomy closes D/E.
