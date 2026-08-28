# FIG-P634-01 — SA2 STRICT R4 修复与本地候选报告

生成时间：2026-08-24 01:57 +08:00

## 结论

`RESULT = LOCAL_CANDIDATE_PASS_FOR_ROOT_BUILD_AND_NEW_SA1`

`FINAL_FIGURE_PASS = NOT_CLAIMED`

当前唯一图源已完成语义保持的结构化修复。本地候选在原生 300 dpi、1:1、无插值、无膨胀口径下，源字号、逐字形、同角色比例、角色层级、标准自动题注、最终可见纹理、全 pair 重叠与净空、裁切、数学语义、灰度和视觉协调均通过。该结论只授权 root 构建新的全书候选并派独立 SA1；本 SA2 不宣布最终 PASS，也不进入 SA3。

## FILES_CHANGED

唯一业务源码：

- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex`

专属证据：

- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P634-01\STRICT_R4_SA2\` 下的局部 wrapper/PDF、审计脚本、四视图、CSV/JSON、对象 raw/mask/overlay、paint-order 证据、diff、本视觉记录与本报告。

未修改公共样式、正文、合并入口、central build、inventory 或 state；未生成官方 R94。最终两次局部编译的输出均限定在本专属证据目录。

历史披露：本轮早期一次错误命令曾把变量名当作字面输出目录；确认精确目录后只清理了该次生成的五个局部文件。最终候选重编译未在源码目录留下 `symbols.idx` 或其他产物。

## 最终源码变更

完整 R93→当前候选 diff：`source_before_after.diff`。

### 1. 结构化消除原 R3 低轮廓运算符/标点失败

- 行 17：标题使用自然中文短语，不再依赖低轮廓冒号。
- 行 18–25：固定顺序显示为 `1 / 2 / 省略 / j 前一位 / j / j 后一位 / 省略 / d`；小写变量与正文一致，顺序不变。
- 行 28–39：八个坐标框改为坐标角色卡；逗号、等号、加减号和长公式不再堆在框内。
- 行 44–49：轮内状态拆成独立标题与左右字段，明确左侧同轮新值、右侧上一轮旧值。
- 行 51–58：`x^{[d]}` 与 `x^{(t)}` 的等价由双向箭头和“同一状态”表达；成为样本由单向箭头和“仅此记录”表达。
- 行 60–62：使用公共 `\caption` 自动生成标准可见“图 33.3”，保留可选短题注、counter、anchor、`\label`、引用与 LoF。

### 2. 真实修复状态卡跨行碰撞

- 状态卡最小高度为 `10.5mm`。
- 状态标题位于 `y=-1.25cm`，左右说明位于 `y=-1.81cm`。
- 最终独立 raw mask：标题 CJK 与右说明 CJK `overlap=0`、净空 `23px`；标题与最近右侧数学对象净空 `29.15px`。没有把两行合并为一个 parent，也没有用中点切分像素。

### 3. 真实修复文字—斜线纹理净空

- 行 8 定义正常不透明白底文字牌 `sl634-halo`：横向内边距 `1.5pt`、纵向 `1.25pt`，无描边、无缩放。
- 行 28–35 将四个已更新节点拆成“原斜线框 + 前景白底文字牌”。可见文字、位置、字号、顺序和算法含义完全不变。
- 证据保留绘制前纹理、PDF 中实际 alpha-1 白色填充、按真实绘制顺序得到的最终可见纹理；不按文字轮廓、中点或结果导向切分。

## 语义不变量

`semantic_invariants.json = PASS`：

1. 八槽源级顺序固定且每项唯一：`1,2,…,j−1,j,j+1,…,d`。
2. 第 `j` 步的左侧字段是同一轮已写回的新值，右侧字段是上一轮旧值。
3. `x^[j]` 只表示 sweep 内状态。
4. 只有完成第 `d` 步后的 `x^[d]` 与 `x^(t)` 是同一状态；只有该状态被记录为轮末样本。
5. alt 精确保留序列和 `只有 x^[d]=x^(t) 是轮末样本`。
6. 没有 `scale/resize/yscale/raisebox/transform shape` 字形畸变命令。

## 标准题注、句点、引用与 LoF

`caption_counter_audit.json = PASS`：

- 可见自动标签恰为 `图33.3`；同页引用也为 `图33.3`，本地页合计出现 2 次，各自角色明确。
- `.aux` 中 `\newlabel{fig:V5-C04-coordinate-sweep}` 为 `33.3`。
- `.aux` 与 `.lof` 的 `\numberline` 均为 `33.3`；LoF 只有 1 条 figure 项，LoF 渲染显示 `33.3`。
- 源码没有局部隐藏 label 或手工重造编号；无重复题注。
- 可见 label 字体：CJK `NotoSansSC-Bold 9.96pt`；数字与句点 `STIXTwoText-Bold 10.06pt`；题注正文 `NotoSerifSC-ExtraLight 9.96pt`。

`caption_separator_punctuation_audit.csv = PASS`：

- 自动编号句点有独立 ELEMENT_ID `SYM_CAPTION_LABEL_DOT_01` 及自身 raw/mask/overlay。
- 原生 300 dpi 非膨胀墨迹为 `H=6px, W=6px, area=32px`，局部背景差门为 `>=20/255`；在 `33.3` 中清楚可辨。
- 它的语义角色是题注编号分隔标点，不是基准数学运算符，因此不误套 22px 数学运算符高度门；正常有效字号、独立可见墨迹和格式一致性均通过。

## 原生 300 dpi 数值审计

输入为 `local_validation.pdf` 第 1 页。页面为 `2481×3508px`，审计裁图为 `1855×863px`；render 后没有 resize、插值或形态膨胀。

对象计数：199 个读者字形、70 个逻辑文字/子串对象、17 个线/边框/纹理对象，共 87 个对象、3741 个全 pair。

### A. 源字号

- 最小有效基字号 `9.6pt >= 9.5pt`；普通文字 9.6pt、状态说明 9.8pt、状态公式/题注 10.0pt、标题 10.6pt。
- `after_font_audit.csv` 70/70 源字号 PASS。
- `source_role_consistency.csv` 21/21 PASS；每个排印角色 max/min 为 `1.0000`、差 `0.00pt`，单面板跨面板比为 1。

### B/C. 逐字形与运算符

`raw_char_measurements.csv` 没有 FAIL：

- 直接适用的 CJK 最小 `33px >= 30px`。
- 数字最小 `25px >= 24px`。
- 数学小写/base 最小 `20px >= 17px`。
- 自然脚本最小 `24px >= 15px`。
- 12 枚自然脚本括号/方括号全部 `36px >= 15px`。
- 低笔画中文保留 raw，但仅从“接近全字面高度”比较器中标 N/A；没有用父元素高度替代。
- 题注编号句点使用上节独立的语义标点门，不与数学运算符混类。

`operator_height_audit.csv` 中当前 12 个自然脚本 `(`、`)`、`[`、`]` 均有独立 ELEMENT_ID/raw/mask/overlay，12/12 PASS。

### D. 同脚本同语义角色

`same_class_ratio_audit.csv` 70/70 PASS。分组依据预先存在的数学功能，不按字面 glyph 临时拆组：

- `CURRENT_COORDINATE_INDEX`：小写 `j` 在顺序、节点、状态字段和题注中的 MATH_BASE 高度为 `35/36/37px`，max/min `1.0571`。
- `TERMINAL_DIMENSION_INDEX`：小写 `d` 的 MATH_BASE 为 `28/29px`，max/min `1.0357`；自然脚本两例均 `28px`。
- `ITERATION_INDEX`：自然脚本两例均 `24px`。
- `WITHIN_SWEEP_STATE`、`END_SWEEP_STATE`、`ROUND_STATE` 的状态 `x` 重复实例均为 `20px`。
- 全部角色中最大 max/min 为 `1.0588`（`NODE_CJK`）；每个 ELEMENT_ID/角色中位数都在 `[0.92,1.08]`。

### E. 角色层级

`role_ratio_audit.csv` 70/70 PASS。标题/CJK BASE 为 `1.1714`；题注标签/CJK BASE 为 `1.0857`；题注数字 BASE 为 `1.0769`；状态标题/CJK BASE 为 `1.0571`。普通注释、公式块和自然脚本均处于各自允许范围，单面板跨面板比为 1。

### F. 全 pair 重叠、净空、纹理与裁切

`after_overlap_report.csv` 覆盖 3741/3741 pair：

- 非法最终可见 foreground overlap：`0px`；同一复合对象内部 foreground overlap：`0px`。
- 独立 text-text 最小净空 `23px >= 4px`。
- text-line/arrow 最小净空 `15px >= 3px`。
- text-node-border 最小净空 `6px >= 5px`。
- 7 个同节点 text/formula—semantic hatch pair 全部 `overlap=0`，净空 `7,5,8,5,7,7,14.04px`，最小 `5px >= 3px`。
- 与本节点无语义关系的远距离 texture pair 保留 `INTENTIONAL_TEXTURE_UNRELATED` 登记，不套 3px 门，但实际 overlap 仍为 0。
- clip `0px`；最小页面边缘净空 `286px >= 6px`；单面板无跨面板 8px 项。

## 不透明 halo 与 paint-order 证据

`texture_paint_order_audit.csv = PASS`：

- `pre_occlusion_validation.pdf` 只用于证据：它保留相同框、pattern 相位和布局，但把四个前景 halo 设为完全透明，从而得到绘制前纹理 raw mask。
- 最终 PDF 的矢量绘制记录中，四个 alpha-1 白色 halo 的 seqno 为 `21/23/25/27`；各自位于对应斜线框之后、文字之前。
- 只按这些真实白色矩形填充路径的像素中心几何遮挡绘制前纹理；不减去文字轮廓，不使用中点分割，不膨胀 mask。
- 四个纹理的 `pre → occluded → final visible` 像素分别为 `4292→2086→2206`、`4290→2095→2195`、`4195→2180→2015`、`4275→3133→1142`。
- `texture_paint_order/` 对每个节点保存 `PRE_OCCLUSION_TEXTURE_MASK`、`OPAQUE_HALO_MASK`、`FINAL_VISIBLE_TEXTURE_MASK` 与 `PAINT_ORDER_8X`；`objects/` 保存最终 raw/mask/overlay。
- `semantic_texture_clearance_audit.csv` 的几何门使用最终可见纹理，不使用绘制前纹理。

`machine_consistency.json = PASS`，明确机器摘要使用标准题注、小写数学记号、最终可见纹理与 7 个真实 texture pair。

## 编译与视觉验收

`local_compile_audit.json = PASS`：LuaLaTeX 直接两遍，2 页；0 LaTeX error、0 undefined reference、0 overfull、0 underfull。

`after_visual_acceptance.md` 记录：

- `FONT_VISUAL_HARMONY_PASS = true`
- `GRAYSCALE_PASS = true`
- `MATH_SEMANTICS_PASS = true`
- `TEXT_CONSISTENCY_PASS = true`
- `LOCAL_PAGE_INTEGRATION_PASS = true`

最终图中白底文字牌仅在斜线节点中心形成正常留白，不改变节点尺寸或阅读顺序；斜线语义仍清楚，文字更干净。标准题注为两行，与公共样式协调。

## 关键证据索引

- 四视图：`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。
- 字号/字形：`after_font_audit.csv`、`raw_char_measurements.csv`、`after_pixel_measurements.csv`、`operator_height_audit.csv`、`caption_separator_punctuation_audit.csv`。
- 比例：`same_class_ratio_audit.csv`、`source_role_consistency.csv`、`role_ratio_audit.csv`。
- 几何：`after_overlap_report.csv`、`semantic_texture_clearance_audit.csv`、`after_edge_clip_report.csv`、`critical_pairs_manifest.csv`、`object_mask_manifest.csv`。
- paint order：`pre_occlusion_validation.pdf`、`pre_occlusion_figure_crop_300dpi.png`、`texture_paint_order_audit.csv`、`texture_paint_order/`。
- 题注/语义/编译/汇总：`caption_counter_audit.json`、`semantic_invariants.json`、`local_compile_audit.json`、`audit_summary.json`、`machine_consistency.json`。
- 可视总覆盖：`after_text_measurement_overlay_300dpi.png`；右侧 ledger 列出全部 87 个对象。

