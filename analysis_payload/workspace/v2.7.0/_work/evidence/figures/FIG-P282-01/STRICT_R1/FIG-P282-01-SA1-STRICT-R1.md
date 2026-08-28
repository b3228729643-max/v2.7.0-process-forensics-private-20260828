# FIG-P282-01｜独立 SA1 严格 R1 复核报告

RESULT: **FAIL**

FIGURE_ID: `FIG-P282-01`（图 17.1）  
章节: 第 17 章《最大熵模型》  
候选: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r92_fullbook/main_full.pdf`（813 页、4,933,704 bytes）  
图源: `src/绘图源码/第03册_优化模型与序列模型/V3-C01/fig_v3_c01_simplex.tex`  
证据根: 本目录 `STRICT_R1/`

## 独立性、定位和方法

本 SA1 只读复核指定候选 PDF、图源、直接章节正文和公共 caption 样式；未读取 FIG-P282-01 的任何既往 SA1/SA2/SA3/root 报告、旧证据结论或中央库存，未修改源码/公共模板/状态。

在官方候选中检索完整题注，唯一命中物理页 **303**（印刷页码 290），而非任务卡的 323。这里以实际候选页 303 为准；该页码差异作为需要主线程修正的可复现元数据问题。

原始栅格证据由 `pdftoppm` 直接产生：300 dpi 为 2481×3508px，200 dpi 为 1654×2339px；没有任何缩放或重采样。每个文字 PDF/vector bbox 直接映射到 300 dpi 网格，以局部背景差 `>=20/255` 的像素为墨迹。语义对象掩膜覆盖每个文本标签、题注/直接正文、单纯形边界、等高线组、两条约束的延长线/可行段、焦点引线和 marker；逐对距离/交叠在 `after_overlap_report.csv` 中可复算。

## 9.2.1 / 9.3 审核字段

| 字段 | 结论 |
|---|---|
| MATH_SEMANTICS | PASS：两约束段交点 `(0.4133292,0.2886854)` 与 marker `(0.4133333,0.2886751)` 的坐标差分别为 `4.13e-6,1.03e-5`；反变换为 `(p1,p2,p3)=(0.4199983,0.2466566,0.3333452)`，和为 1，熵为 `1.0758153<ln3` |
| TEXT_CONSISTENCY | PASS：图中变量、等高线数值、题注、图后直接正文一致；题注为一条读图结论 |
| READING_ORDER | PASS：单纯形/约束/等高线先建立可行域，再由金色点和引线落到唯一可行最大熵点 |
| SOURCE_FONT_AUDIT | **FAIL**：19 个 source effective_pt 低于 9.5pt |
| PIXEL_HEIGHT_AUDIT | **FAIL**：6 个独立基本 `=` 运算符为 11/13px，低于 22px |
| SAME_CLASS_RATIO_AUDIT | PASS：所有同脚本同语义类位于 `[0.92,1.08]`，max/min `<=1.08` |
| ROLE_RATIO_AUDIT | PASS：constraint BASE=33px；focus=1.0303、contour=0.9848、vertex-formula=1.0606 |
| OVERLAP_PIXEL_COUNT | PASS：0；229 个语义对象对均为 0 |
| CLIP_PIXEL_COUNT | PASS：0 |
| MIN_TEXT_CLEARANCE_PX | PASS：文字—文字 bbox 最小 17.00px（阈值 4px）；文字—图形前景最小 17.98px（阈值 3px）；文字—页边最小 259px（阈值 6px） |
| VISUAL_HARMONY / FONT_AND_DENSITY | **FAIL**：空间关系协调，但 subminimum 标签不能以可读性抵消字号门 |
| LAYOUT | PASS：没有压线、裁切或异常留白 |
| GRAYSCALE | PASS：实线/虚线/点划线/marker 在灰度中仍可区分 |
| CAPTION | PASS：题注、图后解释和图内对象一致 |
| PAGE_INTEGRATION | PASS：完整页 200 dpi 中图、题注、相邻正文连续，无孤行 |
| TECHNICAL | PASS：独立 standalone harness 成功写出 1 页 PDF；官方候选可读取 |

单面板、无 node border、无 panel border、无 legend、无 arrowhead；这些项目为已确认 N/A。跨面板比值同为单面板 N/A。

## 逐元素硬失败（原生 300 dpi bbox）

每行均给出 ELEMENT_ID、图源行、native bbox、门槛和最小定向修复。H_ink 仅作为实测附加证据；source-font gate 和 pixel gate 任一失败即 FAIL。

| ELEMENT_ID | 源行 | 文本 / native bbox(px) | 失败门槛 | 最小修复方向 |
|---|---|---|---|---|
| E01_FOCUS_UNIQUE | 9;147–148 | 唯一可行 `(1607,2319)-(1764,2362)`；H=34 | effective 9.40pt `<9.50pt` | 第 9 行 focus style 提升至安全 10pt，并保留该引线净空 |
| E02_FOCUS_MAXENT | 9;147–148 | 最大熵点 `(1607,2381)-(1764,2424)`；H=34 | effective 9.40pt `<9.50pt` | 同上，保持两行同角色一致 |
| E03_CONTOUR_HEADER | 13;149–150 | 等高线 `(1607,1898)-(1720,1939)`；H=32 | effective 9.00pt `<9.50pt` | 第 13 行 contour style 至少 10pt，重测角色比 |
| E04_OUTER_CJK | 13;149–150 | 外层：`(1607,1956)-(1720,1997)`；H=33 | effective 9.00pt `<9.50pt` | 同上 |
| E05_OUTER_H | 13;149–150 | H `(1719,1957)-(1755,1996)`；H=28 | effective 9.00pt `<9.50pt` | 同上 |
| E06_OUTER_EQUAL | 13;149–150 | = `(1766,1957)-(1797,1996)`；H=13 | effective 9.00pt `<9.50pt`；operator 13px `<22px` | 改为“熵值 0.80”等无孤立小等号表述并放大整行 |
| E07_OUTER_VALUE | 13;149–150 | 0.80 `(1807,1957)-(1884,1996)`；H=27 | effective 9.00pt `<9.50pt` | 放大 contour/value 字号到至少 10pt |
| E08_MID_CJK | 13;149–150 | 中层：`(1607,2015)-(1720,2056)`；H=32 | effective 9.00pt `<9.50pt` | 同 E03 |
| E09_MID_H | 13;149–150 | H `(1719,2015)-(1755,2055)`；H=28 | effective 9.00pt `<9.50pt` | 同 E03 |
| E10_MID_EQUAL | 13;149–150 | = `(1766,2015)-(1797,2055)`；H=13 | effective 9.00pt `<9.50pt`；operator 13px `<22px` | 改为“熵值 0.95”等无孤立小等号表述并放大整行 |
| E11_MID_VALUE | 13;149–150 | 0.95 `(1807,2015)-(1882,2055)`；H=27 | effective 9.00pt `<9.50pt` | 放大 contour/value 字号到至少 10pt |
| E12_INNER_CJK | 13;149–150 | 内层：`(1607,2073)-(1720,2114)`；H=33 | effective 9.00pt `<9.50pt` | 同 E03 |
| E13_INNER_H | 13;149–150 | H `(1719,2074)-(1755,2113)`；H=28 | effective 9.00pt `<9.50pt` | 同 E03 |
| E14_INNER_EQUAL | 13;149–150 | = `(1766,2074)-(1797,2113)`；H=13 | effective 9.00pt `<9.50pt`；operator 13px `<22px` | 改为“熵值 1.05”等无孤立小等号表述并放大整行 |
| E15_INNER_VALUE | 13;149–150 | 1.05 `(1807,2074)-(1880,2113)`；H=27 | effective 9.00pt `<9.50pt` | 放大 contour/value 字号到至少 10pt |
| E16_CONSTRAINT_1_CJK | 17;151–152 | 约束 `(796,1968)-(873,2010)`；H=33 | effective 9.20pt `<9.50pt` | 第 17 行 constraint style 至少 10pt |
| E17_CONSTRAINT_1_DIGIT | 17;151–152 | 1 `(881,1969)-(901,2008)`；H=25 | effective 9.20pt `<9.50pt` | 同 E16 |
| E18_CONSTRAINT_2_CJK | 17;153–154 | 约束 `(1285,1811)-(1363,1853)`；H=33 | effective 9.20pt `<9.50pt` | 同 E16 |
| E19_CONSTRAINT_2_DIGIT | 17;153–154 | 2 `(1371,1812)-(1390,1852)`；H=25 | effective 9.20pt `<9.50pt` | 同 E16 |
| E22_VERTEX_1_EQUAL | 155 | = `(617,2569)-(646,2610)`；H=11 | operator 11px `<22px` | 写成 `p_1` 为 1（或等价无孤立小运算符表达），并保持顶点标签至少 10pt |
| E26_VERTEX_2_EQUAL | 156 | = `(1648,2569)-(1678,2610)`；H=11 | operator 11px `<22px` | 同 E22 |
| E30_VERTEX_3_EQUAL | 157 | = `(1132,1720)-(1162,1760)`；H=11 | operator 11px `<22px` | 同 E22 |

未列为失败的 vertex 基准 9.60pt 和其自然 script 均有明确来源；自然 script 符合合法派生规则。此事实不抵消以上三个 `=` 的独立像素失败。

## 零重叠与最小净空可复现结果

- 所有文字—文字、文字—线/等高线/引线、文字—marker 组合：非法前景交叠为 0；报告共 229 条 PASS 记录。
- 最近文字—图形对象：`CONSTRAINT_1` 与 `G03_CONSTRAINT_1_EXTENSION`，0 像素交叠、最近前景距离 17.98px（门槛 3px）。
- 最近文字—文字对象：`CONTOUR_MID` 与 `CONTOUR_INNER`，0 像素交叠、bbox 距离 17.00px（门槛 4px）。
- 其他最紧邻文本—文本对 `CONTOUR_HEADER`/`CONTOUR_OUTER` 为 17.00px，`FOCUS_1`/`FOCUS_2` 为 19.00px。
- 所有 reader text 到官方页边界的最小距离为 259px；所有文字、线、marker 均无裁切。

## 四视图、图文和页面复核

1. `official_page_303_200dpi.png`：完整页层级、题注和图后正文均完整；图页没有分页破坏。
2. `figure_crop_300dpi.png`：单纯形顶点、约束延长/可行段、三层等高线和金点关系正确，但标签源级字号不足。
3. `standalone_300dpi.png`：当前图源独立 harness 重编译得到，图形关系与官方局部一致；该视图不替代官方候选的 300dpi 测量。
4. `grayscale_300dpi.png`：颜色移除后结构仍由实线、虚线、点划线和 marker 形状区分。

题注与紧随正文都正确表达“概率归一化给出单纯形，已知统计量给出线性约束，可行集为交集，最大熵只在交集内选取”。公式数值与图形相符：三条闭合曲线围绕均匀分布，且约束交点的熵高于内层 `1.05` 但低于 `ln3`，所以它被作为两约束共同可行时的唯一点并无矛盾。

## 结论与后续

`SOURCE_FONT_PASS=false` 和 `PIXEL_HEIGHT_PASS=false` 已足以按第 9.2.1/H 直接判 **FAIL**；不得启动 SA3。应回到唯一 SA2 写者进行定向修复、重建当前官方候选、重新产出全部原始 300dpi 证据，然后分配新的独立 SA1。
