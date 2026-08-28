# FIG-P632-01｜ROOT APPLY R3.5 像素级复核

RESULT: **FAIL_PIXEL_GEOMETRY**  
SPLIT_REQUIRED: **NO**

## 候选与构建身份

- 候选来源：SA2-R2.3；仅将上下条件面板的三行公式块由局部 `(0.05,2.68)` 同构右移至 `(0.45,2.68)`。
- 页面 PDF：`p632_root_r3p5_page.pdf`，A4 单页，82152 bytes。
- 独立 PDF：`p632_root_r3p5_standalone.pdf`，A4 单页，50302 bytes。
- 300 dpi 彩色页、灰度页与独立页均为 `2481x3508` 原生像素；未缩放审查。
- 构建管线：TeX Live 2026 LuaLaTeX；MiKTeX、XeLaTeX 均未使用。

## 机器门

- page/standalone 硬日志命中：`0/0`。
- AUX 精确回写图号/逻辑页：`33.2 / 664`。
- FLS 均命中当前 wrapper、`statlearnbook.sty`、`release_version.tex`、`figure-style-v2.3.1.tex` 与当前 P632 图源。
- 页面版 8 种、独立版 4 种字体均为 `emb=yes sub=yes uni=yes`。
- 两份 PDF 均为 A4 单页；三个 PNG 均为原生 300 dpi `2481x3508`。

## 原生像素 ROI 门

审查使用不缩放、不插值的 1:1 裁剪；坐标均以独立页左上角为原点，格式为 `[x,y,width,height]`。

1. 上条件面板公式/纵轴：`p632_root_r3p5_roi_upper_formula_axis_1to1.png`，`[1280,260,900,620]`。R2.3 已使积分号与纵轴形成明显白隙，原投诉点已修复。
2. 下条件面板公式/纵轴：`p632_root_r3p5_roi_lower_formula_axis_1to1.png`，`[1260,800,930,700]`。积分号与纵轴亦已分离，原投诉点已修复。
3. 上映射标签/纵轴：`p632_root_r3p5_roi_upper_map_axis_1to1.png`，`[1080,570,470,320]`；精细接触区 `p632_root_r3p5_roi_upper_map_axis_contact_1to1.png`，`[1360,640,110,130]`。纵轴实墨右缘为局部 `x=45`，`m_2(b)` 末端括号抗锯齿实墨从局部 `x=48` 开始，中间只有局部 `x=46,47` 两个纯白像素；最小净空约 **2 native px**，按 `1--3 px = FAIL` 的新门槛判失败。
4. 下映射标签/纵轴：`p632_root_r3p5_roi_lower_map_axis_1to1.png`，`[1120,1030,500,390]`；精细接触区 `p632_root_r3p5_roi_lower_map_axis_contact_1to1.png`，`[1340,1170,150,150]`。纵轴中心为局部 `x=64`；普通轴像素为 RGB `(77,83,88)`，但标签穿越处同一列在局部 `y=55` 与 `y=70` 变为标签实墨 RGB `(31,35,40)`，即 `m_1(a)` 与纵轴发生 **0 px 实际接触/覆盖**，判失败。
5. 联合面板/两条映射：`p632_root_r3p5_roi_joint_mapping_1to1.png`，`[420,500,1050,850]`。联合等高线、切片、点、坐标轴及其标签未发现新的互相覆盖，但该 ROI 同时再次显示两条映射标签在条件面板入口处净空不足。
6. 下曲线/警示框边界：`p632_root_r3p5_roi_warning_boundary_1to1.png`，`[1220,1180,920,430]`。曲线、横轴、`3/5` 与红框之间有连续白隙，未见接触。

任一彩色、灰度或 standalone 证据失败即整 UID 失败；standalone 已给出确定接触，故无需用整页缩略图稀释该结论。彩色页与灰度页采用同一几何，也可见相同入口冲突。

## 字号与视觉层级门

- 图源统一使用 `every node/.style={font=\fontsize{9.6pt}{11.5pt}\selectfont}`；未发现 `tiny/scriptsize/footnotesize/small/large` 或第二组局部 `fontsize` 覆盖，也没有总体缩放。
- 300 dpi ROI 中，轴标签、映射注释、公式正文和警示框正文的代表性实墨高度均处于同一约 9.6 pt 视觉层级；上下同构面板字号一致，未见无语义理由的突增或缩小。
- TYPOGRAPHY=`PASS`；但几何门为 `FAIL`，所以 UID 总结论仍为 `FAIL_PIXEL_GEOMETRY`。

## 下一轮最小修复要求

- 保留 R2.3 的两个公式块位置，不得让积分号回退到纵轴。
- 仅调整两条映射路径标签沿路径的位置或局部偏移，使 `m_2(b)` 与上纵轴、`m_1(a)` 与下纵轴/原点均取得稳定白隙；下一轮在三类 300 dpi 证据中的修复目标应不少于 **12 native px**，避免刚好擦过 4 px 验收线。
- 不改变数学、数值、caption、label、alt、曲线、等高线、坐标、字号与警示框内容。
- 根线程在本轮不启动独立 SA1/SA3 终审；先交回专属 SA2 做 R2.4，再以新 jobname 构建 R3.6。

RESULT=FAIL_PIXEL_GEOMETRY  
SPLIT_REQUIRED=NO
