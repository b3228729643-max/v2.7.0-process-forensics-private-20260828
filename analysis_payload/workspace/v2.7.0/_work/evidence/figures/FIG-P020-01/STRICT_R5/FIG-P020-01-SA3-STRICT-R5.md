RESULT: PASS
仅 SA3 候选，等待根签发。

# FIG-P020-01｜SA3 隔离严格复核 R5

## 独立审查范围与方法

- 只读官方候选：`v2.7.0/_work/source/v2.7.0/src/build/strict_current_r90_fullbook/main_full.pdf`，物理第 17 页；PDF 为 813 页、A4 `595.276 × 841.890 pt`。
- 只读当前权威图源：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`（2026-08-23 19:32:52）；官方 PDF 更新于 19:51:48。
- 本审查未读取 FIG-P020-01 的既有 SA1、SA2 或 ROOT 报告、结论或掩膜。
- 物理第 17 页由官方 PDF 直接以 `pdftoppm -r 300` 渲染为原生 `2481 × 3508 px` PNG，未 resize；所有数值检查都在该 1:1 原图及其 PDF 坐标映射上完成。文字前景采用局部背景 RGB 最大通道差 `>=20/255`，符合 Goal §9.2.1-C。
- 四视图均已实际检查：整页 200 dpi、局部原生 300 dpi、由当前图源独立构建的 300 dpi 视图、局部 300 dpi 灰度图。见本目录内 `SA3_FIG-P020-01_page17_200dpi.png`、`SA3_FIG-P020-01_figure_roi_300dpi.png`、`SA3_FIG-P020-01_standalone_page_300dpi.png` / `SA3_FIG-P020-01_standalone_source_rebuild.pdf`、`SA3_FIG-P020-01_figure_roi_grayscale_300dpi.png`。

## 源级有效字号与 300 dpi 字高

图源没有 `\resizebox`、`\scalebox`、`scale=` 或 `transform shape`；graphics scale 为 `1.0`。`\fontsize{10.5pt}{12.6pt}` 的四个节点标题来自图源第 11 行；五个节点正文、回查注释均是 `10.0 pt`；题注由 11 pt 文档类下的 `\small` 产生，为 `10.0 pt`。同一语义角色的源级最大/最小比均为 `1.0000`、差为 `0.00 pt`，满足 `<=1.03` 且 `<=0.25 pt`。

PDF 字体字段中的 `9.9626 pt` / `10.4608 pt` 是 TeX `72.27 pt/in` 映射到 PDF `72 pt/in` 的坐标值，分别可逆换算为源级 `10.00 pt` / `10.50 pt`，不是任何 graphics 缩放。

| 角色（同脚本类） | 数量 | 有效字号 | H_ink（原生 300 dpi） | 相对 CJK 正文基准 36 px | 结论 |
|---|---:|---:|---:|---:|---|
| 节点标题（CJK） | 4 | 10.50 pt | 41–42 px | 1.139–1.167 | PASS |
| 节点正文（CJK） | 5 | 10.00 pt | 36–37 px | 1.000–1.028 | PASS |
| 回查注释（CJK） | 1 | 10.00 pt | 37 px | 1.028 | PASS |
| 题注标签“图”（CJK） | 1 | 10.00 pt | 38 px | 1.056 | PASS |
| 题注正文（CJK） | 1 | 10.00 pt | 37 px | 1.028 | PASS |
| 题注编号“1.1”（数字） | 1 | 10.00 pt | 28 px | 不与 CJK 全字面高度混比 | PASS |

- 所有 CJK 均 `>=30 px`；数字 `1.1` 为 `28 px >=24 px`。本图没有承载语义的拉丁小写、希腊小写、基准数学符号或自然上下标，故这些类别为不适用而非缺测。
- 同角色、同脚本类像素高度比均在 `[0.92, 1.08]`：节点标题最大/最小 `1.0244`，节点正文 `1.0278`；其余同类各只有一个元素。四个节点标题是经源级 `10.5/10.0=1.05` 预设的节点层级强调，最大实际 CJK 比 `1.1667 <=1.25`，未抢占流程主线。
- 本图是单面板，跨面板字号与像素比要求不适用；不存在被跳过的第二面板。
- 可缩小字体的条件未触发：虽所有硬下限通过，但四视图中正文、标题和题注已形成稳定层级且未拥挤，不建议为压缩版面降低任何字号。

逐元素源级和像素证据见 `SA3_FIG-P020-01_source_font_audit.csv`、`SA3_FIG-P020-01_pixel_measurements.csv`、`SA3_FIG-P020-01_role_ratio.csv` 与 300 dpi 标注叠图 `SA3_FIG-P020-01_text_measurement_overlay_300dpi.png`。

## 中间“定义域 → 值域”箭头：矢量身份与净空

PASS。图源第 16–20 行为内嵌 TikZ：`\draw[-{Stealth[...]}] (1.05mm,0)--(5.95mm,0);`，不是 `\to` 或其他放大文字。官方 PDF 的原生矢量清单又独立定位到：

- `D011`：描边直线；
- `D012`：填充的 Stealth 箭头头；
- 原生 300 dpi 墨迹 bbox：`[1055, 1377, 1114, 1388]`，即 59 × 11 px 的图形路径而非字体字形。

逐像素净空（文字墨迹到箭头墨迹，未缩放）：

| 对象对 | 非法重叠像素 | 净空 | 阈值 | 结论 |
|---|---:|---:|---:|---|
| “定义域” ↔ 中间矢量箭头 | 0 | 13.79 px | >=3 px | PASS |
| 中间矢量箭头 ↔ “值域” | 0 | 15.79 px | >=3 px | PASS |

这两个测量在 `SA3_FIG-P020-01_overlap_clearance.csv` 中有专门的 `ARROW_CLEARANCE_*` 行；矢量路径与文字框同时标在测量叠图中。

## 重叠、裁切与净空

- 审计了 13 个读者可见文字 ELEMENT_ID、78 个 TEXT–TEXT 组合、117 个 TEXT–LINE_ARROW/NODE_BORDER 组合、13 个图像边缘组合，以及两项中间箭头专检。
- `OVERLAP_PIXEL_COUNT = 0`；`CLIP_PIXEL_COUNT = 0`。节点填充/注释底色只按背景处理，节点边框、所有实线/虚线箭头及箭头头均作为独立前景对象检查。
- 最小 TEXT–TEXT PDF bbox 净空为 `8.00 px >=4 px`（题注“图”与“1.1”，以及回查注释与题注标签均为 8 px）。
- 最小 TEXT–GRAPHIC 墨迹净空为 `13.79 px >=3 px`（“定义域”到中间矢量箭头）；最小节点文字到自身边框净空为 `14.00 px >=5 px`；最小文字到原生 A4 图像边缘为 `265 px >=6 px`。
- 无相邻面板，故跨面板 `>=8 px` 没有适用对象；这不是未知值。

完整对照行、阈值、重叠数和结论见 `SA3_FIG-P020-01_overlap_clearance.csv`；官方 PDF 的文字/矢量原始清单见 `SA3_FIG-P020-01_native_pdf_inventory.json`。

## 四视图、数学语义、图文与页面融合

- 局部 300 dpi：四个节点从左到右依次为“对象声明 → 关系与映射 → 运算与逻辑 → 可核验任务”；三条主箭头只沿正向连接相邻节点，回查线独立为下方虚线回路，端点停在边界，阅读路径唯一。
- 独立 300 dpi：由当前图源重新构建的单图与官方页的节点/箭头结构一致，无文字、边框或箭头突兀放大；中间箭头具有恰当的内嵌关系标记视觉权重，不压过正文或流程主线。
- 灰度 300 dpi：主流程实线箭头、回查虚线箭头、节点边框和方向箭头头仍可区分；颜色不是唯一编码，层级未崩塌。
- 整页 200 dpi：图置于“优化解释”之后，题注和紧随的读图提示完整，随后例题开始；图宽、上下留白、题注和正文衔接稳定，无孤行、异常留白、溢出或分页冲突。
- 数学/文字/题注：映射 `定义域 → 值域`、从对象定义到任务陈述的正向依赖、以及“从任务端逆向核对”的虚线回路与题注和相邻正文一致；没有公式、变量、方向或题注语义冲突。

## §9.2.1 判定矩阵

```text
SOURCE_FONT_PASS             = true
PIXEL_HEIGHT_PASS            = true
SAME_CLASS_RATIO_PASS        = true
ROLE_RATIO_PASS              = true
OVERLAP_PIXEL_COUNT          = 0
CLIP_PIXEL_COUNT             = 0
MIN_TEXT_TEXT_CLEARANCE_PX   = 8.00
MIN_TEXT_GRAPHIC_CLEARANCE_PX= 13.79
MIN_NODE_TEXT_BORDER_PX      = 14.00
VISUAL_HARMONY_PASS          = true
MATH_SEMANTICS_PASS          = true
TEXT_CONSISTENCY_PASS        = true
GRAYSCALE_PASS               = true
PAGE_INTEGRATION_PASS        = true
```

所有适用硬门均有本 SA3 生成的原始证据且通过。因此本隔离 SA3 结论为 PASS；该结论不构成最终发布签发，仍须根线程按流程签发。
