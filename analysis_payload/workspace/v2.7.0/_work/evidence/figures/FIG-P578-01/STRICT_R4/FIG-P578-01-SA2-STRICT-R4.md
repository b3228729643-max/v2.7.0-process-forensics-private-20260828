RESULT: FIXED

# FIG-P578-01｜专属 SA2 定点返修（STRICT_R4）

## 白名单与唯一源码改动

- 唯一修改图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`。
- 新增局部宏 `\slfigRejLift`（源码第 9 行），以 `\phantom + \llap + \smash + \raisebox{2.2pt}` 在原布局盒内只上移可见内容；不扩大或移动节点外廓。
- `init`（第 44--45 行）与 `evaluate`（第 61--62 行）显式保持原两行断行，并只对第二行应用该宏。
- 未改任何 wrapper、章节、公共宏、中央 CSV/JSON、inventory、state、旧 `STRICT_R3` 证据或其他图源；本轮新增证据全部位于本 `STRICT_R4` 目录。
- 字号声明保持 `9.6pt/11.6pt` 与局部数学 `10.7pt/12.4pt`；未使用 `\resizebox`、`\scalebox` 或整体缩放。

## 局部构建与原生渲染

| 工件 | 构建结果 | PDF | 原生 300 dpi PNG |
|---|---|---:|---:|
| page | LuaLaTeX 成功，1 页 A4，`595.276 × 841.89 pt` | `candidate_page.pdf`，74,713 bytes | `candidate_page_300dpi.png`，`2481 × 3508`，299.9994 dpi |
| standalone | LuaLaTeX 成功，1 页 A4，`595.276 × 841.89 pt` | `candidate_standalone.pdf`，60,651 bytes | `candidate_standalone_300dpi.png`，`2481 × 3508`，299.9994 dpi |

- 两份 `.fls` 分别命中只读 page/standalone wrapper，并共同命中当前唯一图源。
- 两份日志均以 `Output written on ... (1 page, ...)` 结束。
- 对 page 与 standalone 日志逐项扫描：`^!`、`Fatal error`、`Emergency stop`、`LaTeX Error`、`Package .* Error`、`Undefined control sequence`、`Overfull [hv]box`、`Underfull [hv]box`、`Missing character` 均为 `0`；每份日志硬模式合计 `0`。
- 另生成 page 灰度原生视图 `candidate_page_gray_300dpi.png`；三张最终视图均由 Poppler 直接以 300 dpi 渲染，未 resize、未重采样。

## 1:1 逐像素修复结果

坐标均为 `2481 × 3508` page PNG 左上角原点、闭区间实墨包围盒；净空采用与 `STRICT_R3` 正式报告一致的颜色掩膜与最近像素距离口径。目标下边净空为 `>= 8 px`。

| 检查 | 修改前文字 bbox | 修改前下边框 bbox | 前 | 修改后文字 bbox | 修改后下边框 bbox | 后 | 结果 |
|---|---|---|---:|---|---|---:|---|
| `N_INIT_TEXT_BORDER_BOTTOM` | `(844,713)-(1278,819)` | `(777,819)-(1344,829)` | 0 px | `(844,713)-(1278,809)` | `(777,819)-(1344,829)` | **18 px** | PASS |
| `N_EVALUATE_TEXT_BORDER_BOTTOM` | `(886,1877)-(1235,1982)` | `(777,1983)-(1344,1992)` | 2 px | `(900,1877)-(1221,1972)` | `(777,1983)-(1344,1992)` | **18 px** | PASS |

standalone 独立复测同样通过：`init` 文字 `(838,713)-(1272,809)`、下边框 `(772,819)-(1338,830)`、净空 18 px；`evaluate` 文字 `(894,1877)-(1215,1972)`、下边框 `(772,1983)-(1338,1992)`、净空 18 px。两项 overlap pixel 均为 0。

## 行间、脚本、箭头与四边回归

| 节点 | 上/下/左/右文字—边框净空 | 第一—第二行 | 入箭头 | 出箭头 | overlap |
|---|---|---:|---:|---:|---:|
| `init` | `8 / 18 / 60 / 57 px` | 20 px | 29 px | 14 px | 0 |
| `evaluate` | `9 / 18 / 114 / 117 px` | 14 px | 24 px | 9 px | 0 |

- `init` 自然下标脚本到第一行净空 45 px、到下边框 18 px，均无接触；第二行上移后仍远高于文字—文字 4 px 门。
- 两节点文字到入/出箭头均高于 3 px 门；没有制造文字—箭头接触。
- 两节点全部定向关系在 page 与 standalone 中均 `PASS`，`AFTER` 失败列表为空。

## 字号/像素门保持

- 图源字号声明计数仍为 `9.6pt × 3`、`10.7pt × 1`；页面提取的目标节点可见字号仍为 `9.5641pt`、`10.6600pt`，自然脚本仍为 `7.4620pt`，未发生字号变更。
- R4 目标角色逐字实墨中位数：`INIT-CJK=35.0 px >=30`、`INIT-MATH=28.0 px >=22`、`INIT-SCRIPT=18.0 px >=15`、`EVALUATE-CJK=35.5 px >=30`、`EVALUATE-MATH=29.5 px >=22`，全部 PASS。
- 其余文字栅格完全未变，因此沿用官方 R3 已通过的其余字号/像素关系不会因本次局部定位而失效。

## 拓扑、数量与全页回归

- 静态计数：21 个状态节点、16 个分支标签；算法状态、文字、分支方向、回路、caption、label、alt 与拓扑均未改。
- R3 candidate 与 R4 page 的 89 个 PDF vector drawing 在数量、路径几何和样式上逐项完全一致；节点外廓、箭头、标签白底、边框与页面位置未移动。
- 原生整页栅格差分为 12,197 个像素，全部落在两个第二行文字目标盒：`INIT [844,754,1276,831]`、`EVALUATE [874,1919,1246,1994]`；目标盒外变化像素严格为 `0`。
- 因而所有非目标节点、16 个分支标签、跨节点边界、题注、后文与页面边缘保持逐像素不变。全页前景到最近页面边缘仍为 171 px（R3/R4 相同），无裁切、页面溢出或新跨节点重叠。
- 已人工打开并检查 page、standalone、灰度、两个 1:1 节点 ROI 和 before/after ROI：无文字—文字、文字—箭头、文字—边框、跨节点重叠，无裁切、断字或页面溢出。

## 证据索引

- 构建：`candidate_page.{pdf,log,fls}`、`candidate_standalone.{pdf,log,fls}`。
- 原生视图：`candidate_page_300dpi.png`、`candidate_standalone_300dpi.png`、`candidate_page_gray_300dpi.png`。
- 逐像素：`strict_r4_measurements.csv`、`strict_r4_target_pixel_heights.csv`、`strict_r4_summary.json`、`strict_r4_measurement_overlay_300dpi.png`、`strict_r4_raster_diff_overlay_300dpi.png` 与 `roi/` 下 1:1 ROI。
- 可复测脚本：`measure_strict_r4.py`。

本报告仅声明 SA2 局部候选已修复；官方全书构建、独立 SA1/SA3 与根签发由根线程继续完成。
