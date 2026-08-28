# Independent mathematics, semantics, and reading-order recomputation

## Recomputed mathematics

Let `Y_k` be independent Gamma variables with shape `alpha_k > 0` and common rate `lambda > 0`. Put

`alpha_0 = sum_k alpha_k`, `S = sum_k Y_k`, and `Theta_k = Y_k / S`.

Using `Y_k = S Theta_k`, `Theta_K = 1 - sum_{k<K} Theta_k`, the transformation domain is `S > 0` and `Theta` in the open `(K-1)`-simplex. Its absolute Jacobian is `S^(K-1)`. Therefore the transformed joint density is

`[lambda^alpha_0 / Gamma(alpha_0)] S^(alpha_0-1) exp(-lambda S)`

times

`[Gamma(alpha_0) / product_k Gamma(alpha_k)] product_k Theta_k^(alpha_k-1)`.

The first factor is the `Gamma(alpha_0, lambda)` density and the second is the `Dir(alpha)` density. Their factorization proves

- `S ~ Gamma(alpha_0, lambda)`;
- `Theta ~ Dir(alpha)`;
- `S` is independent of `Theta`;
- `sum_k Theta_k = 1` follows identically from normalization;
- for `K=2`, `Theta_1 ~ Beta(alpha_1, alpha_2)`.

The common **rate** is essential: unequal rates produce `exp[-S sum_k lambda_k Theta_k]`, which does not separate. Every displayed formula, direction, and special-case statement is therefore mathematically correct.

## Semantic and reading-order adjudication

The intended reading order is unambiguous and matches the source/caption:

1. read the independent common-rate Gamma inputs vertically (`Y_1`, `Y_2`, ellipsis, `Y_K`);
2. follow the three fan-in arrows to the total `S`;
3. divide each component by `S`;
4. read the normalized proportions `Theta_k = Y_k/S`;
5. follow the final arrow to the Dirichlet vector and simplex constraint;
6. read the dashed consequences below: independence of total and proportions, and the `K=2` Beta special case;
7. read the caption, which states the same construction and sampling interpretation.

The numbered badges reinforce stages 1-3 without replacing the arrows. The simplex icon sits above the Dirichlet result and its note is adjacent without covering the result. Dashed paths are visually subordinate and do not imply the wrong main direction. Source, rendered labels, page lead-in, and caption agree on Gamma shape/rate notation, normalization, independence, Dirichlet output, and Beta specialization. No missing glyph, tofu, wrong codepoint, wrong formula, reversed arrow, false implication, or reading-order ambiguity is present.
