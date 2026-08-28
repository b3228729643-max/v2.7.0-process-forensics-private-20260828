RESULT: PASS

FIGURE_ID: FIG-P020-01

VERDICT_SCOPE: SA1 候选通过，等待 SA3/根签发；本报告不登记最终通过。

INDEPENDENCE: 本轮只从当前 R90 官方整书、当前图源、公共题注样式和相邻正文独立重测。未读取或采信 R4/R5 既有报告、旧 PASS、CURRENT_STATUS 或 inventory 结论。

## H. 硬门判定矩阵

- SOURCE_FONT_PASS = true
- PIXEL_HEIGHT_PASS = true
- SAME_CLASS_RATIO_PASS = true
- ROLE_RATIO_PASS = true
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 8.000（跨读者区域；同面板 TEXT-TEXT 最小 9.000）
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

全部布尔项为 true；273 组正式逐对检查无失败项；所有非法对的交集像素最大值和总值均为 0。

## 官方输入、渲染与坐标

- 官方输入：`build/strict_current_r90_fullbook/main_full.pdf`，813 页，A4；目标为 1-based 物理页 17。
- 页提取：`pypdf.PdfWriter.add_page(reader.pages[16])`，输出 `SA1_official_page17.pdf`。
- 200 dpi：`pdftoppm -f 17 -l 17 -singlefile -r 200 -png`，得到 1654 x 2339。
- 300 dpi：`pdftoppm -f 17 -l 17 -singlefile -r 300 -png`，得到 2481 x 3508。
- 300 dpi 原图之后只执行 `Image.crop` 或 RGB 到灰度转换；没有 resize、重采样、截图或二次栅格化。
- 含题注图裁剪：`(236,1205,2197,1684)`，1961 x 479；图形本体 1:1 裁剪：`(236,1205,2197,1615)`，1961 x 410。
- 全部 ROI 坐标、尺寸和命令见 `SA1_render_record.md`。

## 完整 ELEMENT_ID 清单

读者文字/数字共 13 个：

- `T_OBJ_TITLE`、`T_OBJ_BODY`
- `T_REL_TITLE`、`T_REL_DOMAIN`、`T_REL_RANGE`
- `T_LOGIC_TITLE`、`T_LOGIC_BODY`
- `T_TASK_TITLE`、`T_TASK_BODY`
- `T_AUDIT`
- `T_CAP_LABEL`、`T_CAP_NUM`、`T_CAP_TEXT`

前景图形语义对象：四个节点边框 `G_NODE_OBJECT_BORDER`、`G_NODE_RELATION_BORDER`、`G_NODE_LOGIC_BORDER`、`G_NODE_TASK_BORDER`；三支主依赖箭头 `G_MAIN_ARROW_1..3`；关系节点内图形箭头 `G_REL_INLINE_ARROW`；逆向核对折返箭头 `G_AUDIT_ARROW`。五个箭头头部另建子对象掩膜，专门执行 ARROWHEAD-TEXT 检查。

背景/装饰共 6 个：`BG_OUTER_PANEL`、四个节点填充、`BG_AUDIT_LABEL`。它们均不作为前景；尤其白色 `BG_AUDIT_LABEL` 没有被用来掩盖或豁免重叠。

逐元素 PDF bbox、300 dpi 墨迹 bbox、源行、类别与掩膜对应见 `SA1_element_inventory.csv` 和 `SA1_combined_masks_300dpi.png`。

## A. 源级有效字号

当前图源没有 `resizebox`、`scalebox`、`scale` 或 `transform shape`；累计 `graphics_scale=1.000`。

- 四个节点标题：源行 11、14/15/22/23，declared/effective = 10.5/10.5 pt。
- 五个节点正文文字对象：源行 14/15/21/22/23，declared/effective = 10.0/10.0 pt。
- 逆向核对注释：源行 34-35，declared/effective = 10.0/10.0 pt。
- 题注标签、编号和正文：图源行 38，公共样式 `statlearnbook.sty:305` 的 11pt 文档 `small` 实现为 effective 10.0 pt；PDF 字号与 TeX-pt 到 bp 的换算相符。

