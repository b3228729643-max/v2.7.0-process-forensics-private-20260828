RESULT: FAIL

# FIG-P126-01（图 8.1）SA1 STRICT-R1 独立重新资格审查

- 审查身份：独立 SA1，只读；未读取、未引用旧 PASS 或旧 SA 结论。
- 官方候选：`main_full.pdf` R90，物理页 137（PDF 零基页 136），813 页整书中的唯一完整题注定位页。
- 当前源：`fig_v1_c08_coordinate.tex`。
- 结论边界：本报告只判定本轮候选不合格；不更新 inventory/state，不宣称全书结论。

## 1. 硬门矩阵

| 硬门 | 结果 | 实测依据 |
|---|---:|---|
| SOURCE_FONT_PASS | false | `x^(0)` 与 `x*` 基准 9.2pt；步骤号 1--7 为 8.6pt，均低于 9.5pt |
| PIXEL_HEIGHT_PASS | false | `T-STEP-2=23px<24px`、`T-STEP-7=23px<24px`、`T-XSTAR-SCRIPT=14px<15px` |
| SAME_CLASS_RATIO_PASS | true | 步骤数字相对中位数范围 `[0.958,1.042]`；其余同角色同脚本类均在 `[0.92,1.08]`，源级同类差值均为 0 |
| ROLE_RATIO_PASS | false | 以步骤数字中位数 24px 为 BASE：轴标签 31/24=1.292>1.18；图例 45/24=1.875>1.10；普通注释基准 `x` 为 21/24=0.875<0.95 |
| OVERLAP_PIXEL_COUNT | 73 | 5 个独立对象对共有 73 个非法前景交叠像素；任一像素即失败 |
| CLIP_PIXEL_COUNT | 0 | 48 个对象掩膜均完整落在 2481x3508 官方页内；最小文字到官方页边 300px |
| MIN_TEXT_CLEARANCE_PX | 0 | 有交叠；无交叠但仍不足的两对分别只有 2px、1px 保守空白净空 |
| VISUAL_HARMONY_PASS | false | 步骤号/普通注释过小，而轴标签与图例相对 BASE 过大；数据曲线穿字 |
| MATH_SEMANTICS_PASS | false | 正文定义精确坐标 `argmin`，但轴对齐等高线与 q0--q7 端点不满足坐标子问题最小化；正文又描述“主轴不对齐”，图中却完全轴对齐 |
| TEXT_CONSISTENCY_PASS | false | 题注“每段只改一个坐标”成立，但正文的坐标失配几何与图中等高线方向不一致 |
| GRAYSCALE_PASS | false | 实线/虚线编码可区分，但灰度视图保留全部穿字和净空失败，不能通过完整灰度验收 |
| PAGE_INTEGRATION_PASS | true | 200dpi 整页无裁切、无异常大留白，题注与后文分页稳定；局部图自身失败不等同于分页失败 |
| TECHNICAL_BUILD_PASS | true | 独立 LuaLaTeX 1 页输出；LaTeX/Package Error、Undefined control sequence、Emergency stop、Fatal、Overfull/Underfull 均为 0 |

因此不满足 Goal §9.2.1-H 的全真条件，必须 FAIL。

## 2. 官方页、四视图与坐标系统

- 物理页：137；页面尺寸 `595.276001pt x 841.890015pt`。
- 200dpi 整页：`1654x2339`；文件 `full_page_200dpi.png`。
- 300dpi 原生整页：`2481x3508`；文件 `full_page_300dpi.png`。渲染矩阵为 `(300/72,300/72)`，未 resize。
- 图+题注裁剪：PDF `(105,55,475,263)pt`，原生像素 `(437,229,1980,1096)`；文件 `figure_crop_300dpi.png`。
- 图体裁剪：PDF `(145,55,440,243)pt`，原生像素 `(604,229,1834,1013)`；文件 `figure_only_300dpi.png`。
- 独立图：`standalone_wrapper.pdf` 直接引用当前源；原生 300dpi 整页 `2481x3508`，前景紧裁 `(670,260,1847,1012)`；文件 `standalone_300dpi.png`。
- 灰度：由原生 300dpi 图+题注裁剪直接转灰，不改尺寸；文件 `grayscale_300dpi.png`。
- 1:1 ROI：`roi_x0_300dpi_1to1.png`、`roi_steps_300dpi_1to1.png`、`roi_xstar_300dpi_1to1.png`、`roi_axes_300dpi_1to1.png`、`roi_legend_300dpi_1to1.png`。
- 所有对象 bbox 叠加见 `element_bbox_overlay_300dpi_1to1.png`；渲染命令、DPI、裁剪坐标见 `commands.txt` 与 `render_manifest.txt`。

## 3. 源级字号与 300dpi 实际墨迹

无 `resizebox/scalebox/transform shape`，累计 `graphics_scale=1.000`。TeX pt 到 PDF bp 的 `72/72.27` 换算不是图形缩放。`slfig axis` 在 axis 选项中晚于图专属 style，使轴标签最终解析为 10pt；全局 `every axis` 也使图例最终为 10pt，均由官方 PDF 字体 span 复核。

