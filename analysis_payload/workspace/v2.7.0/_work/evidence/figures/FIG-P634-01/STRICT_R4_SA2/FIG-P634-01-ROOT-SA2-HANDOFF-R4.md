# FIG-P634-01 根线程复核｜SA2 STRICT R4 交权

结论：**接受为“可进入官方 R94 构建”的 SA2 本地候选**。这不是官方全书 SA1、SA3 或最终逐图 PASS。

## 根线程独立回读

- 唯一业务源码为 `fig_v5_c04_coordinate_sweep.tex`。根线程已对 `source_before_R93.tex` 执行完整 diff；未发现公共样式、正文、合并入口、中央清单或状态的 SA2 越权修改。
- 根线程已查看本地原生 300 dpi 图裁、整页、灰度、测量 overlay，以及斜线纹理的绘制前 mask、真实不透明白色 halo、最终可见纹理和最近邻 8× paint-order 证据。
- 当前可见数学记号保持正文一致的小写 `j/d/t`，状态为 `x^{[j]}`、`x^{[d]}`、`x^{(t)}`；已作废的大写键方案没有保留。固定扫描顺序、左侧同轮新值、右侧上一轮旧值与仅轮末记录的语义均在图、题注和 alt 中闭合。
- 公共自动题注、同页引用、`.aux`、`.lof` 与 LoF 渲染均为标准 `图 33.3`；没有 `labelformat=empty`、手工“图 33 之 3”或重复题注。编号句点保留独立原始 mask，并按题注编号分隔标点的上下文可辨性审计。
- 本地源级字号 70/70 PASS，最小有效基字号 9.6pt；199 个读者 glyph 无 FAIL，12 枚自然脚本括号／方括号独立审核通过；同脚本同语义角色与角色层级均使用 actual raw `H_ink`，70/70 PASS。
- `after_overlap_report.csv` 覆盖 87 个对象的 3741 个唯一 pair：非法最终可见 foreground overlap 为 0，clip 为 0；独立 text-text 最小 23px、text-line/arrow 最小 15px、text-node-border 最小 6px。
- 四个斜线节点使用源码真实 alpha-1 白色 halo。审计同时保留 PRE_OCCLUSION_TEXTURE、halo 与 FINAL_VISIBLE_TEXTURE，未按文字轮廓或中点切分；7 个同节点文字／公式—最终可见纹理 pair 的 overlap 均为 0，净空为 7/5/8/5/7/7/14.04px，最小 5px。
- `audit_summary.json` 的 `NUMERIC_GATES_PASS`、`LOCAL_SA2_GATES_PASS` 与 `machine_consistency.json` 均为 true/PASS；正式报告及视觉记录已清除旧 J/D/T、手工题注和旧纹理口径。

## 后续边界

根线程须从当前唯一源码构建官方 R94，全书独立重定位图 33.3，并直接从官方 PDF 原生 300 dpi 重做整页、图裁、逐 glyph、全 pair、纹理、题注、灰度与页面融合证据。只有全新独立 SA1 通过后才可进入隔离 SA3；SA2 本地证据不得迁移为最终 PASS。
