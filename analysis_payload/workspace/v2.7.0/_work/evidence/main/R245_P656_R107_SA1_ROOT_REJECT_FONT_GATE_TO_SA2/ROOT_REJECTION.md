# R245 P656 R107 SA1 root rejection: source font gate

- Time: `2026-08-26T17:06:30+08:00`
- UID: `FIG-P656-01`; candidate R107; source SHA-256 `BC954A32F6FC8811F9557AD9A3147795CB6CB467DEAEF6195A3A0B1D9E855852`.
- Submitted handoff ID: `C-FIG-P656-01-R107-SA1-FRESH-ISOLATED-V1`.

## What passed

The sealed evidence independently locates Figure 34.2 on physical page 705 / printed page 692. Its frozen denominator is 90 glyph + 25 drawing = `N=115`; all `C(115,2)=6,555` pairs and 34 critical relations are present. The three nonzero raw intersections total 97 pixels and are design connections: the count-box border to the second arrow shaft start, and two shaft-to-arrowhead joins. Illegal overlap, clipping, empty masks and mask contamination are all zero. Full page, figure crop, grayscale, standalone, text overlay, drawing overlay, all six glyph sheets and all six critical sheets show readable and semantically correct content: ordered sequences map to `(3,1,2)`, the nonnegative-integer/sum constraint is correct, the multiplicity is `N!/prod_k n_k!`, and the warning correctly says the count vector is not a probability vector.

The root has 408 ordinary files. Its 406-row manifest excludes only itself and `WRITE_STOPPED`; manifest-to-filesystem path/bytes/SHA mismatch and duplicates are zero. All 408 files are read-only, ADS count is zero, and `WRITE_STOPPED` is strictly latest.

## Decisive rejection

The active Goal and both strict protocol/schema require general visible text and base formulas to satisfy `effective_pt >= 9.5pt`; R168 makes minor raster/contour/ratio differences advisory but does not waive this explicit source-level minimum.

The current source declares 9.2pt globally, 9.4pt for nodes, 8.8pt for the arrow label, and 9.2pt for the constraint/warning. The final glyph inventory has 90 rows: 4 at 8.8pt, 24 at 9.2pt, 56 at 9.4pt and only 6 at 9.9pt. Therefore 84/90 visible glyphs fail the source font gate. This is a real protocol failure independent of pixel micro-differences.

In addition, the glyph/drawing/view/hard-gate manual ledgers predate the last regeneration of their referenced machine images; only the critical ledger was refreshed and reconciles to the final relation table. This timing gap cannot rescue the font failure.

Decision: `ROOT_REJECT_SA1_PASS / FAIL_TO_SA2_SOURCE_FONT_GATE`. SA3 is forbidden. The sealed root remains immutable.

## Authorized next action

C is the sole current business source writer for `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_multinomial_counts.tex`. It may only raise all general visible declarations below 9.5pt to at least 9.5pt, preferably a uniform 9.5pt with natural line spacing. Text, formulas, coordinates, node sizes, edges, colors, caption and semantics must not change; scale/resize/transform are forbidden. C must freeze an exact static diff, source identity and geometry-risk account, then request the one TeX slot. No TeX, commit, fresh role or second UID is authorized yet.

P656 moves `SA1 → SA2`. Inventory becomes `32 SA1 / 51 SA2 / 0 SA3 / 16 A_LOCAL_PASS`; strict final remains `0/99`.