## 剩余风险

1. 这是局部 wrapper；真实全书分页、物理页、相邻正文与页内融合必须由 root 在新全书候选上重新发现和复核，不能沿用 R93 的物理页假设。
2. 标准题注、引用与 LoF 已在本地通过，但 root 仍须在新全书构建中核对全局 anchor、目录与交叉引用。
3. text-node-border 最小 6px、semantic texture 最小 5px 均过门但接近下限；新 SA1 应从最终全书 PDF 独立重测。
4. SA1 不得复制本目录 CSV 作为独立证据。

## ROOT 下一动作

1. 冻结当前唯一图源；由 root 在中央受控入口构建新的官方全书候选。
2. 从新 PDF 重新发现 FIG-P634-01 的物理页、印刷页和图号；禁止假设仍为 R93 的页码。
3. 直接从新全书 PDF 生成 200 dpi full page 与原生 300 dpi full page/crop/standalone/grayscale，不得 render 后 resize。
4. 派全新独立 SA1 到新证据目录，重新审核全部字形、题注句点、同脚本同角色、角色层级、全 pair、最终可见纹理、clip、灰度、标准题注/引用/LoF 和真实页面融合。
5. 新 SA1 必须重点复核：状态两行独立净空；7 个同节点文字—最终可见纹理 pair；标准自动“图 33.3”；小写 `j/d/t` 与 `x^[j]/x^[d]/x^(t)`；全书页面协调。
6. 只有新 SA1 全门 PASS 后才可派隔离 SA3。本 SA2 到此交权。
