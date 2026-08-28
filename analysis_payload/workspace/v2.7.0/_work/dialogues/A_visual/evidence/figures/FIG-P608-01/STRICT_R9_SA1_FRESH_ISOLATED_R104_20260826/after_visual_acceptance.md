# FIG-P608-01 — R104 fresh isolated SA1 visual acceptance

- `HANDOFF_ID`: `A-R104-P608-SA1-FRESH-ISOLATED-20260826`
- reviewer role: fresh isolated read-only SA1
- official candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- independently located physical page: `661`
- printed page: `648`
- figure number: `32.8`
- source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex`

## Identity and native views

The page was located from the R104 PDF text layer using the current-source phrases “预热段”, “保留样本”, “运行均值” and the caption beginning “舍弃前…”. No old page number or old P608 evidence was used.

| Evidence | Native dimensions | Native crop on 300 dpi page |
|---|---:|---:|
| `full_page_200dpi.png` | 1654 × 2339 | full page |
| R104 full-page 300 dpi render | 2481 × 3508 | full page |
| `figure_crop_300dpi.png` | 1930 × 981 | `[250,895,2180,1876]` |
| `standalone_300dpi.png` | 1543 × 864 | `[437,916,1980,1780]` |
| `grayscale_300dpi.png` | 1930 × 981 | same crop as figure crop |

PDF page size is `595.2760 × 841.8900 pt`. All measurement coordinates are from the unresized native 300 dpi R104 render. The UID object boundary is the standalone TikZ graphic. The caption and surrounding page prose are audited in the figure-crop/full-page view ledgers but are not mixed into the standalone figure-object denominator.

## Object, glyph, rule, and pair closure

- visible text glyphs: `68/68`
- semantic graphic/background objects: `21/21`
- PDF drawing records mapped exactly once: `58/58`
- visible `GRAPHIC/MATH_RULE` objects: `6/6`
- total objects: `89`
- all unordered pairs: `C(89,2) = 3916/3916`
- ordinary portable mask PNG files: `89/89`
- empty masks: `0`
- glyph contact rows actually reviewed: `68/68`
- math-rule contact rows actually reviewed: `6/6`
- overlap/critical ROI rows actually reviewed: `23/23`

The four bars forming the two custom equals signs are separate rule objects. Each equals-sign composite has a native visible height of `23 px`, meeting the `22 px` baseline mathematical-operator gate. The two overlines are separate nonempty rule objects and were not merged into their `X` glyphs.

## Font and pixel gates

- source ordinary text: `9.6 pt` effective, no `resizebox`, `scalebox`, `scale`, or `transform shape`
- source axis/title text: `10.8 pt` effective
- natural TeX scripts: `7.56 pt` from a `10.8 pt` base; minimum native ink height `18 px`, above the `15 px` script gate
- CJK ink heights: `34–40 px`, all at or above `30 px`
- digit ink heights: `26–27 px` for ordinary digits and `22 px` for natural script digits, all passing their applicable gates
- Latin/math uppercase `X`: `30 px`, above `24 px`
- base lowercase `t`: `25–28 px`, above `17 px`; natural-script `t`: `21 px`, above `15 px`
- commas: four same-codepoint calibrants, `H` ratio `1.0`, area ratio `1.0`
- ellipses: two same-codepoint calibrants, `H` ratio `1.0`, area ratio `1.0`
- decimal points: three same-codepoint calibrants, `H` ratio `1.0`, area ratio `1.0`
- source role ratios: annotation `1.0× BASE`; axis/panel title `1.125× BASE`, within the required role bands
- cross-panel same-codepoint values (`X`, script `6`, math colon, script `t`) match exactly in native pixel height
- `FONT_VISUAL_HARMONY_PASS=true`

R168 advisory only: PDF text metadata reports approximately `9.564/10.760/7.532 pt` for source `9.6/10.8/7.56 pt`; this is a subpixel transformation/metadata difference without any visible imbalance. Mixed-outline height ratios for comma versus ellipsis and for script digit/colon/letter are not treated as same-contour comparisons; every same-codepoint calibration and all manual contact cells pass.

## Geometry

- `OVERLAP_PIXEL_COUNT=0` for every non-whitelisted illegal relationship
- `CLIP_PIXEL_COUNT=0`
- minimum independent text–text clearance: `20 px` (`>=4 px`)
- minimum text/formula–line, arrow, marker, rule, or texture clearance: `13 px` (`>=3 px`)
- minimum cross-panel reader-element clearance: `154 px` (`>=8 px`)
- minimum text-to-standalone-image-edge clearance: `20 px` (`>=6 px`)
- node-border and legend categories: justified `N/A` because this figure has no nodes or legend

All actual mask intersections were opened in `raw/A/B/intersection/1× overlay/8× nearest` form. They are limited to intentional coordinate-system construction, plotted data over its designated hatch background, the `t=1` endpoint on the declared `xmin=1` axis boundary, running-mean crossings of the target-value reference, and hatch-boundary connections. No text or formula overlaps any unrelated foreground object.

## Semantics, grayscale, and page integration

- all 20 trace values match the current source
- warm-up is correctly labeled `t=1,…,5`
- retained samples are correctly labeled `t=6,…,20`
- all 15 retained-sample running means were independently recomputed and match the source coordinates; the final value at `t=20` is `2.0000`
- `X_t`, `\overline X_{6:t}`, the custom equals signs, overlines, and target value `2` are visually and mathematically coherent
- PDF text-layer `U+2236` for the STIX math colon is the rendered math-colon semantics of source `:` and is not a wrong codepoint
- no tofu, missing glyph, wrong visible codepoint, unreadable text, clipping, or illegal overlap was observed
- grayscale differentiation and full-page integration both pass

## Manual-ledger conclusion

- glyph manual rows: `68 PASS`
- math-rule manual rows: `6 PASS`
- overlap/critical ROI manual rows: `23 PASS`
- view manual rows: `5 PASS`
- panel/role/script manual rows: `23 PASS`
- final CSV/JSON/Markdown machine crosscheck: `PASS`

`SA1_DECISION=PASS`

`NEXT_STATUS=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

`A_LOCAL_PASS=NOT_CLAIMED`

