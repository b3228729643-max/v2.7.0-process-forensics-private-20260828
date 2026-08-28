# FIG-P412-01 — ROOT VALIDATION STRICT-R1

ROOT_RESULT: **CONFIRM SA1 FAIL; ROUTE TO SA2**

## Frozen identity

- Candidate: `src/build/strict_current_r93_fullbook/main_full.pdf`
- Current physical page: `449/813`; printed page: `436`; figure: `23.1`.
- Source: `src/绘图源码/第03册_优化模型与序列模型/V3-C07/fig_v3_c07_selection_loop.tex`.

## Root evidence recheck

- Root opened the native full-page, 300 dpi figure crop, native grayscale view, text-overlay view, and the exact `T05__V08` raw/overlay/overlap-mask ROI at 1:1 pixels.
- The earlier provisional `T05__V08 = 161 px` result was a reconstruction error. The real PDF contains a dashed feedback path followed by an opaque white label background. Exact undilated span/vector masks give `MASK_OVERLAP_PX=0` and a nearest foreground distance of `7 px`; this exceeds the `3 px` text-to-line gate. The current overlap sum is therefore `0`, not a hard failure.
- All `315` independent pairs were recorded (`91` text-text + `224` text-vector); overlap sum `0`, nonzero-overlap rows `0`, failing-clearance rows `0`, and clip count `0`. Text-text PDF/vector bbox minimum is `9.752 px`; node text-border minimum is `17 px`; figure-edge minimum is `30.370 px`.
- Pixel heights pass: source-owned CJK spans are `33–34 px`; all relevant CJK spans are `33–38 px`; caption digits are `28 px`. Same-class and role ratios pass.
- Source declarations independently confirm the hard failure: ordinary nodes use `9.4 pt`, the locked node uses `9.2 pt`, and two annotations use `9.0 pt`. Thus all `11` source-owned visible text spans are below the required `9.5 pt` floor. Caption spans are not part of this source-owned failure.

## Caption-chain clarification

The SA1 report conservatively marked caption source size unknown because its task scope did not include the shared style. Root resolved the current dependency without modifying it: the 11 pt `ctexbook` entry loads `common/statlearnbook.sty`, whose line 305 sets `\captionsetup{font={small,...}}`; the frozen PDF span size is `9.962640 pt`. The caption chain is therefore auditable and above `9.5 pt`. SA2 does **not** need to modify the shared caption style for this figure.

## Routing

`SOURCE_FONT_PASS=false`; every other measured hard gate currently passes. Per Goal §9.2.1-I, SA3 is prohibited. The next role is a single whitelisted SA2 that raises only this figure's visible source-owned text to at least `9.5 pt`, preserves current role ratios and geometry, and emits a fresh candidate for a new independent SA1.
