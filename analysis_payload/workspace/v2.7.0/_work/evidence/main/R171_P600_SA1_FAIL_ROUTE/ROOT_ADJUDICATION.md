# FIG-P600-01 SA1 fail-route adjudication

- Status: `MAIN_ACCEPTS_CONTENT_FAIL_TO_SA2`
- Main commit inspected: `f5971bdca5f25628d077594cdd8fd35dc9b895f5`
- No business source edit or TeX invocation was made in this adjudication.

## Independent mainline check

The C handoff reports that R101 physical page 649 / printed page 636 says Figure 32.4 draws paired flows and a rejection self-loop separately, while its complete 22-object inventory has no rejection self-loop. The submitted evidence root was mechanically rejected only because `WRITE_STOPPED` was not strictly newer than the final manifest.

Main independently checked the current integration source:

- `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C03.tex:222` says: `图...把成对流与拒绝自环分开绘制。`
- `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_balance_flux.tex` contains the two proposal-flow quantities `a` and `b`, their common clipped value `min(a,b)`, and two accepted directional flows. It contains no rejection self-loop.

The semantic mismatch is therefore independently reproduced. `S07`, `H07_TEXT_CONSISTENCY`, and `H14_FINAL` are accepted as a real content failure. This is unrelated to relaxed font micro-review.

## Lean routing decision

- `FIG-P600-01` moves from central SA1 to SA2.
- The old P600 evidence root and root-reject handoff remain immutable historical evidence.
- No evidence-only reseal is required for this already-determined FAIL direction; repeating a package solely to repair marker ordering would not change the business route.
- The eventual minimal repair belongs to the mainline chapter-text single writer, not the C figure-source writer: replace the inaccurate claim with `图...把双向提议流与截平后的成对接受流分开绘制。`
- That source edit is deliberately deferred until the P602 R103 fresh role chain has stopped reading the same V5-C03 chapter, avoiding source/PDF isolation contamination.
- P600 remains frozen in SA2 until the mainline text fix, a later official candidate, and a new fresh role chain.

## Referenced immutable handoff

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\C\C-FIG-P600-01-R101-SA1-FRESH-V1-ROOT-REJECT-R1\HANDOFF.md`
