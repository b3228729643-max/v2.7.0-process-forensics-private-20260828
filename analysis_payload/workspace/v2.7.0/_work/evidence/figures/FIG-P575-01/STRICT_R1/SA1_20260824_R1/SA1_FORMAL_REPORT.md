# FIG-P575-01 / 图31.3 — SA1 正式独立严格复核报告（R1）

RESULT: FAIL

FIGURE_ID: FIG-P575-01

CANONICAL_UID: FIG-P575-01

COVERAGE:

- 官方最终 PDF `main_full.pdf` 物理页 623（页内印刷页码 610）；独立题注/正文锚点定位。
- 图源 `fig_v5_c02_generalized_inverse.tex:3--54` 与相邻正文 `V5-C02.tex:276--305`。
- 31 个唯一语义文字 ELEMENT_ID、151 个逐 glyph/必要 substring trace、22 个图形语义对象，共 53 个最终可见图块对象；全部 1378 个无序 pair。

BLOCKERS:

1. 28/31 语义文字元素 source effective_pt < 9.50pt：刻度 8.50pt，标签/部分注释 9.20pt，右面板注释 9.00pt；不存在整体放大抵消。
2. 26/151 glyph trace 直接像素门 FAIL；141/151 为综合 source-font / pixel / D / E gate FAIL，二者已严格分列。
3. D 同面板同角色同 broad-script（非 exact glyph 分组）失败组 10；E 的可比 script/BASE 测量失败行 16，无 BASE 的行显式 N/A。
4. 文字-文字 PDF/vector bbox 净空 4px 门失败 4 对；最终可见 raw-mask overlap 为 0，不能把 bbox 净空失败误写成 overlap。

MATHEMATICAL_FINDINGS:

PASS — 连续面板 `Q(.65)=-ln(.35)/.65=1.615926`，图内 1.615 代入 `F=1-exp(-.65x)` 得 0.650040；离散阶梯质量 `(0.25,0.45,0.25,0.05)` 总和为 1，`Q(.70)=2`、`Q(.72)=3`。详见 `mathematical_recomputation.md`。

TEXT_CONSISTENCY:

PASS — 图内 `.70` 与题注 `0.7` 数值一致；“首次达到”与 `Q(u)=inf{x:F(x)>=u}`、正文 jump/flat 解释一致。

READING_ORDER:

PASS — 左连续投影 → 右离散跳跃的单向阅读路径清楚。

SOURCE_FONT_AUDIT:

FAIL — 语义元素表 `after_font_audit.csv`：31 行，28 FAIL；glyph trace 仅在 `after_pixel_measurements.csv`。

PIXEL_HEIGHT_AUDIT:

FAIL — pixel-height failed glyph = 26；所有 raw glyph masks 在 native 300dpi 1:1 网格、local-background delta >=20/255 下测量。

SAME_CLASS_RATIO_AUDIT:

FAIL — failed group = 10；`same_class_ratio_audit.csv` 的分组键固定为 panel + role + broad script class。

ROLE_RATIO_AUDIT:

FAIL — failed comparable-script row = 16；无可比 BASE 的 CJK/小写/数学标点明确 `N/A`。

OVERLAP_PIXEL_COUNT: 0

OVERLAP_PIXEL_AUDIT:

PASS for final-visible illegal overlap: 0 pixels / 0 pairs. 轴—刻度、曲线—点、导线—点的 24 个实际 final-visible 源级有意图形连接均在 pair 表标为 `INTENTIONAL_CONNECTION=true` / `PASS`，未计入非法重叠。

CLIP_PIXEL_COUNT: 0

MIN_TEXT_CLEARANCE_PX: 0.000

TEXT_TEXT_PDF_BBOX_MIN_PX: 0.000

TEXT_TEXT_RAW_INK_MIN_PX: 6.708

TEXT_TEXT_CLEARANCE_FAILURES:

- `PAIR_0171` T_P1_X_TICK_1 ↔ T_P1_ANNOT_Q065: `TEXT_TEXT_PDF_BBOX_CLEARANCE_FAILURE`; PDF/vector bbox=0.000px, raw ink=6.708px, intersection=0px.
- `PAIR_0406` T_P2_X_TICK_1 ↔ T_P2_ANNOT_Q070: `TEXT_TEXT_PDF_BBOX_CLEARANCE_FAILURE`; PDF/vector bbox=0.000px, raw ink=14.000px, intersection=0px.
- `PAIR_0533` T_P2_X_TICK_4 ↔ T_P2_ANNOT_Q072: `TEXT_TEXT_PDF_BBOX_CLEARANCE_FAILURE`; PDF/vector bbox=0.000px, raw ink=8.944px, intersection=0px.
- `PAIR_0977` T_P2_ANNOT_U070 ↔ T_P2_AXIS_FX: `TEXT_TEXT_PDF_BBOX_CLEARANCE_FAILURE`; PDF/vector bbox=3.000px, raw ink=14.000px, intersection=0px.

VISUAL_HARMONY:

FAIL — 数学、灰度、阅读顺序和页面融合可通过，但 source font、glyph pixel/D/E 和文字 bbox 净空硬门未通过；不得以“仍可读”覆盖。

GRAYSCALE:

PASS — 虚线/点划线与圆/方/三角在 `grayscale_300dpi.png` 中仍区分。

CAPTION:

PASS — 只陈述图的读图结论，且与正文严格一致。

PAGE_INTEGRATION:

PASS — `full_page_200dpi.png` 显示图、题注及后续 comparison box/节标题连续，无裁切或异常留白。

REQUIRED_FIXES:

- SA2 应提高所有刻度、轴标签与注释的有效字号到硬门以上，并调整 `Q(.65)`、`Q(.70)=2`、`Q(.72)=3` 与相邻 tick/`F(x)` 的坐标，使 PDF/vector bbox 净空达到至少 4px；不得整体缩小。
- SA2 后必须由新最终 PDF 重新生成全部 native 300dpi 证据，再由新的 SA1/SA3 复核。

EVIDENCE_USED:

- `render_manifest.json`, `full_page_200dpi.png`, `full_page_300dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `same_class_ratio_audit.csv`, `role_ratio_audit.csv`, `after_overlap_report.csv`, `edge_clearance_report.csv`
- `after_text_measurement_overlay_300dpi.png`, `after_glyph_measurement_overlay_300dpi.png`, `masks/`, `glyph_evidence/`, `pair_evidence/`, `machine_terminal_check.*`
