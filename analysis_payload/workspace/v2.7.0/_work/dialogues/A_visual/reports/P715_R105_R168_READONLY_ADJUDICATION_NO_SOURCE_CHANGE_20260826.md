# FIG-P715-01 R105 R168 read-only adjudication

Formal verdict: `P715_R168_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

## Current candidate and source

- Official candidate: R105.
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf`.
- PDF identity supplied by the official freeze: 817 A4 pages, 4,967,209 bytes, SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`.
- Current location independently found from current source and R105 text: physical page 765, printed page 752, Figure 36.2.
- Page 765: A4, 595.276 × 841.89 pt, rotation 0, PDF 1.7, unencrypted.
- Current source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex`.
- Source SHA-256: `51B21C62DE42564CB4B915C51F7A213F36D8784475CD15A92474497D2F6EED2F`.
- Active Goal query returned null; this review therefore used the explicit main-thread R168 instruction plus the current strict protocol/schema.

No old P715 evidence, role report, handoff, state, inventory, or prior conclusion was used as evidence.

## Direct current observations

The following views were rendered directly from R105 and actually opened:

- full physical page 765 at native 300 dpi: 2481 × 3508 px;
- color figure crop at native 300 dpi: 2010 × 1040 px;
- grayscale figure crop at native 300 dpi: 2010 × 1040 px;
- native-bbox 8× nearest-neighbour view of the formerly threshold-sensitive terminal CJK `一` in the left-panel title.

The two panels, graph nodes and arrows, matrices, formulas, highlights, caption, surrounding definition, and page hierarchy are all readable. There is no tofu, wrong codepoint, substituted symbol, broken stroke, real clipping, illegal overlap, or visibly severe size imbalance. Grayscale preserves the graph/matrix reading order and the orange focus boxes remain distinguishable by border geometry.

## R168 adjudication of the old 6 px CJK item

The terminal CJK `一` in `网页图、邻接矩阵与列归一` has a final visible native-300-dpi glyph bbox around full-page pixels `(986,296)-(1029,358)`. Its thresholded ink is approximately 40 px wide and 6 px high. The low height is the intrinsic single-horizontal-stroke topology of U+4E00, not a missing component or raster truncation.

The native and nearest-neighbour views show a continuous horizontal stroke, intact antialiasing at both ends, correct dark-blue title color, no neighboring-object contamination, and no clipping. The word `归一` is immediately legible in its title context. Under R168, an absolute pixel-height or peer-ratio micro-failure that remains visually clear cannot alone trigger source repair or FAIL_TO_SA2. This item is therefore `ADVISORY_ONLY`, not a hard defect.

Other low-profile CJK strokes and fine role/peer ratio differences are likewise visually clear and harmonized. No same-class item shows tofu, wrong semantics, actual unreadability, or a conspicuous size discontinuity.

## Source-level role check

- Base/every-node: 9.5 pt.
- Panel titles: 10.4 pt bold.
- Circular page nodes: 10.2 pt bold.
- Edge notes: 9.5 pt.
- Formula blocks: 12 pt.
- Matrix cells: 10.2 pt.
- Gray explanatory notes: 9.5 pt.
- `resizebox`, `scalebox`, `transform shape`, and accumulated graphics scaling: absent.

The hierarchy is intentional and visually coherent: titles are mildly larger/bold, formulas receive emphasis, matrix cells match node labels, and explanatory notes remain secondary but readable. R168 advisory micro-ratios do not reveal any visually obvious imbalance.

## Semantic and geometry check

- Directed edges are exactly `i→j`, `j→i`, `j→h`, `h→i`.
- Column out-degrees are `(1,2,1)`.
- Displayed `A`, column-normalized `M`, and `P=M^T` are mutually consistent.
- `1^T M=1^T`, `P1=1`, column-vector and row-vector updates, and the caption agree with the adjacent current text.
- Node text has ample border clearance; arrows and labels remain separated; panel borders do not clip content; matrices and focus boxes do not obscure digits or fractions.
- Full-page integration and caption spacing are clean.

## Route

No R168 real hard defect remains. P715 does not require an SA2 source patch, TeX build, or source-scope grant. Route it without source change to a completely fresh isolated R105 SA1 after main-thread acceptance. No fresh role is started here.
