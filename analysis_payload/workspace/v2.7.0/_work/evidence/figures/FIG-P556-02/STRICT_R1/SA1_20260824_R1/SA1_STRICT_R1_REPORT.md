# FIG-P556-02（图30.5）｜独立 SA1 严格视觉、文字与数学首审

## 1. 身份、冻结输入与独立定位

- 任务：`FIG-P556-02`；角色：独立只读 SA1；轮次：`STRICT_R1/SA1_20260824_R1`。
- 冻结候选：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`。
- 真实定位：物理 PDF 第 **602** 页、印刷第 **589** 页、**图30.5**。这由冻结 PDF 的图号和实际题注定位；未采用旧索引的页码字段。
- 图源：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_chain_properties.tex`；直接相邻正文：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C01.tex:628,639-640`；公共样式：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty:275-276,305`。
- 覆盖：14 个语义文字对象、167 个可见字形/运算符/标点、18 个独立 PDF 矢量组件、343 个唯一成对关系。题注自然行流为一个 `CAPTION_PARENT`，未拆成伪文字对象。

## 2. 四视图、固定像素网格与分离 raw mask

`full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png` 与 `grayscale_300dpi.png` 都来自冻结 PDF。唯一测量网格是整张物理页直接 rasterize 的原生 300 dpi 网格；图裁和 standalone 都是该网格的像素切片，绝不 resize。

每个字形以 PDF char bbox 在局部背景差 `>=20/255` 的前景建立未膨胀 raw mask，位于 `masks/glyph_raw/`；文字父对象位于 `masks/text_raw/`。每条边、箭头、箭头头、刻线、marker、节点边框与卡片边框由 PDF path 独立重建到同一网格，位于 `masks/vector_raw/`。节点/卡片填充被排除为背景；数值不使用 paint-order 可见层。本轮没有碰撞失败 pair；仍为 12 个最近临界 pair 保留原图 ROI、双方 raw mask、交集、overlay 与三个最近邻 `8x` 检查图，见 `critical_pair_index.csv` 与 `critical_pair_manifest.md`。

## 3. 源级有效字号

`SOURCE_FONT_PASS: false`；**10/14** 语义对象低于 9.5 pt。面板标题为 10.4 pt、题注 `\small` 为 10.0 pt（通过）；状态标签 9.4 pt、公式与底部摘要 9.2 pt、三条回答注记 8.8 pt（失败）。同角色 source max/min 和绝对差自身一致（`SOURCE_ROLE_RATIO_PASS: true`），但不能抵消最低字号硬失败。完整 declared/effective/font-source 行在 `after_font_audit.csv`；无 graphics scale，`GRAPHICS_SCALE=1.0`。

## 4. 300 dpi 逐字形门

`PIXEL_HEIGHT_PASS: false`；**17/167** 字形未达自身阈值。`after_pixel_measurements.csv` 将每个中文/全角字符、大写/数字、小写/希腊、基准数学运算符/标点和自然脚本各自列出 PDF bbox、raw `H_ink_px`、阈值、局部背景、字体及 raw mask；父公式/整行没有替代任何子串。

## 5. 同类、角色比例与 FONT_VISUAL_HARMONY

`SAME_CLASS_RATIO_PASS: false`；actual raw `H_ink_px` 的同面板、同角色、同脚本审计有 **36** 个失败行（34 个元素/类比与 2 个跨面板同角色同脚本中位数比），绝未用 declared pt、PDF span-size proxy 或 exact-glyph 分组判门。`ROLE_RATIO_PASS: false`，失败行 **3**；CJK BASE 是三张卡重复的普通回答注记，而 LOWER_GREEK、UPPER_DIGIT 与 MATH_OPERATOR 分别使用各自同脚本的公式 BASE。没有可比脚本的角色/脚本组合明确写为 `N/A`，不构成跨脚本伪失败；所有数值均在 `role_ratio_audit.csv`。

