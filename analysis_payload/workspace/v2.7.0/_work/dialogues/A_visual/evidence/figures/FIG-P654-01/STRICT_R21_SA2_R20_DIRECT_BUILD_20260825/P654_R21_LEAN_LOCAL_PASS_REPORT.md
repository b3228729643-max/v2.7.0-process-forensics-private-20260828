# P654 R21 lean local-pass report

## Outcome

`FIG-P654-01` passes the R168 hard visual, semantic, geometry, overlap, clipping, and relationship gates on the single R21 direct-LuaLaTeX candidate. The correct route is `P654_R21_LEAN_LOCAL_PASS_READY_REQUEST_COMMIT`; this report does not itself authorize a commit, a fresh role, or `A_LOCAL_PASS`.

## Frozen identities

- PDF: `build/v260_FIG-P654-01_standalone.pdf`
- PDF identity: 1 A4 page, 43,970 bytes, SHA-256 `3F1D7A22BCA99828074360790CBED5EA755F6A5C27CB1AE821ABB77FE457C241`
- Source SHA-256: `2EF1663B13A7982ACD5835217D0BB317FBF44146B08BE19F439430A2B42FABE7`
- Wrapper SHA-256: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- Build: one direct `lualatex` invocation, natural exit 0, one PDF, residual TeX processes 0.

## Lean full machine result

- Full object denominator: `93 glyph + 21 graphic = 114`.
- Full unordered-pair denominator: `C(114,2)=6,441`; actual 6,441.
- Critical pair denominator: 174.
- Machine object failures / pair failures / illegal-overlap failures / clipping failures: `0 / 0 / 0 / 0`.
- Seven source relationships remain present and unchanged; the one-role formula-size source gate is internally consistent.
- The four equal-distance ownership pixels between G0002 and G0005 were resolved by native-component evidence: the pixels belong to the lower stroke of “别”, with visible white space before the target n. This is not a collision or semantic ambiguity.

## Human terminal review under R168

The reviewer opened the full native page, every glyph sheet (5), every graphic sheet (6), every complete pair matrix block (4), the ownership tie diagnostic, and seven targeted critical overlays. The explicit 114-ID ledger is `MANUAL_R168_VISUAL_LEDGER.md`.

Hard-failure counts are all zero:

- missing/tofu, wrong code point, or wrong mathematical meaning: 0;
- actually unreadable glyph or label: 0;
- plainly visible size imbalance: 0;
- real clipping or unintended overlap: 0;
- missing, reversed, broken, or semantically wrong relationship: 0.

The target n, all three U+002B mathematical plus signs, literal uppercase U+004E N, natural subscripts i/i/0, lowered LDA node, and “应用” edge label are all clear and semantically correct. The prior application-label risk is closed at 19px clearance for both characters. The closest Gamma letter spacings are visually separate; their 1--2px raster values are advisory under R168 and do not justify another source edit or build.

## Integrity and route

- Manual reviewer/decision/note fields were not created or overwritten by a script.
- No TeX was started after the R21 candidate was built.
- No source commit or fresh SA1/SA3 was created.
- Requested next action: main reviews the sealed root and, if accepted, grants the atomic single-source commit and handoff step.
