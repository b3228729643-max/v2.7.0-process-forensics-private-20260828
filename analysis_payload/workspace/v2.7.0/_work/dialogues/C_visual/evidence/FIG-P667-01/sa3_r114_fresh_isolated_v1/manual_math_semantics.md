# Independent mathematics, semantics and context recomputation

## Assumptions and kernels

For `α_i>0`, counts `n_i≥0`, and `N=Σ_i n_i`, the Dirichlet prior and multinomial likelihood are

\[
p(\boldsymbol\theta\mid\boldsymbol\alpha)
=\frac{1}{B(\boldsymbol\alpha)}\prod_i\theta_i^{\alpha_i-1},
\qquad
p(\boldsymbol n\mid\boldsymbol\theta)
=\frac{N!}{\prod_i n_i!}\prod_i\theta_i^{n_i}.
\]

Dropping only factors independent of `θ`, their product has kernel

\[
\prod_i\theta_i^{\alpha_i-1}\prod_i\theta_i^{n_i}
=\prod_i\theta_i^{\alpha_i+n_i-1}.
\]

Because every `α_i+n_i>0`, normalization on the simplex gives

\[
\boldsymbol\Theta\mid\boldsymbol n,\boldsymbol\alpha
\sim \operatorname{Dir}(\boldsymbol\alpha+\boldsymbol n).
\]

Keeping the multinomial and Dirichlet normalization constants and integrating over the simplex gives

\[
p(\boldsymbol n\mid\boldsymbol\alpha)
=\frac{N!}{\prod_i n_i!}
\frac{B(\boldsymbol\alpha+\boldsymbol n)}{B(\boldsymbol\alpha)}.
\]

Thus every displayed mathematical statement in T02, T06, T10, T12–T14 is correct. The phrase “同一组 `log θ_i` 充分统计量” is also correct: taking logs turns the three kernels into coefficient-weighted sums of the same `log θ_i`, and multiplication adds the coefficients componentwise.

## Flow and geometry semantics

- T04 communicates multiplication of the prior and likelihood kernels.
- G04/T08 groups those two inputs and states that their exponents add componentwise.
- The third strip is already the resulting posterior kernel; G05 then maps it to the normalized posterior distribution T12/T13.
- G07 is visually secondary (gray dashed) and leads to the optional marginal-evidence formula T14/T15. Its wording “保留归一化常数” prevents the branch from being mistaken for an additional posterior update.
- Color is not the only encoding: solid versus dashed arrows, box geometry, vertical ordering and the brace all survive grayscale.

No arrow is reversed, no result is attached to the wrong source object, and no geometry suggests addition of probability vectors.

## Caption and current-prose consistency

The current V5-C05 prose states that the posterior parameter is `α+n`, derives the same marginal evidence, and explicitly warns that the addition is in parameters rather than between probability vectors. The displayed caption repeats precisely that reader conclusion. Figure, caption and surrounding prose therefore agree on objects, assumptions, operation and result.

## R168 readability/harmony adjudication

The source uses explicit 9.4 pt main nodes, 8.5 pt underbrace labels, 8.8 pt side/marginal annotations and a 15 pt multiplication sign; vector extraction shows a common approximately 0.9963 scale. Some legacy numerical thresholds are not met literally, but R168 makes those thresholds advisory. Direct inspection of the native 300 dpi crop, normal page view, grayscale and nearest-neighbor 8× ROIs shows no actual unreadability, missing/tofu/wrong glyph, severe imbalance, clipping, illegal visible-ink overlap or semantic/geometric error. The visual hierarchy is coherent: row labels and structural arrows are stronger than annotations, while the mathematical chain remains the primary focus.
