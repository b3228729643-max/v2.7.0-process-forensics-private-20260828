# FIG-P020-01 — SA2 strict repair R4

- Role: SA2 repair (`gpt-5.6-sol`, maximum reasoning)
- Date: 2026-08-23
- Trigger: STRICT_R3 failed the 300 dpi native-pixel gate because the local relation arrow `\to` measured 21 px, below the required 22 px.
- Authorized source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`

## Exact source change

- Line 15, local arrow only: `\fontsize{13.5pt}{13.5pt}` -> `\fontsize{14.5pt}{14.5pt}`.
- No node geometry, body/title typography, paths, caption, public style, chapter source, build entry, or state file was changed.

## SA2 preflight result

- Fresh LuaLaTeX page and standalone builds: PASS.
- Native 300 dpi arrow ink: 23 px (target at least 22 px; repair target at least 23 px).
- The arrow remains visibly smaller than the adjacent CJK body text (about 36 px) and does not become typographically abrupt.
- Overlap, clipping, overflow, and local spacing preflight: no defect observed.

## Disposition

`FIXED_PENDING_ROOT_R4_EVIDENCE_AND_INDEPENDENT_SA1_SA3`

The R3 failure record is retained; this repair does not retroactively change it.
