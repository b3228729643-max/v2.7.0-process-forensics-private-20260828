# FIG-P632-01｜ROOT CANDIDATE R3.9

RESULT: **ROOT_TECHNICAL_PASS_PENDING_NEW_SA1_AND_SA3**  
STRICT_FINAL: **NO**

## 候选身份

- 权威图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_conditional_slice.tex`，R3.9，9022 bytes。
- 图级页面 PDF：`R3/p632_root_r3p9_page.pdf`，82204 bytes；独立 PDF：`R3/p632_root_r3p9_standalone.pdf`，50341 bytes。
- 图级原生渲染：`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`，均未 resize。
- 连续版页面：`fullbook_page_680.pdf`；`fullbook_page_200dpi.png` 与 `fullbook_page_300dpi.png` 分别直接按 200/300 dpi 渲染，目标为图 33.2、印刷页 667、物理页 680。
- 连续版页后正常衔接题注、读题翻译与例题 33.1，不存在单页包装器造成的伪空白尾页。

## 严格机器门

- `after_font_audit.csv`：59/59 PASS；非天然脚本最小有效字号 9.5641 pt；同面板同角色最大字号比 1.0101、最大绝对差 0.1001 pt；跨面板最大比 1.0101；源级角色最大比 1.0378。
- `after_pixel_measurements.csv`：59/59 PASS；类中位数比例范围 0.9811--1.0294；像素角色最大比 1.0735。
- 像素高度下界：CJK 34 px、Latin/数字 25 px、x-height 18 px、基准数学 22 px、合法自然脚本 19 px，均达到严格门槛。
- `after_overlap_report.csv`：31/31 PASS；非法重叠像素总上界 0，裁切像素总上界 0；全表最小实测净空 14 px。
- 最紧项为 C23 `x_1`—联合图横轴箭头头部 14 px（门槛 3 px）；上下数字—相邻公式 15 px（跨面板门槛 8 px）；警示文字—边框 17 px（门槛 5 px）。
- 用户明确指出过的“积分号—纵轴”类型已列入 31 项检查，重叠像素为 0，净空达标。

## 根线程 1:1 视觉检查

- 已以 original/1:1 查看 `figure_crop_300dpi.png`、`grayscale_300dpi.png`、`after_text_measurement_overlay_300dpi.png`、`fullbook_page_300dpi.png` 及关键 ROI。
- 未见文字/公式与坐标轴、曲线、映射箭头、箭头头部、标记、等高线、警示框或裁切边接触。
- `x_1=a=1` 与 `(a,b)` 使用引线后不再压等高线；两条映射箭头在进入条件面板前保留净空；下方面板的 `3/5` 与警示框不接触。
- 统一 9.6 pt 图内基准配合自然分式/上下标；上下条件面板同型文字大小一致，没有为避碰而异常缩小，也没有局部大字抢占曲线视觉层级。
- 灰度视图中外层点线、中层虚线、内层实线，以及上下条件曲线的实/虚线仍可区分。

## 连续构建边界

连续版 PDF 共 813 个物理页并成功写出，但全书日志在末尾记录一个书级 `Float(s) lost`。标签比对已定位为 FIG-P756-01（图 37.8）未落版；FIG-P632-01 的标签、题注、图体与后续正文均存在且位于物理页 680。因此：

- FIG-P632 的页面集成证据可用于本图严格复核；
- 该连续版不得作为最终整书发布 PASS；
- 全书构建门继续保持 FAIL，直至 FIG-P756-01 修复并重新成功构建。

当前仅完成根线程技术候选检查。必须等待本轮全新 SA1 PASS；只有随后全新、隔离 SA3 也 PASS，根线程才可建立 `STRICT_FINAL`。

