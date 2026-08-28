# FIG-P324-01 独立 SA1 严格复核（STRICT_R1）

## 1. 结论

**RESULT: FAIL**

FIG-P324-01 不满足 Goal §9.2.1。它在 AdaBoost 语义、图文一致、灰度可辨和整页放置方面没有发现错误，但源级字号、运算符像素高度、同类/跨通道比例、角色比例以及一组文字—文字 bbox 净空均有硬失败。**不得启动 SA3。**

本轮为全新盲审：只读取冻结候选、目标图源、相邻正文、公共字体级联和 Goal §9.2.1；未读取任何既有 R1/SA2/SA3/ROOT 报告或中央库存结论。

## 2. 冻结对象与定位

- 候选 PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r92_fullbook\main_full.pdf`
- 图源：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第03册_优化模型与序列模型\V3-C03\fig_v3_c03_adaboost_loop.tex`
- 相邻正文：`讲义源码/第03册_优化模型与序列模型/chapters/V3-C03.tex:125,128,130-132`
- 正式物理页：349；印刷页：336；正式图号：图 19.1
- PDF 页面：A4，595.276 x 841.89 pt；Poppler 300 dpi 原图：2481 x 3508 px
- 图区域：PDF `(110,278)--(470,448)pt`，300 dpi `(458,1158)--(1959,1867)px`

## 3. 方法与证据完整性

1. 由冻结整书 PDF 直接使用 Poppler 渲染 300 dpi 原图；200 dpi 仅作整页总览，所有数值均来自未 resize 的 300 dpi 原图。
2. 将 43 个可见文字 token 建立唯一 ELEMENT_ID；数学母符号、自然上下标和运算符分别测量。逐项记录源码行、字号级联、300 dpi bbox、实际墨迹高度、同类中位数、同类比例和角色比例。
3. 文字按 PDF 指定色与局部背景沿抗锯齿混合方向分离，阈值要求相对背景至少 20/255；这使金色 O10 与灰色 O11 成为真正独立的语义掩膜，而非宽泛合并掩膜。
4. 逐条重建 15 个 PDF 向量语义对象：7 个节点边框（含双边框擦除层）及 8 组线/箭头/返回线。每个对象均有独立 mask。
5. 对 12 个独立文本对象作全部 text-text 组合；对每个文本对象与每个图形对象作全部 text-graphic 组合。前景距离采用欧氏最近像素；text-text 另以 PDF/vector bbox 检查 4px 硬门。
6. 人工以原生 1:1 查看：O10/O11 临界区、O12 小号图例区、O09/双边框最小图形净空区；并查看四种规定视图。

