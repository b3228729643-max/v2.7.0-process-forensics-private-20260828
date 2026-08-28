# FIG-P262-01 — SA1 Strict R1

RESULT: **FAIL**

## Frozen candidate and direct views

- Official candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r92_fullbook\main_full.pdf` (4,933,704 bytes), physical PDF page **284** (printed page 271).
- `official_page_300dpi.png` and `official_page_200dpi.png` were rendered directly from that page with Poppler; the 300 dpi raster is `2481×3508`. No screenshot, resize, or resampling was used.
- `figure_crop_300dpi.png`, the 1:1 ROIs, and the grayscale image are pixel crops/conversion of that original 300 dpi page only.
- The direct Figure source is `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第02册_基础监督学习方法\V2-C05\fig_v2_c05_sigmoid.tex`. It is inserted at `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第02册_基础监督学习方法\chapters\V2-C05.tex:220`; the immediate explanatory paragraph is line 221. Caption source is line 60.

## Hard-gate outcome

| Gate | Result | Evidence |
|---|---|---|
| SOURCE_FONT_PASS | false | 23 of 26 visible elements have effective 8.7/9.2pt below 9.5pt; see `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | false | Math operators/prime in `E03_XTICK_MINUS, E06_YTICK_ONE, E12_NOTE_SYMM_MINUS, E14_NOTE_SYMM_EQUAL, E16_NOTE_SYMM_MINUS, E21_SLOPE_PRIME, E23_SLOPE_EQUAL` are below C-section operator threshold; see `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | false | Singleton role/script groups cannot be validly ratio-tested; strict protocol declares untestable/unknown a FAIL. Measurable peer groups are retained in CSV. |
| ROLE_RATIO_PASS | false | Required actual-pixel role hierarchy is not fully comparable across this one-panel CJK/math mix; source declaration ratios are recorded but do not substitute for actual-pixel evidence. |
| OVERLAP_PIXEL_COUNT | **241** across reported semantic pairs | `after_overlap_report.csv`; raw text foreground + final-PDF vector masks |
| CLIP_PIXEL_COUNT | 0 | `after_overlap_report.csv`; all mapped text bboxes within official raster |
| MIN_TEXT_CLEARANCE_PX | 0.00 (minimum across logged pairs) | `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | false | Repeated 8.7/9.2pt figure text violates the global reading hierarchy, regardless of basic legibility. |
| MATH_SEMANTICS_PASS | true | Logistic curve, center point, symmetry identity, $\sigma'(0)=1/4$, tangent, and $z=\pm a$ guides agree with source and nearby text. |
| TEXT_CONSISTENCY_PASS | true | Caption and line 221 state the same center symmetry / probability-range conclusion. |
| GRAYSCALE_PASS | true | Curve/markers/guide and tangent remain distinguishable through line styles/markers and contrast in `figure_crop_grayscale_300dpi.png`. |
| PAGE_INTEGRATION_PASS | true | Full 200 dpi page shows a centered graph with caption and the following explanatory paragraph, without page crop or abnormal break. |

## Explicit failures and minimum targeted repair

1. **ELEMENT_IDs `E03_XTICK_MINUS, E04_XTICK_A_NEG, E05_XTICK_A_POS, E06_YTICK_ONE, E07_YTICK_HALF_NUM, E08_YTICK_HALF_DEN, E09_LABEL_PROB_MAP, E10_NOTE_SYMM_SIGMA, E11_NOTE_SYMM_LPAREN, E12_NOTE_SYMM_MINUS, E13_NOTE_SYMM_A, E14_NOTE_SYMM_EQUAL, E15_NOTE_SYMM_ONE, E16_NOTE_SYMM_MINUS, E17_NOTE_SYMM_SIGMA_2, E18_NOTE_SYMM_A_2, E19_SLOPE_CN, E20_SLOPE_SIGMA, E21_SLOPE_PRIME, E22_SLOPE_ZERO, E23_SLOPE_EQUAL, E24_SLOPE_NUM, E25_SLOPE_DEN`** — native 300 dpi bboxes, source lines, declared/effective values, and C-section thresholds are all in `strict_failure_register.csv`. Figure-default/direct/note/formula text is **9.2pt** (source lines 5, 9, 12, 54--57); tick text is **8.7pt** (line 19). Both are below the 9.5pt hard gate. Minimum repair: raise every reader-visible figure font to at least 9.5pt (including PGFPlots ticks); then re-layout/re-render instead of globally scaling.
2. **ELEMENT_IDs `E03_XTICK_MINUS, E06_YTICK_ONE, E12_NOTE_SYMM_MINUS, E14_NOTE_SYMM_EQUAL, E16_NOTE_SYMM_MINUS, E21_SLOPE_PRIME, E23_SLOPE_EQUAL`** — each fails the >=22px basic math/operator rule at its native bbox/ink height. Minimum repair: after raising the base font, enlarge/re-style each individual operator/prime until its own raw-300dpi ink height reaches the cited threshold; do not only enlarge surrounding Chinese text.
3. **Illegal foreground overlap: `E01_AXIS_Y_SIGMA=116px; E06_YTICK_ONE=36px; E19_SLOPE_CN=89px`** — all affected source lines, native bboxes, zero-overlap threshold, and minimal repositioning directions are in `after_overlap_report.csv` and `strict_failure_register.csv`. Specifically: the $y=1$ reference line crosses `$\sigma(z)$` and the y=1 tick label; the $z=a$ guide crosses “中心斜率”.
4. **Same-class and actual role comparisons** are not complete for all role/script combinations. Under the strict protocol these are not passable as unknown. Minimum repair: after the font/layout correction, provide all per-role actual-pixel measures from a regenerated official candidate so each prescribed comparison has a legitimate same-script reference (or record a documented non-applicability accepted by the root protocol).

## Independent visual/semantic review

- Reading order is unambiguous: axes and sigmoid curve first, then the green points/guides, tangent/slope annotation, and symmetry identity.
- The curve matches $1/(1+e^{-z})$; it is monotone, hits $(0,1/2)$, approaches the 0/1 reference levels, and the plotted tangent source formula is $1/2+z/4$. The two guides at $z=\pm2$ support the displayed central symmetry identity.
- Caption: “逻辑斯谛函数把线性预测量映射为概率，并满足关于$(0,1/2)$的中心对称性。” It is one conclusion and agrees with the adjacent prose (“$z=0$时概率为$1/2$，且$\sigma(-z)=1-\sigma(z)$”).
- The white label background prevents the blue curve from passing through “概率映射”; the boxed symmetry formula has a logged node-border clearance above 5 px. However, the masks show the three explicit text–graphic collisions listed above. No clipping was found.

## Evidence inventory

- `official_page_300dpi.png`, `official_page_200dpi.png`
- `figure_crop_300dpi.png`, `standalone_300dpi_from_official.png`, `figure_crop_grayscale_300dpi.png`
- `roi_ticks_axis_1to1_300dpi.png`, `roi_annotations_1to1_300dpi.png`
- `semantic_mask_TEXT_300dpi.png`, `semantic_mask_LINE_ARROW_MARKER_300dpi.png`, `semantic_masks_figure_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `strict_failure_register.csv`, `after_text_measurement_overlay_300dpi.png`
- `audit_provenance.json`

No SA3 is authorized: this SA1 result is FAIL.
