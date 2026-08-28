# FIG-P582-01 R109 fresh isolated SA1 manual acceptance

- Reviewer: `SA1_FRESH_ISOLATED_R109`
- Handoff ID: `A-R109-P582-SA1-FRESH-ISOLATED-20260826`
- Observation completed: `2026-08-26T22:58:54.0216802+08:00`
- Official independently located page: physical PDF page `632`, printed page `619`
- Final-visible denominator: `N=105` (`78` glyphs + `27` graphics)
- Exhaustive unordered pairs: `C=5460`

## Material actually opened

The reviewer actually opened the final official-page render, native 300 dpi figure crop, native standalone crop, grayscale render, object-overlay render, all four glyph 1x sheets, all four glyph 8x sheets, all four graphic 1x sheets, all twenty graphic 8x sheets, all four critical-pair 1x sheets, and all four critical-pair nearest 8x sheets. This judgment was recorded only after those final artifacts were opened.

## Human decisions

- SOURCE_FONT_PASS: `true` — the source sets figure, ticks, labels, annotations, and value labels at 9.5–9.6 pt and does not use global scaling.
- GLYPH_COMPLETENESS_PASS: `true` — all 78 glyph masks have complete intended strokes; no missing stroke, tofu, wrong codepoint, or foreign-pixel contamination was seen.
- PIXEL_HEIGHT_PASS_R168: `true` — five legacy strict calibration flags (`T016`, `T019`, `T032`, `T059`, `T063`) are microscopic taxonomy/shape differences only. The four punctuation dots are exact, visible decimal dots; `T032` is an exact, balanced equals sign with correct meaning.
- SAME_CLASS_RATIO_PASS: `true` — no strict same-class ratio failure exists.
- ROLE_RATIO_PASS: `true` — visual hierarchy is balanced; formula, ticks, annotations, and caption are mutually legible.
- OVERLAP_PASS: `true` — exhaustive pair analysis reports zero illegal intersection pixels. The closest independent text pair `P3464` has a measured 1 px native white gap and zero intersection; at 8x the glyph boundaries remain distinct with no merged-stroke ambiguity.
- CLIPPING_PASS: `true` — clip pixel count is zero; the minimum object-to-crop-edge clearance is 30 px.
- GRAPHIC_COMPLETENESS_PASS: `true` — all 27 final-visible semantic graphics match the official rendering at 1x and 8x. Source primitive `G016` is excluded from the visible denominator because it is completely hidden by its later-painted square marker in the official final pixels; it is retained in the frozen ledger as an explicitly excluded hidden source primitive.
- FONT_VISUAL_HARMONY_PASS: `true` — no genuinely unreadable label or obvious severe imbalance was seen.
- MATH_SEMANTICS_PASS: `true` — `h(U_i)=U_i^2`; the fixed samples `0.8, 0.1, 0.7, 0.4` yield squared values `.64, .01, .49, .16`, running means `.64, .325, .38, .325`, and the reference is `E[U^2]=1/3`.
- RELATIONSHIP_SEMANTICS_PASS: `true` — the running mean decreases, rises, then decreases, correctly illustrating non-monotone convergence behavior.
- TEXT_CONSISTENCY_PASS: `true` — visible annotations and caption agree with the source semantics.
- GRAYSCALE_PASS: `true` — dashed reference, square sample markers, circular running-mean markers, and line styles remain distinguishable without color.
- PAGE_INTEGRATION_PASS: `true` — the figure is centered and sharp; the two-line caption is natural; no page-boundary collision or crowding is present.

## R168 disposition

R168 controls the hard verdict. Microscopic font, pixel, and taxonomy differences are advisory. A hard failure would require missing/tofu/wrong-codepoint or wrong math meaning, genuinely unreadable text or obvious severe imbalance, true clipping/illegal overlap, or substantive geometry/relationship/semantic error. None is present.

## Decision

`PASS`

This is an SA1 evidence result only. It does not claim `A_LOCAL_PASS`. The next permitted action is review by a different fresh isolated SA3; this SA1 does not launch that reviewer.
