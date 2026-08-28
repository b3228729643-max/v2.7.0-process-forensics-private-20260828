# FIG-P033-01｜独立 SA1 严格复核（新 Goal R1）

- RESULT: **FAIL**
- ROUTE: `SA2_REQUIRED`
- OFFICIAL_SOURCE: `build/strict_current_r89_fullbook/main_full.pdf`，物理页 29
- SOURCE_WRITES: `NONE`

## 硬失败

1. 图内 `残差`、`最短距离`、勾股关系等可见文字为 9.2pt，低于一般可见文字 `>=9.5pt` 硬门。
2. 原生 300 dpi 页面中，`子空间 S` 与下侧子空间边界发生 **20 个非法重叠像素**；最小净空为 0。
3. 同类公式像素比例失败：`x` 为 21px 与 19px，比值 `1.105>1.08`；`p` 为 29px 与 26px，比值 `1.115>1.08`。
4. 数学几何不精确：当前 `OP` 未与所画子空间带严格平行，`PX` 未与该带严格垂直，方向偏差为 `1.2646°`。当前直角符号只证明 `OP ⟂ PX`，不能证明二者与所画 `S` 的关系。
5. 当前对象缺少新 Goal 指定的五类最终 `after_*` 证据；裁切像素严格值未知，不能判 0。

## 精确修复入口

保持左端不变时，应把带的右端 y 差从 1.45 改为 1.325；建议右上端改为 `(4.84,1.365)`、右下端改为 `(4.96,.885)`，使带方向与投影线严格一致。`子空间 S` 应移入带内或调整位置，不能用白底遮除边界；所有可见基准文字统一到至少 10pt 并重新测量同类比例。

修复后必须从最终候选直出未缩放 300 dpi 图，生成逐元素字号、字高、比例、重叠/裁切/净空、叠加框和四视图证据，再启动新的独立 SA1 与隔离 SA3。

## 门矩阵

| 门 | 结果 |
|---|---|
| SOURCE_FONT | FAIL |
| PIXEL_HEIGHT | FAIL（完整逐元素证据缺失） |
| SAME_CLASS_RATIO | FAIL |
| ROLE_RATIO | FAIL（完整实测证据缺失） |
| OVERLAP | FAIL，至少 20px |
| CLIP | UNKNOWN → FAIL |
| MATH_SEMANTICS | FAIL |
| VISUAL_HARMONY | FAIL |

## 证据来源

- `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex`
- `build/strict_current_r89_fullbook/main_full.pdf` 物理页 29
- 对应章节、AUX、LOG 与共享图样式（只读）