| 元素 | 源行 | 最终有效字号 | 原生 H_ink | 门槛 | 结论 |
|---|---:|---:|---:|---:|---|
| `T-X0-BASE` (`x`) | 44 | 9.2pt | 21px | lowercase 17px | 源级 FAIL |
| `T-STEP-1..7` | 45--53 | 8.6pt | 24,23,24,24,24,25,23px | digit 24px | 全部源级 FAIL；2、7 像素也 FAIL |
| `T-XSTAR-BASE` (`x`) | 61--62 | 9.2pt | 21px | lowercase 17px | 源级 FAIL |
| `T-XSTAR-SCRIPT` (`*`) | 61--62 | 由 9.2pt 基准自然派生，约 6.44pt | 14px | natural script 15px | 像素 FAIL，且父公式基准也低于 9.5pt |
| `T-XAXIS/T-YAXIS` | 16 | 解析后基准 10pt | 基准 21px、下标 26px | 17/15px | 单元素像素 PASS；角色比 FAIL |
| 两条图例 | 64,66 | 解析后基准 10pt | CJK 38px、`x` 21px、下标 26px | 30/17/15px | 单元素像素 PASS；角色比 FAIL |
| 题注 | 69 | 10pt | CJK 38--43px、数字 28px | 30/24px | PASS |

完整逐元素表为 `after_pixel_measurements.csv`；源级级联为 `source_font_audit.csv`；同类比与角色比分别为 `same_class_ratio_checks.csv`、`role_ratio_checks.csv`。每个文字元素均有 `masks/T-*.png` 独立掩膜。

## 4. 像素级零重叠与净空

掩膜由官方 PDF 页导出 MuPDF SVG path，再仅保留单个语义对象，使用同一 MuPDF 以 300dpi 渲染；前景阈值为相对白底任一 RGB 通道差 `>=20/255`。这样可发现被后绘制文字覆盖、在最终合成图中不易直接看出的底层曲线穿字。

| 文字对象（全页 bbox px） | 图形对象（全页 bbox px） | 交叠像素 | 保守空白净空 | 判定 |
|---|---|---:|---:|---|
| `T-STEP-1` `(767,483)-(781,507)` | `G-CONTOUR-OUTER` `(672,406)-(1781,809)` | 12 | 0 | FAIL |
| `T-STEP-2` `(1001,450)-(1017,473)` | `G-CONTOUR-2` `(797,452)-(1656,763)` | 4 | 0 | FAIL |
| `T-STEP-4` `(1125,519)-(1143,543)` | `G-CONTOUR-INNER` `(1034,537)-(1419,677)` | 0 | 2px <3 | FAIL |
| `T-STEP-5` `(1096,585)-(1111,609)` | `G-AXIS-X` `(652,600)-(1562,615)` | 24 | 0 | FAIL |
| `T-STEP-6` `(1186,542)-(1201,567)` | `G-CONTOUR-INNER` `(1034,537)-(1419,677)` | 0 | 1px <3 | FAIL |
| `T-XAXIS-BASE` `(1503,561)-(1525,582)` | `G-CONTOUR-3` `(916,494)-(1537,721)` | 25 | 0 | FAIL |
| `T-XAXIS-SUB` `(1528,566)-(1542,592)` | `G-CONTOUR-3` `(916,494)-(1537,721)` | 8 | 0 | FAIL |

- 5 个交叠对象对合计 73 个非法像素交集；另外 2 对虽为 0 交叠，却低于 3px 净空。
- 独立 TEXT--TEXT 最小保守净空为 38.319px，满足 4px。
- 文字到官方页面边缘最小 300px，满足 6px；单面板，无跨面板门；没有节点边框对象。
- 失败对象对的原生 1:1 着色证据在 `risk_rois/`：红=文字、蓝=图形、黄=交集。全部对象对及最近距离在 `pairwise_object_checks.csv`，失败与最近对象摘要在 `high_risk_pairs.csv`。
- `CLIP_PIXEL_COUNT=0`；所有文字、曲线、箭头头部、标记均有非空完整掩膜，且 bbox 不接触官方页边。

## 5. 数学/几何与图文一致性

正文 `V1-C08.tex:343--346` 明确定义每次更新为精确坐标子问题 `argmin`。当前四条等高线（源 20--27）均为 `x=R cos t, y=r sin t`，即中心在原点且主轴与坐标轴完全对齐。对这种目标，固定 `x1` 后精确更新 `x2` 应直接得到 0，固定 `x2` 后精确更新 `x1` 也应直接得到 0；但 q1 为 `(-3.20,.85)`、q2 为 `(-1.65,.85)`，已与等高线语义冲突。

