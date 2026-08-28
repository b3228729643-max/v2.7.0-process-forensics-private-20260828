# FIG-P033-01 STATIC_R3 source patch

- HANDOFF_ID: `A-R110-P033-SA2-SOURCE-STATIC-R3-20260827`
- route: `SOURCE_PATCH_READY_REQUEST_BUILD_SLOT`
- authority: `MAIN_R297_P033_SA1_FAIL_ACCEPTED_MINIMAL_SINGLE_SOURCE_STATIC_SCOPE`
- generated: `2026-08-27T04:34:50.2240223+08:00`
- TeX/LuaLaTeX/latexmk invocations: `0`
- commit: `NOT_AUTHORIZED / NOT_CREATED`

## Exact source scope

Only `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex` changed. The sole edit is the label y coordinate:

`at (-.18,-.23)` → `at (-.18,-.39)`

The x coordinate, label text, `anchor=north west`, color/style, plane geometry, O/P/X, vectors, dashed line, right-angle mark, brace, other labels/formulae and caption-facing semantics are unchanged. Git scope is exactly one file, 1 insertion and 1 deletion; `git diff --check` passes and the index is empty.

## Identity

- before: 2,383 bytes; SHA-256 `4BCD50FE3BFDF1A3DCFC9089E103D256555949D859EC650F047CECB3A04EF6D4`
- after: 2,383 bytes; SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`

## 300 dpi displacement and risk estimate

The source fixes `y=1.45cm`; therefore one coordinate unit equals 171.259843 px at 300 dpi. The 0.16-unit downward move equals 27.401575 px. Against the accepted 24 px R2886 ink overlap, the projected native separation is 3.401575 px.

The official R110 physical page 29 was independently rendered at 300 dpi without TeX. In that current page, the `子空间 S` label ink occupies rows 2656–2694 and the caption first line occupies rows 2780–2836, leaving 85 empty pixel rows. After the proposed move, the projected remaining label-to-caption ink clearance is about 57.60 px. Thus the minimal change covers the known overlap while retaining substantial caption/page slack.

This is a static projection only. It does not claim PASS; a single explicitly granted standalone/direct LuaLaTeX candidate is required to measure the actual new PDF and re-run full geometry regressions.

## Frozen request

`P033_SOURCE_PATCH_READY_REQUEST_BUILD_SLOT`