`FONT_VISUAL_HARMONY_PASS: false`，`VISUAL_HARMONY_PASS: false`。理由是 8.8--9.4 pt 的可见信息角色低于硬下限，并且 raw-H 角色层级存在失败；“适当缩小”不适用，因为它会进一步违反字号、像素、比例和整体阅读门。

## 6. 零重叠、净空、边缘和裁切

`OVERLAP_PIXEL_COUNT: 0`，`OVERLAP_FAIL_PAIR_COUNT: 0`，`CLIP_PIXEL_COUNT: 0`。全部文字--文字、跨面板文字--文字、文字--线/箭头/marker、文字--节点边框和文字--卡片边框都登记在 `after_overlap_report.csv`；该表每一无序 pair 仅计一次。最小 raw/bbox 净空为 **21.954 px**，其余最小正净空为 **21.954 px**；图证据裁边最小 bbox 净空为 **25.000 px**。边缘/裁切逐项见 `after_edge_clip_report.csv`。

本节的 `OVERLAP/CLIP` 结论只来自双方分离的 native-300dpi raw mask。若本次存在失败或临界对，其交集和 `8x` 证据可由 `critical_pair_manifest.md` 精确追溯。

## 7. 数学、正文、题注、阅读顺序、灰度与页面整合

`MATH_SEMANTICS_PASS: true`：双向 1/2 支撑图与 `i↔j` 正确对应通信/不可约性；`d(i)=gcd{n≥1:P_ii^(n)>0}` 与 2,4,6,8 返回时长示意正确表达周期的 gcd；`E_i[tau_i^+]<∞` 正确给出正常返。三者分别回答连通性、回返节律和平均正回返时间，未相互替代。

`CAPTION_PASS: false`，`TEXT_CONSISTENCY_PASS: false`：图注宣称“三类”却只明说不可约性和周期性，遗漏正常返；更直接地，紧邻 `V5-C01.tex:639` 称本图为三类状态图（可约非周期、不可约周期、不可约非周期），而当前源/PDF 是三卡属性解释图。这是独立从 source → frozen PDF → direct body 得出的结论，不沿用错位索引读图结论。详见 `math_text_semantics_audit.json`。

`READING_ORDER_PASS: true`（从左到右：不可约性、周期性、正常返，再读底部总结）；`GRAYSCALE_PASS: true`（文字、边框与箭头在灰度仍可区分）；`PAGE_INTEGRATION_PASS: true`（图、题注及随后图30.6的页内连接无裁切/异常断行）。这些通过项不覆盖字号、像素、比例和文字一致性硬失败。

## 8. 最终矩阵与移交

```text
RESULT: FAIL
TASK_ID: FIG-P556-02
PHYSICAL_PAGE: 602
PRINTED_PAGE: 589
COVERAGE_PASS: true
SOURCE_FONT_PASS: false (10 failures)
SOURCE_ROLE_RATIO_PASS: true
PIXEL_HEIGHT_PASS: false (17/167 glyph failures)
SAME_CLASS_RATIO_PASS: false (36 failures; actual raw H_ink)
ROLE_RATIO_PASS: false (3 failures; actual raw H_ink)
OVERLAP_PIXEL_COUNT: 0 (0 failing pairs)
CLIP_PIXEL_COUNT: 0
MIN_TEXT_CLEARANCE_PX: 21.954
FONT_VISUAL_HARMONY_PASS: false
VISUAL_HARMONY_PASS: false
MATH_SEMANTICS_PASS: true
CAPTION_PASS: false
TEXT_CONSISTENCY_PASS: false
READING_ORDER_PASS: true
GRAYSCALE_PASS: true
PAGE_INTEGRATION_PASS: true
NEXT_ROLE: SA2
```

SA2 应只修改该图和允许的直接相邻正文：先把答案、公式、状态和摘要提升到有效至少 9.5 pt，再重新排布卡片/间距以保持所有 raw-H 和净空门；补齐图注对正常返的说明，并使正文的图30.5描述与三卡图一致。不得整体缩放规避失败；新候选必须以新 PDF 重新全量 SA1。
