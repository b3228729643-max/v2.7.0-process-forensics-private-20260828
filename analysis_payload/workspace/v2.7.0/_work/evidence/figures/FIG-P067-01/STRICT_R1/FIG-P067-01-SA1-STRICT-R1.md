# FIG-P067-01｜独立 SA1 严格复核（新 Goal R1）

- RESULT: **FAIL**
- ROUTE: `SA2_REQUIRED`
- OFFICIAL_SOURCE: `build/strict_current_r89_fullbook/main_full.pdf`，物理页 68、印刷页 55、图 4.1
- SOURCE_WRITES: `NONE`

## 字号硬失败

- 上面板刻度 8.8pt；下面板刻度 8.6pt。
- `p_i` 质量标签与两条注释 9.2pt。
- 两面板轴标题 9.4pt。
- 题注约 9.963pt 单独达标，但不能抵消全部图内基准文字低于 9.5pt。

## 原生 300 dpi 像素与重叠

官方 PDF 物理页 68 直接渲染为 `2481×3508px @ 300dpi`，未 resize。多数可隔离数字/CJK/脚本达到类别像素下限，但碰撞元素无法获得独立 H_ink，且没有完整逐元素表，因此像素门仍 FAIL。

已确认两类非法重叠：

1. 下面板 y 刻度 `0.30` 与 `0.35` 的文本 bbox 交叠；保守重建核心前景交集至少 11px。
2. 下面板注释“同一 `t_i`：跳高=`p_i`”与 `t=4` 竖向虚线导线相交；核心前景交集 11px。

故 `OVERLAP_PIXEL_COUNT >= 22`、`MIN_TEXT_CLEARANCE_PX=0`。页面内未见明显裁切，但没有独立对象掩膜证明 `CLIP_PIXEL_COUNT=0`，严格值为 unknown，按 FAIL。

## 数学与引用

数学语义通过：PMF `(0.15,0.30,0.35,0.20)` 和为 1；CDF 台阶 `0→.15→.45→.80→1`，跳高与 PMF 一致；开闭点正确表达右连续。正文引用、图号和题注一致。

## 门矩阵

| 门 | 结果 |
|---|---|
| SOURCE_FONT | FAIL |
| PIXEL_HEIGHT | FAIL（碰撞污染且全量表缺失） |
| SAME_CLASS_RATIO | UNKNOWN → FAIL |
| ROLE_RATIO | UNKNOWN → FAIL |
| OVERLAP | FAIL，保守下界 22px |
| CLIP | UNKNOWN → FAIL |
| MATH_SEMANTICS | PASS |
| TEXT_CONSISTENCY | PASS |
| VISUAL_HARMONY / GRAYSCALE / PAGE | FAIL |

## 必须修复

SA2 应把全部图内非脚本基准文字提高到至少 9.8pt；删除/替换过密的 `.30/.35` 刻度之一或增大面板高度，使文字间净空至少 4px；移动下面板注释，确保与 t=4 导线至少 3px 净空。修复后从最终 PDF 直出 300 dpi 全量测量、对象掩膜和四视图，再重新走独立 SA1 与隔离 SA3。

## 证据来源

- `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`
- `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C04.tex`
- `build/strict_current_r89_fullbook/main_full.pdf/.fls/.aux/.log`
