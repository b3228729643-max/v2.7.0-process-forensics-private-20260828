# Handoff — FIG-P640-01 R105 fresh SA1 → SA2

- `HANDOFF_ID`: `MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- `RESULT`: `FAIL_TO_SA2`
- `OFFICIAL_PDF_SHA256`: `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`
- `PHYSICAL_PAGE`: `690`

## Single actionable hard defect

The right ESS curve illegally fuses with the first `N` in the lower line of the limit annotation `N_eff/N→0`. This is visible at native 300 dpi and 8× nearest and is the only non-whitelisted failing unordered pair after real white occlusion is applied.

- source: `...\V5-C04\fig_v5_c04_mixing_rho_comparison.tex`
- source lines: 47–48
- current placement: `at (axis description cs:.98,.96) {$|\rho|\to1^-:$\\$N_{\rm eff}/N\to0$};`
- failing IDs: `GLYPH-0109` ↔ `PATH-RIGHT-ESS-CURVE`
- machine candidate intersection: `103 px`; manual conservative hard lower bound: `>=1 native px`
- evidence: `roi/right_curve_vs_limit_N_native1x.png`, `roi/right_curve_vs_limit_N_8x_nearest.png`, `machine/critical_overlap_measurement.json`

SA2 may reposition the node or add a genuine opaque source background, but must preserve semantics, page balance and the `.99` endpoint.

## Confirmed non-defect

The `.99` open marker does **not** contact its dedicated vertical tick: raw-mask intersection is `0 px` and vector-outline whitespace is positive (`0.2137756 pt = 0.8907317 native px`). Preserve this relationship.

## Re-entry condition

After a source fix and new official full-book build, create wholly new evidence and run fresh SA1 again. Do not reuse this failure package as PASS evidence.

No source, PDF, build, central state or inventory was modified.

Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826`
Report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P640-01-SA1-R105-FRESH-ISOLATED-MAIN-REPLACEMENT-20260826.md`