所有一般读者文字 effective_pt >= 9.5 pt。同角色源级 max/min=1.000、绝对差 0.000 pt，满足 <=1.03 和 <=0.25 pt；单面板无跨面板同角色缩放。节点标题/正文的有意层级为 10.5/10.0=1.05，低于强调绝对上限 1.25，且四节点一致。

完整记录见 `SA1_font_audit.csv`。

## C-D-E. 300 dpi 墨迹高度、同类比例与角色层级

按局部背景色差 >=20/255 建立墨迹掩膜，实测如下：

| ELEMENT_ID | H_ink_px | 类别中位数 | 对中位数比例 |
|---|---:|---:|---:|
| T_OBJ_TITLE | 41 | 41.5 | 0.987952 |
| T_REL_TITLE | 41 | 41.5 | 0.987952 |
| T_LOGIC_TITLE | 42 | 41.5 | 1.012048 |
| T_TASK_TITLE | 42 | 41.5 | 1.012048 |
| T_OBJ_BODY | 38 | 38 | 1.000000 |
| T_REL_DOMAIN | 38 | 38 | 1.000000 |
| T_REL_RANGE | 38 | 38 | 1.000000 |
| T_LOGIC_BODY | 38 | 38 | 1.000000 |
| T_TASK_BODY | 39 | 38 | 1.026316 |
| T_AUDIT | 38 | 38 | 1.000000 |
| T_CAP_LABEL | 38 | 38 | 1.000000 |
| T_CAP_NUM | 28 | 28 | 1.000000 |
| T_CAP_TEXT | 39 | 39 | 1.000000 |

- CJK 最小 38 px，超过 30 px 硬门；数字 `1.1` 为 28 px，超过 24 px 硬门。
- 本图无拉丁/希腊/公式脚本类文字。中间箭头是图形，不拿箭头高度冒充文字字号。
- 节点标题同类像素 max/min=42/41=1.024390；节点正文 max/min=39/38=1.026316；均位于 [0.92,1.08]。
- CJK 节点标题中位数/节点正文 BASE 中位数=41.5/38=1.092105；标题语义强调明显但克制，低于 1.25。注释为 1.000000，题注正文为 1.026316，均不抢主体。
- 题注数字因脚本类别不同，不与 CJK 全高直接比墨迹高度；它按 effective 10 pt 与数字 24 px 独立硬门验收。

完整字段见 `SA1_pixel_measurements.csv`。

## F. 零重叠、净空和裁切

对全部 13 个文字对象执行全组合 TEXT-TEXT；对每个文字对象执行全部箭头、箭头头部、四个节点边框检查；另执行跨读者区域和图像边缘检查。共 273 对。

- TEXT-TEXT 同面板 bbox 最小净空：9.000 px（要求 >=4）。
- 主图到题注相邻读者区域最小净空：8.000 px（保守按跨面板要求 >=8）。
- TEXT-LINE_ARROW/ARROWHEAD 最小净空：12.928 px（要求 >=3）。
- TEXT-NODE_BORDER 最小净空：15.000 px（要求 >=5）。
- TEXT-IMAGE_EDGE 最小净空：29.000 px（要求 >=6）。
- 全部文字、箭头头部、线和节点边框到原生裁图边缘的前景最小净空：29 px；没有前景触边，`CLIP_PIXEL_COUNT=0`。
- 所有逐对 `OVERLAP_PIXEL_COUNT=0`。

关键箭头复核：

- `G_REL_INLINE_ARROW` 在源行 16-20 由内联 TikZ `\draw` 产生；PDF 文本提取只出现“定义域”和“值域”两个独立文字 span，箭头另见 vector drawing，故它不是文字字形。
- 源几何：路径 4.90 mm、Stealth 头 1.55 x 1.05 mm、线宽 0.72 pt；300 dpi 墨迹 bbox `(1055,1375,1115,1389)`，60 x 14 px。
- `T_REL_DOMAIN` 到整支图形箭头：重叠 0，净空 12.928 px；最近点 `(1042,1386)` 与 `(1055,1381)`。
- `T_REL_RANGE` 到整支图形箭头：重叠 0，净空 13.318 px；最近点 `(1128,1378)` 与 `(1114,1381)`。
- 箭头头部到 `T_REL_RANGE`：重叠 0，净空 13.318 px。
- 三支主依赖箭头到任一文字的最小净空分别为 42.566、48.092、41.942 px，重叠均为 0。
- 逆向核对折返箭头到注释：重叠 0，净空 13.000 px；测量不借助白色底遮盖。

