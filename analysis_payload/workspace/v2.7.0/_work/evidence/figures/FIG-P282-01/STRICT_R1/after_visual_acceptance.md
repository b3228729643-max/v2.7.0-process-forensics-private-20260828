# FIG-P282-01｜after visual acceptance｜独立 SA1 严格 R1

RESULT: **FAIL**

本记录只使用当前官方候选 `src/build/strict_current_r92_fullbook/main_full.pdf`（813 页、4,933,704 bytes）和指定图源；未读取任何既往 SA1/SA2/SA3/root 结论，未修改源码或状态。

## 候选、定位与原始栅格证据

- 官方 PDF 中检索题注文字“概率单纯形上的熵等高线与线性约束”仅命中一次：物理页 **303**（页内印刷页码 290）。任务卡中的 323 与当前候选不一致，须由主线程更新其元数据；本复核以候选实际页 303 为准。
- `official_page_303_300dpi.png`：直接 `pdftoppm -r 300` 渲染，2481×3508 px；未缩放、未重采样。
- `official_page_303_200dpi.png`：直接 `pdftoppm -r 200` 渲染；未缩放、未重采样。
- PDF 文本/vector bbox 直接映射到该 300 dpi 像素网格。文字前景采用局部背景差 `ΔRGBmax >=20/255`；像素高度为前景行跨度。
- 文本掩膜按语义标签、公式子元素、题注及直接正文建立。图形掩膜分别建立为：单纯形边界、等高线组、约束 1/2 的完整延长线、约束 1/2 的可行段、焦点引线和焦点标记；不是宽泛合并掩膜。详见 `after_overlap_report.csv`、`semantic_masks_300dpi.png`。

## 9.2.1 硬门判定矩阵

| 项目 | 结果 | 原始证据 / 说明 |
|---|---:|---|
| SOURCE_FONT_PASS | false | 19/38 个元素源级 effective_pt 仅 9.00、9.20 或 9.40pt，低于 9.50pt |
| PIXEL_HEIGHT_PASS | false | 6 个独立 `=` 运算符为 13px 或 11px，低于 22px |
| SAME_CLASS_RATIO_PASS | true | 每个同脚本、同语义组均在 `[0.92,1.08]` 且组内 max/min `<=1.08` |
| ROLE_RATIO_PASS | true | 普通约束标签为 BASE=33px；focus=1.0303、contour=0.9848、vertex formula=1.0606，均在相应门内 |
| OVERLAP_PIXEL_COUNT | 0 | 229 个语义对象对均 PASS；最近对象对亦给出可复现距离 |
| CLIP_PIXEL_COUNT | 0 | 所有文字/图形 vector bbox 均在页内，1:1 原图无裁切 |
| MIN_TEXT_CLEARANCE_PX | 17.00 | `CONTOUR_MID`–`CONTOUR_INNER` 及 `CONTOUR_HEADER`–`CONTOUR_OUTER`；要求 `>=4px` |
| 最小文字—图形前景距离 | 17.98 | `CONSTRAINT_1`–`G03_CONSTRAINT_1_EXTENSION`；要求 `>=3px` |
| 最小文字—页边距离 | 259 | 要求 `>=6px` |
| VISUAL_HARMONY_PASS | false | 空间/层级本身可读，但 9.00–9.40pt 图内标签违反硬字号门，不能以“观感尚可”判通过 |
| MATH_SEMANTICS_PASS | true | 两条可行约束段唯一相交；交点换回概率为 `(0.419998,0.246657,0.333345)`，和为 1，`H=1.075815<ln3=1.098612`，与金色 marker 坐标误差 `<1.1e-5` |
| TEXT_CONSISTENCY_PASS | true | 顶点 `p_1,p_2,p_3`、`H=0.80/0.95/1.05`、题注和紧随正文均一致：可行集为单纯形与线性约束之交，最大熵点只在该交内选择 |
| GRAYSCALE_PASS | true | 实线、虚线、点划线/浅色延长线和 marker 在 `grayscale_300dpi.png` 中仍可分辨 |
| PAGE_INTEGRATION_PASS | true | 图、题注和随后正文均留在同一页，无孤行、裁切或异常空白 |

单面板图，无 panel border 或 node border；这些对象类别为已知 N/A，而非未知。无图例、无箭头头部。跨面板一致性同样为 N/A（单面板）。

## 四视图与 1:1 ROI 结论

- 完整页 200 dpi：图位于两段解释框之后，题注及直接正文相邻，页内融合正常。
- 官方局部 300 dpi：约束 1/2、三条熵等高线、可行交点和引线都可追踪；未见压线或裁切。
- 独立图 300 dpi：指定 standalone harness 在项目内缓存下成功编译，`standalone_300dpi.png` 与官方局部的几何/文字关系一致。
- 灰度 300 dpi：颜色撤除后实线、虚线、点划线和标记形状仍提供独立编码。
- 关键原始 1:1 ROI：`roi_contour_labels_1to1_300dpi.png`、`roi_focus_leader_1to1_300dpi.png`、`roi_top_vertex_1to1_300dpi.png`、`roi_lower_vertices_1to1_300dpi.png`、`roi_constraint_1_1to1_300dpi.png`、`roi_caption_direct_text_1to1_300dpi.png`。

## 硬失败与最小修复方向

完整逐元素 source/bbox/H_ink 表在 `after_font_audit.csv` 与 `after_pixel_measurements.csv`，本记录只归纳其可复现失败簇：

1. `E01,E02`：图源第 9 行 focus label 为 9.40pt，低于 `>=9.50pt`。将该样式和所有同层级标签提升到安全值（建议 10pt），不得整体缩图。
2. `E03–E15`：图源第 13 行 contour label 为 9.00pt，低于 `>=9.50pt`；其中三处 `=`（`E06,E10,E14`）原生 H_ink=13px，低于 `>=22px`。
3. `E16–E19`：图源第 17 行约束标签为 9.20pt，低于 `>=9.50pt`。
4. `E22,E26,E30`：图源第 155–157 行顶点公式的 `=` 原生 H_ink=11px，低于 `>=22px`，尽管其 9.60pt 基准字号本身合格。

最低风险的修复不是仅升高整个图：统一将第 9/13/17/19 行的读者文字提升至至少 10pt，随后用不含孤立小 `=` 的语义文本重排等式（例如“熵值 0.80”“`p_1` 为 1”），腾出空间并重新做全量 300 dpi 审计。还需把任务卡的物理页元数据从 323 校正为当前候选的 303。修复后必须重新构建官方全书并由新的独立 SA1 复核；本 SA1 FAIL，不能启动 SA3。