即使把图解释成一个含交叉项的固定二次型，精确坐标最小点的比例也必须恒定；当前 x2 更新的 `y/x` 依次为 `-0.265625,-0.193939,-0.114286`，x1 更新的 `x/y` 依次为 `-1.941176,-2.187500,0`，同样不可能来自同一固定二次型。与此同时正文 350--356 行解释“椭圆主轴与坐标轴不对齐时之字形”，图中却画成完全对齐。数值证据见 `math_semantics_check.csv`。

题注中的局部命题“每个子步只改变一个坐标”成立，因为每段线均水平或竖直；但它不能抵消上述目标/端点/正文条件的不一致。

## 6. 四视图、灰度与页面融合

- 300dpi 图裁剪与独立图均复现同一问题，不是页面截图或缩放伪影。
- 灰度中蓝色实线与青色虚线仍可由线型区分，轮廓/坐标轴也可辨；但步骤 1、2、5 和 `x_1` 的穿线仍在，步骤 4、6 的净空仍不足，因此完整 `GRAYSCALE_PASS=false`。
- 200dpi 整页中图宽、题注、后续正文和节标题分页自然，无裁切或异常留白，故单列 `PAGE_INTEGRATION_PASS=true`；这不改变图本体 FAIL。
- 字号观感上，步骤号和两个普通公式注释相对轴标签/图例偏小，图例/轴标签相对当前 BASE 又显得突兀；不能只缩小大字来规避，任何调整后仍须保持基准 `>=9.5pt` 和全部像素下限。

## 7. 给 SA2 的可执行定向修复

1. **先修数学模型与轨迹（源 20--42）**：不要继续使用轴对齐 `({R*cos(x)},{r*sin(x)})` 配合任意 q 点。建议明确使用
   `f(x_1,x_2)=x_1^2+x_1x_2+x_2^2`（即 `rho=1/2`），画旋转等高线
   `x=r(cos t+sqrt(3)sin t)/sqrt(2)`、`y=r(cos t-sqrt(3)sin t)/sqrt(2)`；取 `q0=(-3.20,2.20)`，按精确循环坐标最小化依次设
   `q1=(-3.20,1.60)`、`q2=(-.80,1.60)`、`q3=(-.80,.40)`、`q4=(-.20,.40)`、`q5=(-.20,.10)`、`q6=(-.05,.10)`、`q7=(-.05,.025)`，把最优星标单独保留在 `(0,0)`。这样每个端点都满足 `x_2=-x_1/2` 或 `x_1=-x_2/2`，正文“主轴不对齐/之字形”与图一致，且 q7 是逼近而非冒充有限步精确到达。
2. **源 45--53 步骤号**：把所有 `8.6pt` 统一提高到建议起点 `10.0pt`（不得低于 9.5pt），再依据新几何逐个重放。步骤 1、2、5 必须移出相交曲线/轴；步骤 4、6 必须留出至少 3px 原生空白，不能只做到“不碰”。
3. **源 44、61--62 普通公式注释**：`9.2pt` 统一提高到建议起点 `10.0pt`；保证 `x*` 的自然上标实际墨迹 `>=15px`。若需适当缩小，只能在最终仍满足 9.5pt/像素/角色比且不损害整体观看时进行。
4. **源 4--7 与 axis 选项 12--18 的级联**：当前图专属 `tick/label style` 写在 `slfig axis` 之前而被公共 10pt 样式覆盖。改为 `[slfig axis,slfig-FIG-P126-01-axis,...]` 或在 axis 末尾使用 `.append style`，使最终有效字号可追溯；图例也需使用最终可验证的 9.5--10pt 设定。不要让源码声明与官方 PDF 最终字号不一致。
5. **`x_1` 轴标**：把标签移到所有等高线外侧，或扩大 `xmax` 后置于轴箭头外侧，原生文字到任一轮廓/箭头必须 `>=3px`；不能依赖曲线从字后穿过。
6. **重新验收**：SA2 修改后必须独立编译官方页和 standalone，重新生成 2481x3508 原生 300dpi；对全部 24 个文字子元素和所有曲线/箭头/标记重建掩膜，不能只复测本报告列出的 7 对。只有全部硬门为 true、非法像素 0、clip 0、净空达标，才可交回新的 SA1。

## 8. 证据索引

- 渲染/裁剪：`render_manifest.txt`、`commands.txt`。
- 官方页与四视图：`official_page_137.pdf`、`full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。
- 源与正文快照：`source_excerpt_numbered.txt`、`context_excerpt_numbered.txt`。
- 字号/像素/比值：`source_font_audit.csv`、`after_pixel_measurements.csv`、`same_class_ratio_checks.csv`、`role_ratio_checks.csv`。
- 对象/掩膜/重叠：`graphic_elements.csv`、`masks/`、`pairwise_object_checks.csv`、`high_risk_pairs.csv`、`risk_rois/`、`element_bbox_overlay_300dpi_1to1.png`。
- 数学语义：`math_semantics_check.csv`。
- 技术日志：`standalone_wrapper.log`、`standalone_log_hard_scan.txt`。
