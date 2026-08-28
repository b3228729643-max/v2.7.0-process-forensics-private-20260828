# FIG-P309-01 - subagent1 STRICT_R1 独立复核

RESULT: FAIL  
FIGURE_ID: FIG-P309-01  
OFFICIAL_CANDIDATE: `strict_current_r92_fullbook/main_full.pdf`  
OFFICIAL_PHYSICAL_PAGE: 334  
PRINTED_PAGE: 321  
SOURCE: `绘图源码/第03册_优化模型与序列模型/V3-C02/fig_v3_c02_margin.tex`

## BLOCKERS

1. `SOURCE_FONT_PASS=false`：`w`、`2/\lVert w\rVert`、`外圈：支持向量` 的基准有效字号均为 9.2pt<9.5pt（源 53-54、59-60、73-74 行；样式定义见 4、11 行）。
2. `PIXEL_HEIGHT_PASS=false`：`T11_HMINUS_SUBMINUS` 的 300dpi 实测墨迹高度为 3px<15px。
3. `SAME_CLASS_RATIO_PASS=false`：
   - `T03_MARGIN_SLASH` 为 33px，相对同角色基础数学运算符中位数 36px 的比例为 0.9167<0.92；
   - `T08_HPLUS_SUBPLUS` 为 19px、`T11_HMINUS_SUBMINUS` 为 3px，相对自然脚本中位数 11px 的比例为 1.7273 与 0.2727，均不在 [0.92,1.08]。
4. 因上述硬门失败，`VISUAL_HARMONY_PASS=false`。`H_-` 的细小减号在原生 1:1 ROI 中可直接复核，不能以“可读”判通过。

## MATH_SEMANTICS

PASS。

- 令 `g(x)=-0.7x_1+x_2-0.2`，三条绘制直线分别给出 `g=0,+1,-1`。
- 正类外圈点 `(1.5,2.25)`、`(3.7,3.79)` 的 `g=1`；负类外圈点 `(2.2,0.74)`、`(4.3,2.21)` 的 `g=-1`。其余正/负样本均位于正确一侧。
- 双向间隔箭头两端 `g=-0.99996,+0.99996`；绘制长度 1.6383983，与 `2/sqrt(0.7^2+1)=1.6384638` 的差为 0.0000655。
- `w` 箭头位移 `(-0.7,1)` 与三条平行线的法向量一致。详见 `math_semantics_check.csv`。

## TEXT_CONSISTENCY

PASS。图内 `H_+`、`H`、`H_-`、`w`、`2/||w||` 和“外圈：支持向量”均与 610、616 行正文及图注一致。题注仅陈述“分类超平面、两条间隔边界与几何间隔”，未夹入方法说明。

## READING_ORDER

PASS。三条平行边界为主结构；外圈指出支持向量；两支法向箭头说明 `w` 与边界距离，阅读顺序单一且无遮挡。

## SOURCE_FONT_AUDIT

FAIL。16 个 token 均已列入 `after_font_audit.csv`；7 个 token 的基准有效字号为 9.2pt。图中没有 `resizebox`、`scalebox` 或 `transform shape` 累计缩放，故 `graphics_scale=1.0000`。

## PIXEL_HEIGHT_AUDIT

FAIL。16 个 token 均由最终候选/同源独立图直接以 Poppler 300dpi 渲染并测量；只有 `T11_HMINUS_SUBMINUS` 低于自身脚本级下限（3px<15px）。其余 token 各自像素高度下限通过。

## SAME_CLASS_RATIO_AUDIT

FAIL。斜线/范数竖线组与 `H_+`/`H_-` 自然脚本组存在上述精确超限。跨面板门不适用（单面板）。

## ROLE_RATIO_AUDIT

PASS。按相同脚本类别、角色中位数相对本地 BASE 比较：可比较的轴标签、普通标注、公式基准和直线标签角色比均为 1.0000，落入适用角色带。自然脚本只在父公式基准下评估角色层级，其自身像素下限和同类比例另行执行且已失败。

