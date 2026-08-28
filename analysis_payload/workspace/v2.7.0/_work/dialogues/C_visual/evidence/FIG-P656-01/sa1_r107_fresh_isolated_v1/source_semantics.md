# Source semantics and object coverage

The current source was read without modification. Its visible semantics are:

1. Three ordered sequences: `1,1,1,2,3,3`; `1,3,1,2,1,3`; `3,1,2,1,3,1`.
2. Each sequence maps to the same count vector `n=(n1,n2,n3)=(3,1,2)`.
3. The support constraint is `n_k ∈ Z_{≥0}, sum_k n_k=N`.
4. The warning says the count vector is not a probability vector.
5. The coefficient card states that the number of sequences producing the same count is `N! / product_k n_k!`.
6. Two blue arrows encode the left-to-right compression/counting flow.
7. The caption explains ordered trials, count-vector compression, the multinomial coefficient, support constraints, and the count/probability distinction.

Source size coverage is complete in `after_font_audit.csv`: the TikZ base, every-node default, heading, sequence digits, count formula, arrow label, support formula, warning, coefficient label, and coefficient formula are all recorded. There is no `resizebox`, `scalebox`, `scale`, or `transform shape` chain. R168 makes the small source-size and taxonomy/peer metadata deviations advisory; every actual visible item remains sharp and readable, with no severe imbalance.

The PDF character stream yields exactly 90 visible figure-body glyph leaves (`G001`–`G090`). The visible PDF vector inventory yields exactly 25 drawing/path leaves (`D001`–`D025`): 18 sequence-node border/pattern composites, three rounded boxes, two arrow shafts, and two arrowheads. The displayed multinomial coefficient uses a slash, not a path-drawn fraction bar; the independent visible math-rule denominator is therefore zero. Caption glyphs are outside the figure-body leaf denominator and are reviewed separately in the figure-plus-caption and page-integration views.

Frozen denominator: `N = 90 + 25 + 0 = 115`; all unordered pairs: `C(115,2) = 6555`.
