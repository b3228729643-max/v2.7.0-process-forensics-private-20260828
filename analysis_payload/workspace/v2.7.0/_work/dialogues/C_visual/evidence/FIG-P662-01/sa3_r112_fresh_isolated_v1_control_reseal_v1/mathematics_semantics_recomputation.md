# Independent mathematics and semantics recomputation

Reviewer identity: `C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-V1`

## Frozen displayed claims

The current source and frozen R112 pixels display the following claims:

1. Independent variables `Y_i ~ Gamma(alpha_i, lambda)` share one rate `lambda`.
2. `S = sum_{k=1}^K Y_k`.
3. `Theta_k = Y_k/S`, hence `sum_k Theta_k = 1`.
4. `Theta ~ Dir(alpha)`.
5. `S ~ Gamma(alpha_0, lambda)` and `S` is independent of `Theta`, where `alpha_0 = sum_i alpha_i` in the current chapter context.
6. For `K=2`, `Theta_1 ~ Beta(alpha_1, alpha_2)`.
7. The construction supplies a reproducible Dirichlet sampling route when the independent Gamma draws are reproducibly generated.

## Re-derivation from current whitelisted inputs

Assume `K >= 2`, every `alpha_i > 0`, `lambda > 0`, and the `Y_i` are mutually independent with the source's shape--rate convention. Their joint density is

`f_Y(y) = lambda^(alpha_0) / prod_i Gamma(alpha_i) * prod_i y_i^(alpha_i-1) * exp(-lambda * sum_i y_i)`

on the positive orthant, with `alpha_0 = sum_i alpha_i`. Set `s=sum_i y_i`, `theta_i=y_i/s` for `i<K`, and `theta_K=1-sum_{i<K} theta_i`. The inverse map is `y_i=s theta_i`, and the Jacobian absolute value is `s^(K-1)`. Substitution gives

`f_{S,Theta}(s,theta)`

`= [lambda^(alpha_0)/Gamma(alpha_0) * s^(alpha_0-1) exp(-lambda s)]`

`  * [Gamma(alpha_0)/prod_i Gamma(alpha_i) * prod_i theta_i^(alpha_i-1)]`.

The first bracket is the `Gamma(alpha_0,lambda)` density and the second is the `Dir(alpha)` density. Because the transformed joint density factors into a function of `s` times a function of `theta`, `S` and `Theta` are independent. This independently confirms claims 4 and 5.

Claim 3 follows algebraically:

`sum_k Theta_k = sum_k(Y_k/S) = (sum_k Y_k)/S = S/S = 1`,

and positivity of the Gamma draws makes every component positive. Thus the displayed triangle/point cue correctly represents membership in the simplex interior.

When `K=2`, `Theta_2=1-Theta_1`, and the Dirichlet density reduces to a one-dimensional density proportional to

`theta_1^(alpha_1-1) (1-theta_1)^(alpha_2-1)`,

with normalizer `B(alpha_1,alpha_2)`. Therefore `Theta_1 ~ Beta(alpha_1,alpha_2)`, confirming claim 6.

For a deterministic interface check using only the current chapter's example values `(2,3,5)`, `S=10` and `Theta=(1/5,3/10,1/2)`; the components are positive and sum to one. This checks the displayed sum/divide mechanics without using it as a probabilistic proof.

The source uses `Y_i,lambda` in the figure while the adjacent theorem uses `G_i,b`. Both are locally declared names for the same independent shape--rate Gamma construction. The renaming changes no mathematical object or parameterization. Common rate is essential: unequal rates would produce `exp(-s sum_i lambda_i theta_i)`, which does not factor.

## Semantic and reading-order adjudication

The visible route is single-directional: independent Gamma inputs -> total `S` -> divide every input by `S` -> probability vector `Theta` -> Dirichlet result. The dashed paths then explain the derived independence statement, and the gold lower-right node gives the `K=2` specialization. The simplex glyph reinforces the constraint rather than adding a contradictory claim. Caption, alt text, source, and adjacent chapter context all state the same construction.

Mathematical conclusion: no wrong direction, index, distribution, rate convention, normalization, independence statement, special case, or simplex relation was found.
