# FIG-P033-01 R110 R3 static source patch report

## Verdict

`P033_SOURCE_PATCH_READY_REQUEST_BUILD_SLOT`

This is a static-only source freeze. It does not claim geometry PASS or local PASS. Exactly one new controlled standalone/direct LuaLaTeX invocation is required before any machine or visual verdict.

## Authority and identity

- authority: `MAIN_R297_P033_SA1_FAIL_ACCEPTED_MINIMAL_SINGLE_SOURCE_STATIC_SCOPE`
- HANDOFF_ID: `A-R110-P033-SA2-SOURCE-STATIC-R3-20260827`
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STATIC_R3_SOURCE_PATCH_20260827`
- only source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex`
- before: 2,383 bytes / SHA-256 `4BCD50FE3BFDF1A3DCFC9089E103D256555949D859EC650F047CECB3A04EF6D4`
- after: 2,383 bytes / SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`
- Git diff: one file, 1 insertion, 1 deletion; `git diff --check` PASS; staged files 0

## Exact change

```diff
-  \node[text=SLGray,anchor=north west] at (-.18,-.23) {子空间 $S$};
+  \node[text=SLGray,anchor=north west] at (-.18,-.39) {子空间 $S$};
```

Only the y coordinate changed. The x coordinate, wording, anchor, font/color/style, plane geometry, O/P/X, three vectors, dashed projection, right-angle mark, brace, all other labels/formulae and caption semantics remain unchanged.

## Static 300 dpi estimate

- frozen TikZ y scale: 1.45 cm/unit
- 300 dpi scale: 171.259843 px/unit
- downward move: 0.16 unit = 27.401575 px
- accepted old overlap: 24 px
- projected separation: 3.401575 px
- independent R110-page measurement: current label ink rows 2656–2694; caption first-line ink rows 2780–2836; 85 empty rows
- projected label-to-caption empty rows after movement: approximately 57.60 px

The change is therefore just large enough to cover the confirmed 24 px collision while retaining substantial caption/page clearance. This remains a projection pending the one authorized new PDF.

## Frozen evidence audit

- payload 6; controls 3; ordinary 9
- dual manifest rows 6/6; CSV↔JSON and manifest↔FS mismatches 0
- all 9 ordinary files read-only; root directory marked read-only
- ADS 0; cache/pyc 0
- `WRITE_STOPPED.md` is strictly latest by 284,826,846 ticks; files at/after marker excluding marker 0
- WSTOP SHA-256 `AE6527E0AFF5CAC6C1428EF481EBD2A671BBAE5638990A9687F9A5D0C3991BE7`
- TeX-family processes 0; TeX invocations in this static round 0
- commit not created; second UID/role not started

## Request

Grant one controlled standalone/direct LuaLaTeX build slot for the frozen P033 source. The new candidate must re-measure R2886 and all geometry regressions from the new PDF; no old manual conclusion is reused.
