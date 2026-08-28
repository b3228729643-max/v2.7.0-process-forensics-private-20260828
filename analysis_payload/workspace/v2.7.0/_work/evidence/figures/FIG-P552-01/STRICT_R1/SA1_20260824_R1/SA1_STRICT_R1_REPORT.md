# FIG-P552-01（图30.3）｜独立 SA1 严格视觉与数学首审

## 1. 身份、覆盖与冻结输入

- 任务：`FIG-P552-01`；角色：独立、只读 SA1；轮次：`STRICT_R1/SA1_20260824_R1`。
- 冻结候选：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`。
- 独立定位：物理 PDF 第 **596** 页，印刷第 **583** 页，**图30.3**。
- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_return_time.tex`；相邻正文复核 `V5-C01.tex:410--432`。
- 覆盖：41 个独立语义文字对象、154 个可见字形（运算符、标点、上下标单列）、43 个矢量线/箭头/节点边框组件、2,583 个成对关系（820 TEXT--TEXT，其中跨面板 380；984 TEXT--LINE/ARROW；779 TEXT--NODE_BORDER）。题注两自然行按一个 `CAPTION_PARENT`，结论框两行按一个 `CONCLUSION`，未制造伪文字对。

## 2. 渲染、四视图与原生像素方法

`full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png` 和 `grayscale_300dpi.png` 均来自冻结 PDF。300 dpi 的权威网格先直接 rasterize 整个物理页，再以该网格的像素切片生成图裁；全程没有二次缩放。direct-clip 路径因 clip 原点可能改变抗锯齿相位，已标记 `SUPERSEDED`，不进入最终指标。`measurement_consistency.json` 固定此口径。`masks/figure_foreground_raw_300dpi.png` 用相对局部背景差 `>=20/255` 建立前景，未作形态学膨胀。

每个字形以 PDF char bbox 截取自身 raw 前景，保存于 `masks/glyph_raw/`；语义对象 raw mask 位于 `masks/text_raw/`。每个线、箭头、箭头头、刻线和节点边框从最终 PDF 的绘制路径独立重建并以同一 300 dpi 全页网格渲染，保存于 `masks/vector_raw/`；`masks/vector_visible_raw/` 保留最终 paint-order 可见层作诊断，不能替代独立矢量关系检查。所有 31 个失败/临界关系均保留原图 ROI、A/B 分离 mask、交集 mask、overlay 与 `*_raw_8x_nn.png`、`*_overlay_8x_nn.png`、`*_overlap_8x_nn.png`。索引见 `critical_pair_index.csv` / `critical_pair_manifest.md`；8×文件只作最近邻人工核看，不参与测量。

## 3. 源级有效字号

`SOURCE_FONT_PASS: false`，**38/41** 语义对象低于 9.5 pt。

| 角色 / 对象 | 有效 pt | 数量 | 判定 |
|---|---:|---:|---|
| 面板标题 | 9.4 | 2 | FAIL |
| 节点标签（event/hit） | 9.2 | 16 | FAIL |
| 区间文字 / 结论框 | 9.2 | 3 | FAIL |
| 刻度 | 8.6 | 16 | FAIL |
| `$t>0$ 才计入`注记 | 8.8 | 1 | FAIL |
| 时间轴 `$t$` | 10.0 | 2 | PASS（继承全局 `every node/.append style={font=\small}`） |
| 题注 | 10.0 | 1 | PASS（`captionsetup{font={small,...}}`） |

完整 declared/effective/来源行及字体继承规则在 `after_font_audit.csv`。没有 graphics scale；`GRAPHICS_SCALE=1.0`。

## 4. 300 dpi 逐字形门

`PIXEL_HEIGHT_PASS: false`，**10/154** 字形未过自身门槛（不以父公式、整行或邻字高度替代）。失败对象如下：

- 上/下区间标签的全角逗号各 11 px（>=30）、全角冒号各 20 px（>=30）、独立 `=` 各 13 px（>=22）；
- 结论公式的 `∞` 为 18 px（>=22）；
- 题注的句点为 7 px（>=22）、全角冒号 22 px（>=30）、全角逗号 13 px（>=30）。

每一字形的 PDF bbox、raw H_ink、阈值、字体、源码行和结论在 `after_pixel_measurements.csv`；自然产生的脚本以 >=9.5 pt 基公式条件另列，未被父公式代替。

## 5. 同类、角色比例与字体视觉协调

`SAME_CLASS_RATIO_PASS: false`。Goal D 的正式口径为每个可见字形的**实际未膨胀 raw `H_ink_px` / 同面板、同角色、同脚本中位数**，不是 source pt 或 PDF span-size 代理。154 行中有 **34** 行不在 `[0.92,1.08]`，完整行和各自的 raw H_ink 在 `same_class_ratio_audit.csv`。PDF span size × 300/72 仅保留为诊断列，不用于 PASS。

