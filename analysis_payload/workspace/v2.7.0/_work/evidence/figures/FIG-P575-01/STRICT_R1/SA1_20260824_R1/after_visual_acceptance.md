# FIG-P575-01 SA1 严格视觉验收（R1）

RESULT: FAIL

## 固定输入定位

- 仅审计官方 R94 `main_full.pdf` 物理页 623（PDF 内页码 610）。
- 独立定位链：前页正文锚点“图31.3把严格递增与离散跳跃放在同一‘首次达到’规则下” → 本页图题注“图31.3 广义逆采用首次达到规则…”。
- 原生网格：2481 × 3508 px @ 300 dpi；页面 595.276 × 841.890 PDF pt。
- 图块裁图为整页原生 300 dpi 的整数像素裁切；未 resize。具体整数坐标见 `render_manifest.json`。

## 9.2.1 / 严格 schema 判定

SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
OVERLAP_FAIL_PAIR_COUNT = 0
CLEARANCE_FAIL_PAIR_COUNT = 4
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.000
MIN_TEXT_TEXT_PDF_BBOX_CLEARANCE_PX = 0.000
MIN_TEXT_RAW_INK_CLEARANCE_PX = 6.708
FONT_VISUAL_HARMONY_PASS = false
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## 可复核的失败原因

1. 图源 line 14 将所有刻度声明为 8.50pt；lines 5/15/24--27 为 9.20pt；lines 41--50 为 9.00pt。图由 V5-C02.tex:302 直接 `\input`，没有可抵消的放大，故这些读者可见元素的 effective_pt 仍低于 9.50pt 硬门。
2. `after_font_audit.csv` 只计 31 个唯一语义文字 ELEMENT_ID（其中 28 个源字号 FAIL）；`after_pixel_measurements.csv` 是 151 个逐 glyph/必要 substring trace，其中 **pixel-height failed = 26**，而综合字号/像素/D/E gate failed = 141（D 失败组 10，E 失败行 16）。不得把 glyph trace 冒充语义元素，也不得把综合 FAIL 误报为像素高度 FAIL。关键数学标点/运算符单独建 mask；对应 raw masks、1:1 overlay 和 8× nearest 核像素证据见 `glyph_evidence/`。
3. 同面板、同角色、同 broad-script D 组中有 10 组失败；未按 exact glyph 拆组。E 仅在有同脚本 BASE 时计算；CJK/小写/数学标点没有可比 numeric BASE 时均明确标为 N/A，而不是借用不相同脚本的字号。

空间 mask 计数使用最终可见前景（native PDF 300 dpi，局部背景差 >=20/255）。无真实文字 halo/白底/双边框：因此不存在可用于删减的 pre/halo/final 三态；普通白纸和节点/marker fill 未当作 halo。节点边框对象数为 0，`TEXT_NODE_BORDER` 关系显式 N/A；其余全部无序对象 pair 已枚举。

## 视觉结论

数学、题注/正文一致、阅读顺序、灰度编码和整页融合均可通过；但“能读”不能覆盖 9.2.1 字号、逐 glyph 像素和比例硬门。本图必须交 SA2 定向修复（提高刻度/标签/注释的有效字号，并在新最终 PDF 上重新全量取证）。
