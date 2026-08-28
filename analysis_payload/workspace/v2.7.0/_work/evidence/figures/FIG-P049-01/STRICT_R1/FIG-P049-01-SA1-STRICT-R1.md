# FIG-P049-01｜独立 SA1 严格复核（新 Goal R1）

- RESULT: **FAIL**
- ROUTE: `SA2_REQUIRED`
- OFFICIAL_SOURCE: `build/strict_current_r89_fullbook/main_full.pdf`，物理页 48、图 3.1
- SOURCE_WRITES: `NONE`

## 字号与像素

- 曲线标签、点/向量标签为 9.4pt；说明、公式与三条读图注释为 9.2pt；刻度样式定义为 8.8pt。所有实际可见的 9.2/9.4pt 项低于 `>=9.5pt`。
- 官方页原生 300 dpi 抽查中，`v_{tan}` 的脚本 `n` 为 14px，第 3 条注释公式脚本 `a/n` 为 14/13px，低于自然脚本 15px 下限。
- 当前缺少最终候选的全量逐元素 H_ink、同类/角色比、叠加图、掩膜、ROI、重叠/裁切/净空报告；任一未知按 FAIL。

## 数学语义

- 正确：`f(P)=1`，`∇f(P)=(8/15,2/3)`，梯度箭头 `G-P=(.72,.90)=1.35∇f(P)`。
- 错误：当前 `T-P=(.94,-.75)`，与梯度点积为 `1/750≠0`；`T-Tm=(1.88,-1.50)`，与梯度点积为 `1/375≠0`；直角标记两臂点积为 `9/5000≠0`。图与题注宣称精确正交，因此为硬性数学 FAIL。
- 精确修复坐标：`T=(3.3375,.33)`、`Tm=(1.4625,1.83)`。
- 第 1 条引导终点 `(2.75,1.36)` 的 `f=1.4111419753`，不在 `f=1` 等值线上；第 3 条引导终点 `(2.67,1.23)` 的 `f=1.2590444444`，不在切线或 P 点。必须重定向到真实对象。
- 三条椭圆实际对应 `f=1/4,16/25,1`，顺序本身正确；关联说明与索引须保持一致。

## 门矩阵

| 门 | 结果 |
|---|---|
| SOURCE_FONT | FAIL |
| PIXEL_HEIGHT | FAIL |
| SAME_CLASS_RATIO | UNKNOWN → FAIL |
| ROLE_RATIO | UNKNOWN → FAIL |
| OVERLAP / CLIP / CLEARANCE | UNKNOWN → FAIL |
| MATH_SEMANTICS | FAIL |
| VISUAL_HARMONY / GRAYSCALE / PAGE | 缺四视图与全量证据 → FAIL |
| REFERENCE | 图号与引用存在，但不能抵消数学失败 |

## 必须修复

SA2 应把所有可见基准文字统一提升到至少 10pt，修正 tick 定义；采用上述精确切线坐标，重定位两条错误引导线。随后从新候选生成完整五类 `after_*` 证据、原生 300 dpi ROI/掩膜与四视图，并重新走独立 SA1、隔离 SA3 和根验收。

## 证据来源

- `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex`
- `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C03.tex`
- `build/strict_current_r89_fullbook/main_full.pdf` 物理页 48，以及对应 AUX/LOG