`ROLE_RATIO_PASS: false`。Goal E 与跨面板检查同样直接用实际 raw H_ink：annotation lower 为 TOP/BOTTOM `29/25=1.160`、operator 为 `24.5/18=1.361`、natural-script 为 `27/23=1.174`，均高于 1.10；PANEL_TITLE lower 为 `20/29=1.450`。以节点正文 raw BASE=30 px 时，时间轴标题=26 px（**0.867**，低于 `[1.00,1.18]`）、刻度=25 px（**0.833**，低于 `[0.95,1.10]`）、题注=37 px（**1.233**，高于 `[0.95,1.10]`）。见 `role_ratio_audit.csv`。

`FONT_VISUAL_HARMONY_PASS: false`，同时 `VISUAL_HARMONY_PASS: false`。原因是有效字号从 8.6 到 10.0 pt 断裂且多数承担信息角色不足 9.5 pt；实际 raw H_ink 的同类、跨面板和角色比例亦有上述失败。允许“适当缩小”不适用于此候选：它已低于硬下限，且缩小无法修复比例或净空。

## 6. 零重叠、净空与裁切

`OVERLAP_PIXEL_COUNT: 221`（4 个 unique failure pair 的去重和），`OVERLAP_FAIL_PAIR_COUNT: 4`，`PAIR_CLEARANCE_FAILURE_COUNT: 4`，`CLIP_PIXEL_COUNT: 0`；因此本节 **FAIL**。唯一有效算式为 **22 + 55 + 33 + 111 = 221**。

| 失败 pair | 类型 | 分离 raw 交叠 px | raw 净空 |
|---|---|---:|---:|
| `TOP_INTERVAL__TOP_INTERVAL_ARROW` | TEXT--LINE_ARROW | 22 | 0 |
| `BOTTOM_NOTE__BOTTOM_NODE_BORDER_1` | TEXT--NODE_BORDER | 55 | 0 |
| `BOTTOM_INTERVAL__BOTTOM_INTERVAL_ARROW` | TEXT--LINE_ARROW | 33 | 0 |
| `BOTTOM_NOTE__BOTTOM_INTERVAL_ARROW` | TEXT--LINE_ARROW | 111 | 0 |

这些数字来自未膨胀、双方独立的 300 dpi raw mask，并仅在“同一无序 pair 一次”的口径下计和；白底标签的绘制顺序未被当作“没有几何碰撞”的理由。四项逐像素 ROI 的交集与原图在 `critical_pairs/critical_015_*`、`critical_020_*`、`critical_028_*`、`critical_029_*`；每项亦有 `*_raw_8x_nn.png`、`*_overlay_8x_nn.png`、`*_overlap_8x_nn.png`。这些结果均由整页原生 300 dpi 固定网格切片取得；direct-clip 的早期 187/189 计数为 `SUPERSEDED`，不属本报告的有效结论。最小 PDF/vector bbox 净空也是 0 px；所有其余非失败对的最小正 raw 净空为 9.591 px。页面边缘最小 bbox 净空为 259.845 px，`after_edge_clip_report.csv` 中所有对象 `CLIP_PIXEL_COUNT=0`。

## 7. 数学、文字、阅读顺序、灰度与页面融合

`MATH_SEMANTICS_PASS: true`。上行从 `$j\ne i$` 出发，在 $t=3$ 首次到达 $i$；下行从 $i$ 出发，排除 $t=0$，在 $t=3$ 首次正回返。结论框 `$\mathbb E_i[\tau_i^+]<\infty$` 与相邻正文的正常返定义（`V5-C01.tex:422--428`）一致，也正确否定了用某个固定时刻首次到达概率定义正常返。

`TEXT_CONSISTENCY_PASS: true`；`READING_ORDER_PASS: true`（先比较两条时间线，再读右侧判据和题注）；`GRAYSCALE_PASS: true`（状态字母、箭头和轮廓仍可辨，重点不只靠颜色）；`PAGE_INTEGRATION_PASS: true`（图、题注和页边均完整，整页未见异常断裂）。这些通过项不能覆盖第 3--6 节硬失败。

## 8. 最终矩阵与移交

```text
RESULT: FAIL
TASK_ID: FIG-P552-01
SOURCE_FONT_PASS: false (38 failures)
PIXEL_HEIGHT_PASS: false (10 / 154 glyph failures)
SAME_CLASS_RATIO_PASS: false (34 / 154 actual raw-H_ink rows outside [0.92, 1.08])
ROLE_RATIO_PASS: false
OVERLAP_PIXEL_COUNT: 221 (4 unique failing pairs; 22 + 55 + 33 + 111)
CLIP_PIXEL_COUNT: 0
MIN_TEXT_CLEARANCE_PX: 0
VISUAL_HARMONY_PASS: false
FONT_VISUAL_HARMONY_PASS: false
MATH_SEMANTICS_PASS: true
TEXT_CONSISTENCY_PASS: true
READING_ORDER_PASS: true
GRAYSCALE_PASS: true
PAGE_INTEGRATION_PASS: true
NEXT_ROLE: SA2
```

SA2 应只修复本图：将全部普通可见角色提升到不低于 9.5 pt，并通过调整标签锚点/间距/图宽或换行消除上述四个独立 mask 碰撞；不得整体缩放以规避问题。修复后必须在新冻结候选上重新执行全量 SA1。
