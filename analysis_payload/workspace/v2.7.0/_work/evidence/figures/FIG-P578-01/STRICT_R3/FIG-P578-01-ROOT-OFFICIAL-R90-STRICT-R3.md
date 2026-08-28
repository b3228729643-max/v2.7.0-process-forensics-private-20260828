# FIG-P578-01 根线程官方 R90 严格验收

RESULT: FAIL

## 审查对象

- 官方连续全书：`src/build/strict_current_r90_fullbook/main_full.pdf`
- 物理页：626
- 原生渲染：300 dpi，2481 × 3508，未缩放、未重采样
- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`

## 硬门结果

| 项目 | 结果 | 证据 |
|---|---:|---|
| 源级字号 | 91/91 PASS | `after_font_audit.csv` |
| 原生像素字高/比例 | 91/91 PASS | `after_pixel_measurements.csv` |
| 正式关系检查 | 176 PASS / 2 FAIL，共 178 项 | `after_overlap_report.csv` |
| 非法重叠像素 | 0 | 正式掩膜汇总 |
| 裁切像素 | 0 | 正式掩膜汇总 |
| 最小净空 | 0 px，FAIL | `N_INIT_TEXT_BORDER_BOTTOM` |

## 两项阻断

1. `N_INIT_TEXT_BORDER_BOTTOM`：初始化节点第二行文字实墨包围盒为 `(844,713)-(1278,819)`，节点下边框实墨为 `(777,819)-(1344,829)`；净空 `0 px < 5 px`。文字与边框接触，证据为 `roi/N_INIT_TEXT_BORDER_BOTTOM_PAGE_300DPI_1to1.png`。
2. `N_EVALUATE_TEXT_BORDER_BOTTOM`：求值节点第二行公式实墨为 `(886,1877)-(1235,1982)`，节点下边框实墨为 `(777,1983)-(1344,1992)`；净空 `2 px < 5 px`。证据为 `roi/N_EVALUATE_TEXT_BORDER_BOTTOM_PAGE_300DPI_1to1.png`。

根线程已以原始 1:1 ROI 逐像素回看，两处均是真实的文字—节点边框硬间距失败，不是掩膜误报。全图缩略视图看似整齐不能覆盖局部硬门失败。

## 结论与下一角色

FIG-P578-01 不通过，不得进入 SA3，不得写入 `STRICT_FINAL`。下一角色为唯一 SA2 源码写者，只允许定点增加初始化节点与求值节点的下侧安全空间；目标净空至少 8 px，并保持 21 个节点、16 个分支标签、算法语义、拓扑和其他已经通过的关系不变。修复后必须从新的官方构建重新生成 300 dpi 五类证据并重新走独立 SA1、隔离 SA3、根签发。