核心文件：

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_visual_acceptance.md`
- `measurement_bbox_overlay_300dpi.png`
- `measurement_summary.json`
- `masks/elements/`、`masks/text_objects/`、`masks/graphics/`
- `roi_O10_edge_formula_vs_O11_return_annotation_raw_1to1_300dpi.png`
- `roi_O10_edge_formula_vs_O11_return_annotation_overlay_1to1_300dpi.png`
- `roi_O10_edge_formula_vs_O11_return_annotation_semantic_masks_1to1_300dpi.png`

## 4. 源级字号审计：FAIL

字号级联经过公共样式复核：`statlearnbook.sty` 的 `every node/.append style={font=\small}` 在 11pt 文档中给普通节点 10.0pt；节点内 `slfig node` 也明确使用 `\small`。因此图源第 3 行的 picture 级 9.2pt 不直接决定普通节点文字，普通节点按 10.0pt 通过。显式 node-local `\fontsize` 则覆盖该级联。

精确失败共 13 个 ELEMENT_ID：

| ELEMENT_ID | 源码行 | 内容 | 母字号 | 失败原因 |
|---|---:|---|---:|---|
| E31/E33/E34 | 32-33 | `e`、`mapsto`、`alpha` | 8.8pt | 基准公式 <9.5pt |
| E32/E35 | 32-33 | 两个自然下标 `m` | 母式 8.8pt | 下标母式不合法，不能享受自然 script 例外 |
| E36 | 36-37 | 仅权重更新返回训练 | 8.5pt | 普通注释 <9.5pt |
| E37--E43 | 38-39 | 形状编码与三个 `/` | 8.5pt | 图例/说明 <9.5pt |

标题 E01/E14 为 9.7pt；普通节点母字号为 10.0pt，源级下限通过。

## 5. 300 dpi 实际像素高度：FAIL

43 个 token 中有两个像素下限失败：

| ELEMENT_ID | 内容 | 类别 | H_ink_px | 下限 |
|---|---|---|---:|---:|
| E23 | `=`（集成模型公式） | BASE_OPERATOR | 12 | 22 |
| E33 | `mapsto`（误差到分类器权重） | BASE_OPERATOR | 15 | 22 |

其余 CJK、大写/数字、小写/希腊和自然脚本 token 均达到各自绝对像素下限；这不抵消源级字号及比例失败。

## 6. 同类比例、跨通道一致与角色层级：FAIL

### 6.1 同面板同类

12 个 ELEMENT_ID 的 `H_ink_px / class_median` 超出 `[0.92,1.08]`：

`E04, E06, E07, E10, E13, E16, E21, E23, E24, E25, E26, E29`。

代表值：E06 `G` 为 `29/37=0.7838`；E23 `=` 为 `12/19=0.6316`；E26 `+` 为 `26/19=1.3684`。

### 6.2 跨通道

- 普通节点 CAPS/DIGITS：上通道中位数 37px，下通道 33px，最大/最小 `1.1212 >1.10`。
- 普通节点 NATURAL_SCRIPT：上通道 24.5px，下通道 21px，最大/最小 `1.1667 >1.10`。
- 标题 CJK、节点 CJK、节点 LOWER/GREEK 跨通道分别为 1.0，单独通过。

### 6.3 角色比例

19 个 token 超出角色带：

`E04, E06, E13, E16, E23, E25, E26, E29, E32, E33, E35, E36, E37, E38, E39, E40, E41, E42, E43`。

其中视觉上最稳定、无需依赖不同字形解释的失败是：E36 以及 E37/E39/E41/E43 的 CJK 高度均为 31px，普通节点 CJK BASE 中位数为 36.5px，比值 `0.8493 <0.95`。因此灰色说明和形状编码在整页/整图中明显偏小，和用户要求的字体协调门直接冲突。

## 7. 重叠、裁切与净空：前景零交叠，但 bbox 净空 FAIL

### 7.1 非法前景交叠与裁切

- `OVERLAP_PIXEL_COUNT = 0`
- `CLIP_PIXEL_COUNT = 0`

按独立语义掩膜，没有任意 text-text、text-line/arrow 或 text-node-border 的有效前景像素交集。本图不能被描述为“有 1 个以上非法前景重叠像素”。

### 7.2 O10/O11 精确区分

临界对象：

- O10：源码 32-33 行金色 `e_m mapsto alpha_m`
- O11：源码 36-37 行灰色“仅权重更新返回训练”

分色语义掩膜的最近有效前景坐标为：

- O10 `(1514,1583)`
- O11 `(1514,1589)`

欧氏前景距离为 6.0px，且交集为 0。**但是**两对象的 PDF/vector bbox 在 y 方向相交，计算的 bbox 净空为 `0.0px <4px`。Goal F 明确要求文字—文字 bbox 至少 4px，因此 `TT-O10-O11` 仍为 FAIL。这里的 `MIN_TEXT_CLEARANCE_PX=0` 专指 bbox 净空，不是把 6px 前景距离误报成 0。

原生 1:1 ROI 可见金色下标 `m` 与灰色首行顶端形成明显拥挤；即使前景没有共享像素，也不满足严格净空及视觉协调门。

### 7.3 text-graphic

所有 text-line/arrow/node-border 组合通过。最小值为 O09 集成模型文字到自身 G10 双边框 11.0px，高于节点内 5px 下限；ROI 显示公式和双边框没有相碰。

## 8. 四视图人工复核

- `full_page_200dpi.png`：图在页面中的尺寸、图注换行和上下正文留白正常；但 8.5/8.8pt 的中部说明及底部形状编码明显弱于节点文字。
- `figure_crop_300dpi.png`：主流程顺序清楚；O10/O11 视觉拥挤，底部说明偏小。
- `standalone_300dpi.png`：使用冻结正式页向量区域的原生 300dpi 隔离视图，不做 resize；上述问题仍存在。
- `grayscale_300dpi.png`：节点形状、实/虚线和箭头方向仍可辨，未发现依赖颜色后完全丢失的语义；灰度门单独通过。

## 9. 数学、图文与阅读路径

- `MATH_SEMANTICS_PASS = true`：图中顺序为 `D_m -> G_m -> e_m -> D_{m+1}`；误差通向 `alpha_m`；弱分类器及其系数进入 `F_m=F_{m-1}+alpha_m G_m`；返回线只表达权重更新进入下一轮训练。
- `TEXT_CONSISTENCY_PASS = true`：正文第 125、128、132 行与图注均区分样本权重 `D_m` 和分类器权重 `alpha_m`，图内变量与箭头对应。
- 阅读路径从上通道向右，再由误差下行至加法模型，单向且可解释。
- `PAGE_INTEGRATION_PASS = true`：图、图注、正文、页眉页脚和页边界没有碰撞或裁切；内部硬失败由单独门记录。

## 10. 最小修复方向（交给 subagent2）

1. 将源码 32-33 行边标签母字号提高到至少 9.5pt，并重新放置到金色箭头的安全侧，使其与 O11 的 PDF/vector bbox 至少相隔 4px；建议目标留白大于硬下限，避免增字号后再次拥挤。
2. 将源码 36-37 行说明提高到至少 9.5pt；增字号时同步上移/右移，兼顾 O10、返回虚线和集成模型上边框的 3px/4px 净空。
3. 将源码 38-39 行形状编码提高到至少 9.5pt，并保持与下方图注及上方流程至少相应硬净空。
4. 对 E23 `=` 与 E33 `mapsto` 重新排版，使实际运算符墨迹高度达到 22px，同时不得破坏公式角色带、节点尺寸、同类比例或全图协调性；不能只改源声明而不重测 300 dpi 墨迹。
5. 修复后必须从正式整书新候选重新渲染 300 dpi，逐 token 重做像素/同类/角色/跨通道和全部语义对象净空；不可复用本轮数值。

## 11. 最终矩阵

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.0  # bbox；O10/O11 前景为 6.0px
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
```

**RESULT: FAIL — 禁止进入 SA3。**
