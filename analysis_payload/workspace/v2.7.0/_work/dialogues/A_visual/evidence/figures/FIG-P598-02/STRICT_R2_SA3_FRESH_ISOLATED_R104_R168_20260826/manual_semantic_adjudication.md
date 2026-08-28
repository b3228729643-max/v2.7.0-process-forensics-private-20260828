# FIG-P598-02 SA3 manual semantic adjudication

- Reviewer: `SA3-FRESH-ISOLATED`
- Frozen candidate: R104 physical page 650
- Observation basis: native 300 dpi whole page, figure-plus-caption crop, figure-only crop, grayscale crop, all 19 object contact sheets, both matrices, and all 16 critical overlays.

## Ordered structure

1. Card 1 is headed `1 构造核`, contains `πK=π`, distinct `x` and `y` circular states, and two opposed arrowed transitions. The lower note reads `保持目标分布 π`.
2. Card 2 is headed `2 运行链`, contains a continuous chain curve, a hatched warm-up region, a dashed divider, a baseline, and the labels `warm-up` and `保留段`.
3. Card 3 is headed `3 遍历平均`, contains seven retained-sample dots and the complete estimator `\widehat I_{m,n}=\frac1n\sum_{t=m+1}^{m+n}h(X_t)`. The lower note reads `只用保留样本`.
4. Exactly two rightward flow arrows connect card 1→2 and card 2→3. Both are continuous at their endpoints and preserve the intended reading order.

## Caption and mathematical meaning

The caption states that the three arrow-ordered steps construct a transition kernel having `π` as stationary distribution, run the chain and discard warm-up, then estimate `E_π[h(X)]` from retained samples. This agrees with all three cards and with the displayed estimator. The widehat, fraction rule, summation limits, subscripts, brackets, and all operator codepoints are visibly correct.

## R168 font gate

No missing glyph, tofu, wrong codepoint, wrong mathematical meaning, genuinely unreadable object, severe visible imbalance, or real clipping/overlap was observed. The 9.2/9.4/8.6 pt source declarations, legacy taxonomy ratios, and 1–2 px fine differences are retained in the machine tables as R168 advisory data only. The visual hierarchy is deliberate: blue bold headings lead, black formulas carry the mathematical content, and gray notes remain readable without competing with the formulas.

`FONT_VISUAL_HARMONY_PASS=true`

## Geometry, grayscale, and page integration

All 163 final-visible object masks are nonempty and pure. The 13,203 unordered pairs have zero shared native pixels. Hard text/text, text/border, text/line-arrow-marker, crop-edge, and clipping gates pass. Intended zero-clearance joins are limited to arrow/card, arrow/node, widehat/I, and composed plot crossings; each was inspected in its dedicated 1×/8× overlay. Grayscale keeps the curve, hatch, divider, dots, headings, notes, formula, and caption distinguishable. On the full page the figure sits naturally below the running header, the caption has clear separation, and the following body begins with comfortable whitespace.

`SEMANTICS_PASS=true`

`GEOMETRY_PASS=true`

`GRAYSCALE_PASS=true`

`PAGE_INTEGRATION_PASS=true`
