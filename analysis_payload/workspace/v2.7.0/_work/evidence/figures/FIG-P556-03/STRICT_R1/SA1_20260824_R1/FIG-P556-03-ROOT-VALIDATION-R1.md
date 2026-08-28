# FIG-P556-03｜ROOT VALIDATION｜STRICT R1

## 冻结对象

- 官方候选：R93 `main_full.pdf`，813 页。
- 独立定位：物理第 `602` 页，印刷页码 `589`，图号 `30.6`。
- 图源：`fig_v5_c01_detailed_balance_counterexample.tex`。
- 取证几何：先渲染整张物理页为 native 300 dpi `2481 × 3508 px`，再按像素坐标切片；另有 200 dpi 整页、standalone、灰度和对象覆盖图。

## Root 独立复核

Root 重新读取 CSV、图源与相邻正文，并在 1:1 查看 300 dpi 图面、对象覆盖图、灰度图、200 dpi 整页以及失败 glyph 的 8× nearest-neighbor ROI。复算结果：

- 可见 glyph `114`，语义文字组件 `16`，前景图形组件 `19`，背景填充组件 `6`。
- 源级字号失败 `84 glyph / 14 components`：普通文本明确使用 `9.4pt`、`9.2pt`、`8.8pt`；自然脚本 `6.16pt` 来自不合法的 `8.8pt` 基准公式，不能获得脚本例外。
- raw `H_ink` 失败 `13 glyph / 6 components`；提交证据对运算符、全角标点、短笔画字符和题注分隔点逐字给出原始无膨胀 mask 与阈值。
- D 同类比例：`10/20` 组失败；E 角色比例：`3/20` 组失败，具体为 `0.8750`、`0.8333`、`0.9412`。
- 必查文字关系 `440` 条：TEXT--TEXT `120`、TEXT--CURVE `64`、TEXT--ARROW `64`、TEXT--NODE_BORDER `176`、TEXT--EDGE `16`。非法 overlap 总计 `0px`，clip `0px`；各类最小净空依次为 `35.125/7/34.228/11/19px`，均达到相应门槛。
- 数学与概率语义通过：详细平衡推出平稳性；`A=I_2` 的断开反例说明详细平衡不推出连通或平稳分布唯一。图、题注与相邻正文一致。
- 整页中普通标签和反例说明相对标题、正文视觉偏小；源字号、像素与 D/E 已有硬失败，因此 `FONT_VISUAL_HARMONY_PASS=false` 的结论成立。

## Root 裁决

`FAIL → SA2`。本图不得进入 SA3，也不得计入 99 图最终严格通过数。即使 overlap/clip 为零，源字号、实际像素、同类比例、角色层级与整体和谐任一失败都足以否决。

