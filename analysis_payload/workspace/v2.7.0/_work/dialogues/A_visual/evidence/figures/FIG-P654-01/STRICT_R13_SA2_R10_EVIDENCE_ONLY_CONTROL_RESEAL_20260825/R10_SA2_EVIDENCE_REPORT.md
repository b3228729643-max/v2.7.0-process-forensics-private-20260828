# FIG-P654-01 R10 SA2 evidence report

## Terminal result

`LOCAL_SA2_PATCH_VERIFIED_AWAIT_R10_ROOT`

This is a local SA2 evidence conclusion only. It is not a commit, fresh SA1/SA3 result, `A_LOCAL_PASS`, or central inventory transition. Source and wrapper remained read-only throughout the R10 evidence rebuild.

## Candidate and process identity

- PDF: `build/v260_FIG-P654-01_standalone.pdf`, 43,385 bytes, SHA-256 `86712CDD98EC92AF1A2D274D4E4E987E6AE8338064FD4A3339D2761737A87260`.
- Source SHA-256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`.
- Wrapper SHA-256: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`.
- Controller SHA-256: `90E41A8B9047579FBF36C1C9F9EE5EBCD042B70739146BFD2B312229E67466B8`.
- The recorded direct invocation count is one, natural exit code is zero, `latexmk=false`, automatic retry count is zero, and the result contains exactly one PDF.
- Post-build log review found one output marker, zero fatal/emergency matches, empty stderr, and no `latexmk` text. A later point observation found no `latexmk`, `lualatex`, `luatex`, or `luahbtex` process.

## Native machine evidence

- The R10 PDF was independently rendered at native 300 dpi. Full denominator: `N=116`, consisting of 95 text/formula glyphs and 21 foreground graphic/drawing objects.
- Every glyph is bound to its character, outline, semantic parent, vector bbox, pre-occlusion mask, and final mask. Drawing/path inventory closes at 21/21.
- All unordered pairs were recomputed: `C(116,2)=6,670`, with 6,670/6,670 present and 50 critical pairs materialized as native-1x and exact-nearest-8x bundles.
- Empty masks 0; missing-stroke pixels 0; foreign pixels 0; clip pixels 0; unintended overlap pixels 0; object failures 0; pair failures 0.
- Target `FRM_TRIAL_005` has final mask height 22 px and area 297 px, so it meets the hard target `H>=22` with a complete, non-empty mask.
- Native evidence includes 16 glyph sheets, 21 graphic 1x/8x triples, 50 critical 1x/8x bundles, and 5 whole-figure/page views.

## Frozen R8 taxonomy applied to R10

- Policy SHA-256: `DC81B9ADEF783946FB6DC01E469469B51508EF64755B44D0506CB14F970885DE`.
- The global classifier remains `PANEL_ID + SEMANTIC_ROLE + TYPOGRAPHIC_CLASS`. Assignment does not use element ID, measured height, mask area, pass/fail state, or rank.
- The R10 measurements map 95/95 glyphs exactly once into 10 groups; unmapped 0, duplicate 0, D/E failures 0.
- Source same-role groups: 4/4 pass. Source hierarchy groups: 4/4 pass.
- `FROZEN_R7A_GROUP_RECOMPUTE.csv` is only an explicitly named diagnostic recomputation over the new R10 measurements; its eight legacy frozen-location failures are not migrated R7A decisions and are not inputs to the accepted R8 global taxonomy verdict.

## Actual manual workflow

Before any manual decision was written, the reviewer opened all 16 glyph sheets; all 21 graphic native-1x and exact-nearest-8x triples; all 50 critical native-1x and exact-nearest-8x bundles; all 5 views; all 3 semantic gates; all 10 taxonomy groups; all 4 source same-role groups; and all 4 hierarchy groups.

The eight manual ledgers contain 192 rows (`95/21/50/5/3/10/4/4`). Decision IDs are globally unique; exact duplicate notes 0; normalized duplicate notes 0; blank notes 0. Each row has an object-, relation-, view-, or group-specific observation and independent decision. No script generated or modified a manual field.

## Locked consumer validation

`consumer_validator.py` was frozen before its first and only run at SHA-256 `907D41E53BA99B26CF526D53A932629B430B46477FCAFF58E30145AB56FBFA27`. The one run exited zero with `failure_count=0` and conclusion `LOCAL_SA2_PATCH_VERIFIED_AWAIT_R10_ROOT`. It consumed the frozen manual ledgers and confirmed build identity, complete denominators, target height, taxonomy/source gates, manual set equality, 856 parseable PNG files, and local hygiene without writing any manual field.

## Routing boundary

The R10 evidence root is suitable for independent root acceptance. Until that acceptance and an explicit main-route decision, P654 remains SA2; no source commit or fresh role is authorized by this report.
