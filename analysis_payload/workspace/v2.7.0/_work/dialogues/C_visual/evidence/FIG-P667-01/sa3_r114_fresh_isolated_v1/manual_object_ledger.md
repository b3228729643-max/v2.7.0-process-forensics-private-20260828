# Frozen reader-visible object ledger — post-observation SA3

The denominator is frozen at 24 objects: 17 text objects (`T01`–`T17`) and 7 graphic objects (`G01`–`G07`). This ledger was authored only after every decisive view listed in `manual_view_log.md` had been opened. Machine bboxes, ink counts, source lines and codepoints remain in the corresponding machine CSV files; the findings below are manual visual/semantic observations.

| ID | Manual post-observation finding |
|---|---|
| G01 | Prior strip border is complete, gently rounded and visibly distinct from white without competing with the formula; it encloses T02/T03 with ample outer padding and has no clipped edge. |
| G02 | Likelihood strip border matches G01 in width, height, weight and corner treatment; its interior remains clean around T06/T07. |
| G03 | Posterior strip border matches G01/G02 and terminates cleanly where the main arrow begins; the designed endpoint relation to G05 is not a foreground collision. |
| G04 | The brace spans exactly the prior and likelihood strips, has a clear midpoint cusp and remains separate from T08; it encodes the two inputs being combined. |
| G05 | The solid blue arrow runs left-to-right from posterior kernel toward the posterior distribution box, stays clear of every text object and has a crisp readable head. |
| G06 | The posterior-result box is complete, balanced, lightly filled and contains T12/T13 without border contact; the bottom center is the deliberate anchor for G07. |
| G07 | The dashed gray branch is continuous at native 300 dpi, points downward to T14, and its three shared pixels with G06 form the legal source-defined connector-to-border junction rather than an illegal collision. |
| T01 | “先验核” is complete, bold, readable and aligned with the first strip; no missing strokes, tofu, overlap or clipping. |
| T02 | The prior kernel visibly reads as `p(θ|α)∝∏ᵢθᵢ^(αᵢ−1)`; α, θ, product limits, exponent, minus sign and underbrace are distinguishable at native 1× and 8×. |
| T03 | “先验指数” is readable below its underbrace. The nearest formula ink remains distinct; no stroke crossing or mistaken codepoint is visible. |
| T04 | The gold multiplication sign is centered between the first two strips, visually salient but not dominant, and isolated from borders/text. |
| T05 | “似然核” matches T01/T09 in weight and alignment; all strokes are intact and readable. |
| T06 | The likelihood kernel visibly reads as `p(n|θ)∝∏ᵢθᵢ^nᵢ`; both occurrences of subscript `i`, the exponent `nᵢ`, θ and the conditional bar are visually distinct. |
| T07 | “计数” is readable beneath the exponent underbrace. The machine three-pixel T06/T07 intersection is not a glyph–glyph intersection: the PDF vector bboxes have a positive 0.165 pt vertical gap, and the native/8× overlay shows bbox/antialias attribution around the neighboring subscript. |
| T08 | “指数逐分量相加” is fully readable in blue, horizontally separated from G04, and correctly explains the brace. |
| T09 | “后验核” matches T01/T05 in weight, size and alignment; no anomaly is visible. |
| T10 | The posterior kernel visibly reads as `p(θ|n,α)∝∏ᵢθᵢ^(αᵢ+nᵢ−1)`; the additive exponent, subscripts, minus sign and underbrace are all recoverable without ambiguity. |
| T11 | “逐分量相加” remains readable directly below the posterior exponent underbrace. The tight stack is a single mathematical annotation construct and shows no actual crossing, clipping or misreading in the opened native and 8× views. |
| T12 | The first result line `θ|n` is centered, complete and separated from T13; θ, conditional bar and bold `n` render correctly. |
| T13 | The second result line `∼Dir(α+n)` is complete, centered and readable; the tilde, Dir, parentheses, α, plus and n codepoints render correctly. |
| T14 | The marginal formula is fully visible: both fraction bars, factorials, product/subscripts and Beta ratio are intact; the dashed arrowhead stops above it and no line passes through text. |
| T15 | “保留归一化常数” is centered below T14 with visible separation; it neither touches the formula nor the caption. |
| T16 | Caption label “图 34.7” is bold, complete and clearly separated from the caption sentence; no wrong digit or missing glyph. |
| T17 | The complete two-line caption is readable in the page and native crop. Chinese, `Dirichlet–`, `log θᵢ`, α+n and punctuation render without tofu/replacement characters; the wording agrees with the figure and current prose. |

Denominator finding: all 24 IDs are present once, visually attributable, uncut and semantically necessary. No additional reader-visible text, foreground line, arrow, border or caption object occurs inside the frozen crop.
