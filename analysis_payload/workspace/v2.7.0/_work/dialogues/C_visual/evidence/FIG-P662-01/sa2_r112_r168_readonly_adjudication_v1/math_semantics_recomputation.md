# Independent Gamma-normalization semantics recomputation

Let the visible inputs satisfy

`Y_i ~ Gamma(alpha_i, lambda)`, independently for `i=1,...,K`,

with common shape–rate convention and `lambda>0`. Put `S=sum_i Y_i` and `Theta_i=Y_i/S`. For `i<K`, use `Y_i=S Theta_i` and `Y_K=S(1-sum_{i<K}Theta_i)`. The Jacobian absolute value is `S^(K-1)`. With `alpha_0=sum_i alpha_i`, the joint density becomes

`[lambda^alpha_0 / Gamma(alpha_0)] S^(alpha_0-1) exp(-lambda S)`

times

`[Gamma(alpha_0)/prod_i Gamma(alpha_i)] prod_i Theta_i^(alpha_i-1)`.

The first factor is `Gamma(alpha_0,lambda)` in the chapter's shape–rate parameterization; the second is `Dir(alpha)` on the simplex. The factorization proves both `S ⟂⟂ Theta` and the displayed marginal laws. Since each input is positive, `Theta_i>0` and `sum_i Theta_i=1`. When `K=2`, `Theta_2=1-Theta_1` and `Theta_1 ~ Beta(alpha_1,alpha_2)`.

The figure uses `Y` where the nearby theorem uses `G`; this is a harmless local variable rename because every formula and the current caption are internally consistent. Common rate `lambda`, not merely arbitrary rates, is explicitly shown on every input and repeated in the note. The left-to-right flow—independent Gamma inputs, total, division by the same total, normalized proportions, Dirichlet result—correctly realizes the sampling construction. The two dashed paths correctly identify that both `S` and `Theta` feed the independence statement.

Math/semantic decision: no wrong parameterization, wrong codepoint, missing condition, reversed implication, invalid independence claim, or geometric/reading-order error.
