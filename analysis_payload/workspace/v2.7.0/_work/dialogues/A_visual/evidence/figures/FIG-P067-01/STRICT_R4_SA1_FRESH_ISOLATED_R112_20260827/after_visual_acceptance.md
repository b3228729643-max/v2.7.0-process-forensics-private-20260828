# FIG-P067-01 R112 fresh isolated SA1 visual acceptance

- `HANDOFF_ID`: `A-R112-P067-SA1-FRESH-ISOLATED-20260827`
- reviewer role: fresh isolated SA1 only
- official PDF: `main_full.pdf`, 4,967,100 bytes, SHA-256 `D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2`
- current single source: `fig_v1_c04_cdf.tex`, 4,015 bytes, SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`
- independently localized physical page: 69; printed page: 56; exact caption: `图 4.1 离散随机变量的分布函数：跳跃高度等于对应点的概率质量`
- page size: 595.276 pt × 841.890 pt; native 300 dpi grid: 2481 × 3508 px
- figure crop: page pt `[100,62,489,221]`; integer 300 dpi page pixels `[416,258,2038,921]`; native crop 1622 × 663 px
- standalone crop: page pt `[100,62,489,201]`; integer 300 dpi page pixels `[416,258,2038,838]`; native crop 1622 × 580 px

## Frozen denominator

- visible objects: 150 = 95 `CHAR` + 50 foreground `GRAPHIC` + 5 opaque `BACKGROUND`
- complete unordered-pair denominator: 11,175 = 150 × 149 / 2
- empty masks: 0
- figure-crop edge clip pixels: 0
- 12 critical/near pairs received raw 1×, raw nearest8×, A mask, B mask, intersection, overlay 1×, and overlay nearest8× evidence
- manual object ledger: 150/150 unique IDs; manual critical-pair ledger: 12/12

## Probability and mathematical semantics

- PMF masses are 0.15, 0.30, 0.35, and 0.20; all are nonnegative and sum exactly to 1.
- CDF post-jump levels are 0.15, 0.45, 0.80, and 1.00. Their successive increments are exactly the four PMF masses.
- The CDF is monotone nondecreasing, terminates at 1, and shows right continuity with filled markers on post-jump values and open markers on pre-jump values.
- Top and bottom panels share support points 1, 2, 3, and 4, so every PMF stem matches one CDF jump.
- Axis labels `F_X(t)`, `p_X(t)`, and `t`, tick values, in-figure annotations, and caption agree with the plotted quantities.

## Human visual findings

- The native color crop, standalone crop, grayscale crop, 200 dpi page, 300 dpi page, whole-figure nearest8×, all eight glyph contact sheets, the ID overlay, and all 12 critical raw/overlay ROIs were actually opened.
- No glyph is missing, replaced by tofu, or incorrectly encoded. No mathematical label is actually unreadable.
- No object is truly clipped. No reader-visible illegal overlap remains. All six machine hard candidates are false positives caused by formula-internal layout or raw bbox/paint-order attribution:
  - `PAIR-01585`: `p_2` base/subscript, same formula parent;
  - `PAIR-02220` and `PAIR-02245`: `p_4` versus the top guide/step, raw view visibly separates the glyph ink;
  - `PAIR-02876`: t=1 guide lies in whitespace beside the colon dots;
  - `PAIR-03795`: `F_X` is normal TeX subscript composition;
  - `PAIR-06688`: t=4 guide is occluded by the note background before text paint.
- Grayscale retains clear separation between guides, CDF steps, open/filled jump markers, PMF stems, and text.
- Page fusion is balanced: the figure sits naturally below the running header, caption spacing is even, and the following explanatory paragraph begins cleanly.

## R168 advisory mouth

Nine source declarations are below the older 9.5 pt numeric line: 9.2 pt twice, 8.8 pt twice, 9.4 pt three times, and 8.6 pt twice. Several low-profile punctuation or natural-script pixel heights are also below older micro-raster thresholds. Under the explicitly assigned R168 mouth these are advisory because the actual native and page views are readable, balanced, complete, and semantically correct. They are not hard failures.

Six manual mask-purity rows are `false` (`CHAR-0016`, `CHAR-0021`, `CHAR-0055`, `GRAPHIC-0011`, `GRAPHIC-0012`, `GRAPHIC-0033`) because a tight PDF bbox contains pixels from an earlier/later line or occlusion object. The matching raw nearest8× evidence was opened and shows no reader-visible collision or missing glyph stroke. These rows are retained rather than machine-cleaned so the evidence exposes the attribution limitation.

## Final SA1 decision

- `FONT_VISUAL_HARMONY_PASS=true`
- `SEMANTIC_PASS=true`
- `CAPTION_AND_PAGE_FUSION_PASS=true`
- `ACTUAL_ILLEGAL_OVERLAP_PIXEL_COUNT=0`
- `ACTUAL_CLIP_PIXEL_COUNT=0`
- `FINAL_DECISION=PASS_R168`

This is one fresh isolated SA1 decision only. It does not count as `A_LOCAL_PASS` and does not authorize any central-state write. The next allowed action is for the main line to dispatch a different fresh isolated SA3.