## OVERLAP_PIXEL_COUNT

0。

- 8 个文字语义组 x 25 个独立图形对象共 200 条关系，逐对象交集均为 0。
- 8 个文字语义组共有 28 条 TEXT-TEXT bbox 关系，交集均为 0。
- 文字层与图形层先从 PDF 精确分离；每条线、箭头和标记另建语义掩膜，不以合并掩膜代替归因。
- 支持向量外圈包围类别标记、样本落在间隔线上、法向/间隔箭头与分类线相交均为图形之间的预期语义关系，不属于非法文字重叠。

## CLIP_PIXEL_COUNT

0。正式页边缘最小余量 657px；图裁图主动保留 12px 原生边缘余量，所有文字、箭头头部和标记完整。

## MIN_TEXT_CLEARANCE_PX

8.8489px（TEXT-GRAPHIC，`H_+`/`H_-` 与各自引线）；下限为 3px。TEXT-TEXT 最小 bbox 净空为 28px，下限为 4px。轴标签与轴箭头的净空分别为 10.6619px、11.1655px。所有最近点坐标、算法和 ROI 路径见 `after_overlap_report.csv`。

## VISUAL_HARMONY

FAIL。布局、主体权重和灰度编码本身稳定，但 9.2pt 源级字号、3px 下标减号和同类像素比例硬失败；按 §9.2.1-G 不得给出协调性通过。

## FONT_AND_DENSITY

FAIL。文字密度不高、无需整体缩图；失败源于局部字号/符号设计。允许适度调整字号，但所有有效字号和像素下限必须重新通过。

## LAYOUT

PASS。无文字/线/箭头重叠，无裁切、溢出、挤压或异常留白。最近的六组对象已逐一查看原生 1:1 ROI。

## GRAYSCALE

PASS。`H_+` 虚线、`H` 实线、`H_-` 点划线可区分；正类实心圆、负类空心三角、支持向量外圈在灰度下仍保持冗余编码。

## CAPTION

PASS。题注简洁、单结论，与图和第 616 行正文一致。

## PAGE_INTEGRATION

PASS。物理页 334 的图宽、上下留白、题注和相邻段落协调；没有孤行、遮挡或页面裁切。独立图与正式页 300dpi 模板匹配得分 0.956294，像素偏移为 `(+5,+553)`，可追溯到正式页 ROI。

## REQUIRED_FIXES

1. 将 4、11、53、59 行涉及的 9.2pt 可见文字基准提高到至少 9.5pt；不得整体缩放图来补偿。
2. 结构性重做 `H_+`/`H_-` 直标，避免仅靠 3px 高的自然下标减号传达关键边界。优先使用全高度、同角色一致的文字命名或其他不含微小脚本符号的等价标注，并保留正文中的严格方程语义。
3. 提升字号后先重测 `2/\lVert w\rVert`；若斜线/范数竖线同类比例仍超门，定向调整斜线尺寸或公式写法，确保全部 token 的像素下限和 [0.92,1.08] 比例同时通过。
4. 保留现有几何、样本、外圈、线型及当前零重叠/净空结果；没有必要移动数据或箭头。
5. 生成全新独立图与正式整书候选，再全量重做字号、像素、比例、25 对象重叠、灰度和页面集成检查。SA1 未 PASS 前不得启动 SA3。

## EVIDENCE_USED

- `after_full_page_200dpi.png`
- `after_figure_crop_300dpi.png`
- `after_standalone_300dpi.png`
- `after_grayscale_300dpi.png`
- `after_text_measurement_overlay_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `semantic_graphic_mask_map.csv` 与 `semantic_masks/`
- `roi/`（原生 1:1 raw ROI 与最近像素叠加图）
- `manual_pixel_roi_review.csv`
- `math_semantics_check.csv`
- `audit_summary.json`
- `standalone_build/v260_FIG-P309-01_standalone.log`（硬错误/未定义引用/overfull/underfull 扫描为 0）

## FINAL

RESULT: FAIL。不得启动 subagent3；转 subagent2 定向修复。

