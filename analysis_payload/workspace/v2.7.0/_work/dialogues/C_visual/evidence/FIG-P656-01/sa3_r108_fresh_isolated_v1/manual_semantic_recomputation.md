# FIG-P656-01 independent semantic recomputation

Reviewer identity: `/root/sa3_fig_p656_r108_fresh_isolated_v1`, `gpt-5.6-sol`, `xhigh`.

This record was written after opening the native 300 dpi page, figure, grayscale, overlay, independent masks, and native/8x critical ROIs. It does not reuse any other reviewer conclusion.

## Three displayed sequences

1. Row 1 is `(1, 1, 1, 2, 3, 3)`. Direct tally gives `n_1=3`, `n_2=1`, `n_3=2`.
2. Row 2 is `(1, 3, 1, 2, 1, 3)`. Direct tally again gives `n_1=3`, `n_2=1`, `n_3=2`.
3. Row 3 is `(3, 1, 2, 1, 3, 1)`. Direct tally again gives `n_1=3`, `n_2=1`, `n_3=2`.

Each row has six trials, so `N=6`. The displayed count vector

`n=(n_1,n_2,n_3)=(3,1,2)`

is therefore correct for all three sequences, and `3+1+2=6=N`.

## Multinomial coefficient

For this count vector,

`N!/(n_1! n_2! n_3!) = 6!/(3! 1! 2!) = 720/(6*1*2) = 60`.

Thus exactly 60 distinct ordered category sequences produce the same count vector. The coefficient box shows the correct general formula `N!/prod_k n_k!`; it is not required to print the evaluated value 60 for the relation to be correct.

## Support and warning

The support line `n_k in Z_{>=0}, sum_k n_k=N` is correct: counts are nonnegative integers constrained by the total number of trials. In the adjacent chapter definition this is the support `C_{N,K}={n in N_0^K: sum_i n_i=N}`.

The warning `count vector, not probability vector` is mathematically necessary. Here the entries sum to 6 rather than 1; `n` is a random count vector, whereas the category-probability parameter is `theta in Delta_{K-1}`.

## Arrow and box semantics

- The first arrow maps each ordered sequence to its count vector and is labelled `same count`; all three displayed rows verify that label.
- The second arrow maps the count vector to the number of orderings that realize it. This matches the adjacent text: an ordered-sequence likelihood is `prod_t theta_{y_t}`, while the probability of the compressed count vector reintroduces the multinomial coefficient.
- Both arrows are left-to-right and use source anchors `count.west`, `count.east`, and `coef.west`. Small raster tip/tail gaps are legal attachment rendering and do not change the relationship.

## Caption and page context

The caption states four linked facts: ordered trials are compressed to counts; the multinomial coefficient counts orderings; support requires nonnegative integers summing to `N`; and counts must not be confused with probabilities. All four agree with the figure, equations (34.1)-(34.2), and the surrounding chapter definition. No wrong symbol, direction, count, coefficient, support condition, or semantic role was found.

Manual semantic result: `CLEAR`.
