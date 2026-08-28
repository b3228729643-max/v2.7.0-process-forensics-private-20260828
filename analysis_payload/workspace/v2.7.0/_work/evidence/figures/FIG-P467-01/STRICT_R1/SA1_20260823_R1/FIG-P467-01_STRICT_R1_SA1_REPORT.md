# FIG-P467-01｜STRICT_R1｜SA1 正式严格视觉复核报告

## 结论

**RESULT: FAIL**。下一角色必须为 **SA2**，不得进入 SA3。

本次结论来自当前冻结候选而非历史 PASS、历史截图或旧证据：`strict_current_r93_fullbook/main_full.pdf`。图源只读：`src/绘图源码/第04册_无监督学习与矩阵分解/V4-C03/fig_v4_c03_svd_geometry.tex`；本目录之外没有写入任何文件。

## 定位与覆盖

- 冻结 PDF 物理页：**509**；印刷页：**496**；图号：**图26.1**。这与旧任务卡的“物理页 557”不一致，故本次以冻结 PDF 内实际题注定位为准。
- 直接 `pdftoppm` 从冻结 PDF 输出的原生 300 dpi 页面为 `2481 × 3508 px`；未对该 PNG 二次 resize。
- 实测 76 个读者可见字形，包含所有中文、拉丁/希腊、数字、数学上标与标点；基础标点按独立字形测量，未用整行或父公式 bbox 替代。
- 形成 7 个独立 TEXT 对象、54 个独立 PDF/vector 图形对象；覆盖 399 个不应相交对象对（21 个 TEXT–TEXT + 378 个 TEXT–GRAPHIC）。每个对象均有原始 ROI、未膨胀前景 mask 和 bbox/mask overlay；最临界的 8 对另有独立 pair 证据。

## 9.2.1 验收矩阵

| 项目 | 结果 | 证据/实测 |
|---|---:|---|
| SOURCE_FONT_PASS | false | 47/76 可见字形有效字号不足 9.5pt |
| PIXEL_HEIGHT_PASS | false | 3 个独立字形低于像素门 |
| SAME_CLASS_RATIO_PASS | true | 同角色、同脚本的语义文本元素与跨面板标题均满足阈值 |
| ROLE_RATIO_PASS | true | CJK 面板标题/说明 BASE = `37/33 = 1.1212`，位于 `[1.05,1.20]` |
| OVERLAP_PIXEL_COUNT | 0 | 399 个 TEXT–TEXT/TEXT–GRAPHIC 对均无非法前景相交 |
| CLIP_PIXEL_COUNT | 0 | 61 个独立对象均未触碰页面或图裁图边界 |
| 最小文字—文字 bbox 净空 | 20 px | `ANNOTATION` ↔ `CAPTION_LABEL`；门槛 >=4px |
| 最小文字—文字前景净空 | 43.788 px | `ANNOTATION` ↔ `CAPTION_TEXT` |
| 最小文字—图形前景净空 | 54.197 px | `TITLE_P3` ↔ `GFX_030`；门槛 >=3px |
| VISUAL_HARMONY_PASS | false | 字号硬门失败，不能以其他布局优点抵销 |
| MATH_SEMANTICS_PASS | true | 四面板依次表达单位圆 → `V^T` 旋转 → `Σ` 轴向缩放 → `U` 旋转；箭头/向量坐标与相邻正文一致 |
| TEXT_CONSISTENCY_PASS | true | 图内标题、说明、题注与 V4-C03 第 677--689 行正文一致 |
| GRAYSCALE_PASS | true | 线宽、箭头、位置和结构仍区分主向量/基方向/变换链 |
| PAGE_INTEGRATION_PASS | true | 整页没有图文挤压、裁切或异常空白 |

## 硬失败明细

1. 图默认文本在源文件第 3 行设为 `9.2pt`，四个面板标题在第 19 行设为 `9.4pt`，下方说明在第 48 行设为 `9.0pt`。这些均低于 `effective_pt >= 9.5pt`。对应 25 个标题字形和 22 个说明字形全部失败；`V^{\mathsf T}` 的自然上标还从已不合格的 9.4pt 基准派生，不能获得脚本级例外。
2. 原生 300 dpi 独立字形像素失败：`GLYPH_046`（说明中的“一”，CJK，`H_ink=4px <30px`）、`GLYPH_051`（图号 `26.1` 的 `.`，标点，`7px <22px`）、`GLYPH_067`（题注中的 `、`，标点，`10px <22px`）。详细值、bbox 和原因见 `after_pixel_measurements.csv`。
3. 不存在任何可以把上述失败降级为 PASS 的例外：源级字号不足、独立标点/字形像素不足都是明确硬门，故即使零重叠、零裁切、比例和数学语义通过也必须 FAIL。

## 四视图与像素复核

已在 1:1 原始像素中实际查看：

- `after_full_page_200dpi.png`
- `after_full_page_300dpi.png`
- `after_standalone_300dpi.png`（同一冻结 PDF 的无缩放单图裁图）
- `after_grayscale_300dpi.png`

文本测量叠加图为 `after_text_measurement_overlay_300dpi.png`；所有文本 bbox 映射至同一 300 dpi 坐标。`raw/`、`masks/`、`overlays/` 保留每个对象的原始 ROI、无膨胀 mask 和可追溯叠加图。`intentional_geometry_intersections.csv` 将轴、曲线、箭头头部等有意几何/数据组件接触与文字碰撞严格区分，未将其伪报为 TEXT 碰撞。

## SA2 定向修复要求

仅修改本图源。将所有面板标题、普通说明与其他读者可见图内文本提升到真实 `effective_pt >= 9.5pt`；标题和上标必须由合格的基准字号自然派生。必须通过重排、增宽、换行或拆分来吸收字号增量，禁止 `resizebox`、`scalebox` 或整体缩小规避。生成新的官方 PDF 后，重新从零生成全部 300 dpi 字形、比例、mask、pair、裁切与四视图证据，再创建新的独立 SA1。