逐对最近坐标与全部数值见 `SA1_overlap_report.csv`；测量算法和汇总见 `SA1_measurement_manifest.json`。

## 数学语义、图文一致与阅读路径

MATH_SEMANTICS: PASS。主链为“对象声明 -> 关系与映射 -> 运算与逻辑 -> 可核验任务”，方向与“右侧内容使用左侧定义”一致；节点内“定义域 -> 值域”正确表达映射方向。虚线由任务端折返对象端，表达逆向核对，不表示可逆蕴含。

TEXT_CONSISTENCY: PASS。图内节点、题注和 `V1-C01.tex:119` 的相邻正文一一对应：正文明确要求从任务端逆向核对，并说明箭头是使用关系而非可逆蕴含。

READING_ORDER: PASS。三支同形实线箭头建立唯一左到右主路径；灰色虚线单独编码返回核对路径；中间小箭头只服务于定义域到值域，不与主链混淆。

CAPTION: PASS。题注完整、单行，准确总结依赖关系与箭头含义，没有把方法细节堆进图内。

## 四视图、灰度与页面融合

- `SA1_full_page_200dpi.png`：完整页无孤行、异常大留白、裁切或图题分离；图宽、上下留白与例题衔接协调。
- `SA1_figure_crop_300dpi.png`：节点标题、正文、箭头和题注层级稳定；普通文字没有成为第一视觉焦点。
- `SA1_standalone_300dpi.png` / 各 1:1 ROI：四节点、三支主箭头、内联图形箭头和返回线均锐利且有充分净空。
- `SA1_grayscale_300dpi.png`：主路径仍由实线箭头、返回路径仍由灰色虚线和结构位置区分；不依赖颜色才能理解。
- 字号协调：10.5 pt 标题与 10.0 pt 正文形成轻量层级，没有突兀大字或过小字。本候选无需缩小；若未来调整，仍须保持 9.5 pt、像素下限及全部比例门槛。

VISUAL_HARMONY: PASS。

GRAYSCALE: PASS。

PAGE_INTEGRATION: PASS。

## 技术检查

- R90 `main_full.log` 中：LaTeX Error、Package Error、Undefined control sequence、Emergency stop、Fatal error、Float(s) lost、undefined references/rerun、Overfull、Underfull 均为 0。
- `main_full.aux` 中 `fig:V1-C01-language-flow` 稳定为图 1.1，逻辑页 4；R90 物理页定位为 17。

LAYOUT: PASS。

REQUIRED_FIXES: 无。

EVIDENCE_USED: `SA1_official_page17.pdf`、`SA1_full_page_200dpi.png`、`SA1_full_page_300dpi.png`、`SA1_figure_crop_300dpi.png`、`SA1_standalone_300dpi.png`、`SA1_grayscale_300dpi.png`、全部 `SA1_roi_*_300dpi_1to1.png`、`SA1_text_measurement_overlay_300dpi.png`、`SA1_combined_masks_300dpi.png`、`SA1_font_audit.csv`、`SA1_pixel_measurements.csv`、`SA1_overlap_report.csv`、`SA1_element_inventory.csv`、`SA1_measurement_manifest.json`、`SA1_render_record.md`。

## 子任务回传

- assigned_scope: R90 官方整书物理页 17 的 FIG-P020-01 R5 只读盲审。
- completed: 完成原生 300 dpi 提取、四视图、全元素清单、源级字号、像素高度、角色/同类比例、273 对重叠/净空、裁切、语义、题注、灰度、页面和编译引用检查。
- files_changed: 仅在本证据目录新增 `SA1_*` 证据、测量脚本及本报告；没有修改任何 LaTeX、公共样式、章节、inventory 或状态文件。
- decisions: SA1 候选 PASS；不得登记最终通过。
- unresolved: 等待独立 SA3 和根签发。
- validation: 所有 §9.2.1 适用硬门均有正式数值证据并通过。
- next_action: 根线程把当前 R90 候选和本目录交给全新独立 SA3 重测；SA3 通过后再由根签发。
