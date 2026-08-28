# FIG-P640-01 — R105 fresh isolated SA1 report

- `HANDOFF_ID`: `MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- `ROLE`: fresh isolated SA1, read-only candidate/source auditor
- `RESULT`: **FAIL_TO_SA2**
- `MANUAL_RECORD_UTC`: `2026-08-25T22:45:27.1834804Z`

## Locked candidate

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf`
- physical page: 690 / 817 (printed page 677)
- size: 4,967,209 bytes
- SHA-256: `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`
- page: 595.2760 × 841.8900 pt
- source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex`

## Evidence denominator and pair closure

The foreground denominator is frozen at 253 objects: 242 non-whitespace visible glyphs and 11 semantic foreground drawing groups. The source-defined point-label white rectangle and marker white fill are recorded as two real opaque backgrounds, not duplicated into the foreground denominator. The right `.99` tick is extracted only as a dedicated audit subobject and is not double-counted.

All `253×252/2 = 31,878` unordered pairs are present: 26,506 machine PASS, 5,371 explicit design-whitelisted internal/endpoint relations, and one hard failure. There are no empty glyph/path masks and no crop pixels. Crop-edge minima are 67/58/42/34 native pixels (left/top/right/bottom).

## `.99` marker versus vertical tick

This relationship passes the R168 hard geometry gate:

- separate raw-mask intersection: `0 px`;
- continuous vector-outline gap: `0.2137756 pt`, or `0.8907317` native pixels at 300 dpi;
- complete intervening native pixel rows: `0`;
- conclusion: positive subpixel whitespace and zero contact, not a one-pixel overlap.

The native/8× evidence is `roi/marker_tick_native1x.png` and `roi/marker_tick_8x_nearest.png` under the evidence root.

## Hard failure

The right-panel gold ESS curve visibly fuses with the first `N` of the lower annotation line `N_eff/N→0` (`GLYPH-0109` versus `PATH-RIGHT-ESS-CURVE`). The pair ledger reports a 103-pixel candidate intersection; because glyph and curve use the same color, a machine-only pure-glyph split is not trustworthy, but native and 8× manual review shows an unambiguous shared/fused region. The conservative hard lower bound is `>=1 native px`, which is sufficient for failure.

The responsible source placement is the two-line node at lines 47–48, anchored at `axis description cs:.98,.96` without an opaque background. Evidence: `roi/right_curve_vs_limit_N_native1x.png`, `roi/right_curve_vs_limit_N_8x_nearest.png`, and `machine/critical_overlap_measurement.json`.

## R168 manual gates

- `PAGE_FUSION_PASS=true`: scale, caption, whitespace and adjacent paragraph fit naturally.
- `GRAYSCALE_PASS=true`: all curves remain distinguishable and text remains readable.
- `MATH_SEMANTICS_PASS=true`: `rho^(2k)`, `(1-rho^2)/(1+rho^2)`, the `.99` point and the `|rho|→1^-` limit agree with source and caption.
- `TEXT_CONSISTENCY_PASS=true`: title, axes, legend, annotations and caption agree.
- `FONT_VISUAL_HARMONY_PASS=true` under R168: no missing/tofu/wrong glyph, unreadability or gross visible imbalance. Font-height and ratio variations remain advisory.
- `OVERLAP_PIXEL_COUNT>=1`: hard failure at the curve/annotation collision.
- `CLIP_PIXEL_COUNT=0`.

## SA2 disposition

Reposition the two-line limit annotation or use a genuine source-defined opaque background with auditable paint order, rebuild the official full book, and obtain a new fresh SA1 package. No source, PDF, build, state or inventory was modified by this audit.

Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826`

