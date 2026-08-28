# FIG-P641-01 — R110 SA3 Fresh-Isolated Visual Acceptance Report

## Identity and scope

- Handoff ID: `C-FIG-P641-01-R110-SA3-FRESH-ISOLATED-V1`
- Actual reviewer instance: `/root/sa3_fig_p641_r110_fresh_isolated_v1`
- Model / effort / fork context: `gpt-5.6-sol / xhigh / none`
- Assigned scope: one independent SA3 visual/semantic/pixel audit of UID `FIG-P641-01` against the current R110 full-book PDF and the current single figure source.
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa3_r110_fresh_isolated_v1`

## Frozen input identities

- Official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf`
  - bytes: `4,967,063`
  - SHA-256: `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`
- Current figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex`
  - bytes: `3,008`
  - SHA-256: `8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15`

Both identities were recomputed in this isolated run and exactly match the assigned identities.

## Independent localization and visual views

The current source caption and visible caption independently locate this artifact at physical PDF page `691`, printed page `678`, Figure `33.8`. The PDF page is `595.276 × 841.890 pt` and renders natively at `2481 × 3508 px` at 300 dpi. The complete figure-plus-caption crop is `(60, 550, 530, 730) pt`, corresponding to `(250, 2291, 2209, 3042) px`; the standalone figure body is `(115, 550, 470, 696) pt`, corresponding to `(479, 2291, 1959, 2901) px`.

I actually opened and inspected the full page at 200 dpi and native 300 dpi, the complete figure plus caption, standalone body, grayscale rendering, semantic/object overlay, text overlay, all 21 glyph contact sheets, all three graphic contact sheets, all four critical-relation contact sheets, and every relation-specific native-1× / nearest-neighbor-8× critical ROI. `manual_view_ledger.csv` records these views. No figure edge, node, formula, annotation, or caption ink is clipped.

## Independent mathematical and semantic recomputation

The chapter context gives the joint factorization

`π(α, θ, z | y) ∝ p(z,y | θ) p(θ | α) p(α)`.

When updating `θ` conditional on `α,z,y`, the factor `p(α)` is constant in `θ`; hence

`π(θ | α,z,y) ∝ p(θ | α) p(z,y | θ)`.

The visible graph encodes exactly those two factors incident to the highlighted `θ` node. Its dashed blankets identify `α,z,y`, while the `p(α)` factor is marked outside and eliminated. The formula, annotation, graph adjacency and caption agree. There is no wrong conditional direction, dropped incident factor, retained irrelevant factor, or geometric-semantic mismatch.

## Complete denominator and exhaustive pair review

The complete visible foreground denominator was frozen only after the images were opened:

- 162 glyph objects, `C001`–`C162`, under 11 semantic text parents.
- 18 graphical objects, `G01`–`G18`: three factor borders, four node borders, three dashed blanket borders, six graph edges, annotation shaft and arrowhead.
- Total `N = 180`; exhaustive unordered pairs `C = N(N−1)/2 = 16,110`.
- Critical relations: `41`.
- Empty glyph masks: `0 / 162`; empty graphic masks: `0 / 18`.
- Every one of the 18 PDF drawing objects intersecting the figure body is accounted exactly once.
- Visible mathematical rule objects requiring a separate denominator entry: `0`; there is no fraction bar, root bar, overline, underline, accent, cancel stroke, or analogous math rule in this figure.

The exhaustive pair table contains 14 nonzero raw contacts totaling 258 pixels. Every contact is an explicit source-design connection: factor border↔edge, node border↔edge, blanket boundary↔traversing edge, factor border↔annotation arrowhead, or annotation shaft↔arrowhead. Thus non-design/illegal overlapping pairs are `0`. The three visually sensitive nested node/blanket pairs remain independent: alpha has 7 px clearance, z has 10 px, and y has 10 px. The minimum positive clearance anywhere in the pair universe is 7 px.

## Text, codepoint and typography review

Expected and PDF-extracted visible text agree exactly for all `11 / 11` semantic parents. All `162 / 162` visible glyphs have an explicit Unicode codepoint/name and were manually checked in original, overlay and mask-only panels. Missing glyphs, tofu, wrong codepoints, incomplete masks and foreign-pixel masks are all `0`.

Declared text sizes are 9.2 pt for the legend and 9.5 pt for node, factor, annotation and formula text; the PDF vector sizes are approximately 9.16563 pt and 9.46451 pt respectively, while the caption is approximately 9.96264 pt. The source graphic scale does not transform node text. Native-300-dpi and grayscale inspection shows actual readability and balanced hierarchy. Short punctuation ink heights and the proportionality sign's numeric raster profile are anatomy/taxonomy or numeric micro-font observations only. Under the current Goal/R168 policy they are advisory, because there is no actual unreadability, visible severe size imbalance, missing ink or semantic ambiguity.

## Hard gates

The genuine reviewer ledgers record these results:

- Actual missing/tofu/wrong codepoint: `0`.
- Actual unreadability or visibly severe size imbalance: `0`.
- True clipping: `0`.
- Illegal overlap: `0`.
- Semantic/geometric error: `0`.

All 162 glyph, 18 graphic and 41 critical-relation IDs were manually adjudicated after their relevant images were opened. The ledgers contain one reviewer identity, one decision and a genuine observation for each ID; no machine script generated or prepopulated reviewer identities, decisions, PASS/FAIL values or notes.

## Isolation and forbidden-action accounting

Old P641 evidence/role/root/report/handoff/state/inventory/chat/Git-history/main-acceptance conclusions read: `0`. Other-UID conclusions read: `0`. Evidence-parent enumeration beyond creation/use of the assigned root: `0`. Git calls: `0`. TeX/LuaLaTeX/latexmk calls: `0`. PDF authoring-marker calls: `0`. PDF/source/chapter writes: `0`. Central-state/inventory writes: `0`. Collaboration/thread/agent status or history enumeration calls: `0`. Second UID/role starts: `0`. Process-management actions: `0`.

## Decision

`SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

This is one isolated SA3 role decision only. It does not self-count a main, global or final acceptance. The only unresolved action is the root/main C local acceptance step.
