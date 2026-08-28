# FIG-P157-01-SA3-STRICT-R6-R93

RESULT: **PASS**

## Independent scope and identity

- Frozen candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`
- Identity located from final-PDF caption: physical PDF page **170**, printed page **157**, figure **图 10.1**.
- Figure source read: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex`; direct chapter context read: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C10.tex:255-259` and caption line 61.
- No prior evidence, reviewer report, central status, manifest, or non-permitted shared style source was read.

## Coverage

Every visible text span in the chart/caption, each of the 15 final-PDF figure drawing objects, all curves/reference/marker/leader/axes/arrowheads, all panel and annotation backgrounds, and every independent foreground-pair relation were enumerated. The output includes raw 1:1 ROI, independently derived mask, overlay, pair raw/overlay/overlap mask where same-colour or bbox-near, text span JSON, and vector-object JSON.

There is no visible formula block, base arithmetic operator, Latin lower-case item, Greek item, superscript/subscript/limit, tick label, legend, panel label, or node label in this chart/caption: these classes are **N/A**. The caption number `10.1` is instead a separate PDF span with its own DIGIT measurement.

## Exact hard-gate conclusion

`SOURCE_FONT_PASS=true`. The current figure source, `common/figure-style-v2.3.0.tex:33-39`, `common/statlearnbook.sty:305-306`, and `合并总册/main.tex:7` restore the actual chains: local 9.2pt/8.8pt labels ×1.12; axis-title 9.4pt declaration superseded by later `slfig axis` `\small=10pt`, then ×1.12; caption `\small=10pt` at scale 1.00.

All generated values and paths are in [after_visual_acceptance.md](after_visual_acceptance.md), [after_font_audit.csv](after_font_audit.csv), [after_pixel_measurements.csv](after_pixel_measurements.csv), [after_overlap_report.csv](after_overlap_report.csv), and [after_edge_clip_report.csv](after_edge_clip_report.csv).

## Mathematical and text checks

- Training curve `0.36+3.35 exp(-0.34x)` is strictly decreasing on the shown domain.
- Validation curve `1.08+0.105(x-5.25)^2` has its unique displayed minimum at `(5.25,1.08)`; the vertical reference and gold marker use that same coordinate.
- The training label's leader begins at `(7.15,0.655)`; source-equation recomputation gives `0.654629`.
- Caption and the immediately following reading instruction match the in-figure labels and gray-scale decoding.

## Required action

If any aggregate gate is false, use its object/pair ID and evidence path for a targeted repair, rebuild the frozen candidate, and rerun this audit. The prepass in `prepass_SUPERSEDED/` is expressly superseded by this corrected run.
