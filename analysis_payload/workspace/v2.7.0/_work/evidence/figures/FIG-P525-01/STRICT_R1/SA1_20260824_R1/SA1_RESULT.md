# FIG-P525-01｜STRICT R1｜SA1 正式验收

RESULT: FAIL

NEXT_ROLE: SA2

## 覆盖与输入

- 冻结输入：`src/build/strict_current_r93_fullbook/main_full.pdf`，独立定位到物理 PDF 第 571 页（全书 813 页）。
- 图源：`src/绘图源码/第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_simplex.tex`。
- 相邻正文：`V4-C06.tex:382--413`。
- 已枚举 112 个可见 glyph、14 个语义文字组件、15 个线/marker/边框/填充组件；TEXT--TEXT=91 对、TEXT--GRAPHIC=196 对、TEXT--EDGE=14 对。
- 原生视图：`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。300 dpi 测量图未 resize；crop 仅裁切。

## 硬门矩阵

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | false | true | FAIL |
| SOURCE_FONT_FAILURE_COUNT | 19 glyphs / 2 components | 0 | FAIL |
| PIXEL_HEIGHT_PASS | false | true | FAIL |
| SAME_CLASS_RATIO_PASS | false | true | FAIL |
| ROLE_RATIO_PASS | false | true | FAIL |
| OVERLAP_PIXEL_COUNT | unique=387; pair-sum=387; duplicate=0 | 0 | FAIL |
| CLIP_PIXEL_COUNT | 0 | 0 | PASS |
| MIN_TEXT_CLEARANCE_PX | text/text=20.000; text/line=0.000; text/border=7.000; edge=48.000 | 4/3/5/6 | FAIL |
| FONT_VISUAL_HARMONY_PASS | false | true | FAIL |
| MATH_SEMANTICS_PASS | false | true | FAIL |
| TEXT_CONSISTENCY_PASS | false | true | FAIL |
| GRAYSCALE_PASS | true | true | PASS |
| PAGE_INTEGRATION_PASS | true | true | PASS |

## 强制 FAIL 发现与可执行 SA2 动作

1. **源级有效字号 FAIL。** 图源 L3 的 picture 字号是 9.4pt，但公共 `statlearnbook.sty:L276` 的 `every node/.append style={font=\small}` 在 11pt 文档中将普通 node 覆盖为合格的 10.0pt（冻结 PDF vector span≈9.963pt 与之相符）。仅 L14 的显式图例 `\fontsize{8.8pt}{10.4pt}` 保持 8.8pt 并失败；必须只提升该图例到至少 9.5pt，且公式合法脚本从合格 10.0pt 基准自然派生；不要整体缩放图。
2. **逐 glyph 像素高度 FAIL。** `after_pixel_measurements.csv` 对公式中的 `∶`（21px）、`=`（12px）和 `,`（11px）等独立 substring 使用各自无膨胀 raw mask，不能由父公式替代；图例/题注全角 `：` 与题注句点也分别失败。失败记录和 8x ROI 已落盘。提升有效字号后必须重新原生 300dpi 渲染及逐 glyph 复测。
3. **同类像素比例 FAIL。** `same_class_ratio_audit.csv` 的失败组为：题注 CJK/全角 0.5946--1.0270、公式自然脚本 `k` 0.9062--1.1250、图例 CJK/全角 0.5758--1.0000、主题标签 `∶` 1.0000--1.3810，均越出 [0.92,1.08]。
4. **角色层级 / 视觉协调 FAIL。** 图例 8.8/10.0=0.8800，低于图例相对 BASE 的 0.95 下限；整页和灰度审看都显示其过小，不能视为次要而豁免。
5. **真实边界/marker 交叠 FAIL。** 原生 300dpi、1:1、无膨胀分离 mask 的精确对为：`φ_{:1}` × outer-edge-3 = 88px、`φ_{:2}` × outer-edge-2 = 126px、`φ_{:3}` × outer-edge-2 = 170px、`θ_{2j}` × document-diamond = 3px；每对净空均为 0.000px、clip=0。`overlap_reconciliation.json` 逐一复计 overlap mask，四个 A-side bbox 两两不交，故 pair-sum=unique=387 且重复计数=0。
6. **数学 / 图文一致 FAIL。** `V4-C06.tex:403` 将“同一点有多解”无条件化。本图的固定主题矩阵具有 `det(Phi)=0.4288`，且 `P=(.309,.4195,.2715)^T` 的唯一系数是 `theta=(.3,.45,.25)^T`。修正文句必须区分仿射相关/重复主题、同时改变 Phi/Theta、主题置换等真正的非唯一情形；固定仿射独立 Phi 时明确系数唯一。

## SA1 结论

任一硬门 FAIL 即不得进入 SA3。本轮结果为 **FAIL**，下一角色必须是 **SA2**。SA2 仅可改指定图源及直接相邻正文；修复后须生成新的冻结候选与一套全新 300dpi raw-mask 证据，再由新的 SA1 复审。
