# FIG-P429-01 root validation — STRICT R1

ROOT_RESULT: CONFIRM_SA1_FAIL

- Frozen official input: `strict_current_r93_fullbook/main_full.pdf`, physical page 466, printed page 453, 图 24.1.
- Root read the corrected formal report and all aggregate CSVs, opened the native figure crop/text overlay, and inspected 1:1 raw/separated-mask evidence for all three source-title paths and both evidence-note paths.
- Source floor failure is confirmed: 14/21 visible text/formula elements use 9.0, 9.2, or 9.4 pt with no compensating scale. The inline base relation arrow `→` is independently measured at 16 px, below the 22 px operator threshold.
- Eight true text--line/arrow relations fail. The three source paths and their arrowheads visibly run through `聚类`, `降维`, and `概率建模`; two outgoing evidence arrows also pass through `样本分组` and `潜变量生成观测`. Pair counts sum to 494 because some line/head masks share pixels; the final native unique illegal foreground union is 466 px. These are not intended node connections, mask dilation, broad-bbox inference, or paint-order artefacts.
- The corrected report properly marks the neighbouring middle/right `x` node-border proximity as N/A because the note is external to those nodes. Applicable own-node text-border clearance is 12.25 px and passes. All 68 edge rows pass and clip count is 0.
- Available full-page/crop/grayscale views preserve mathematics, text consistency and page integration, but visual harmony fails from the visible arrow-through-text collisions. A genuine independent standalone 300 dpi view is also missing, so the four-view evidence gate cannot pass.

Disposition: reject current candidate; next role is SA2 only. SA3 is prohibited until a rebuilt official candidate has complete four-view evidence and a fresh strict SA1 PASS.
