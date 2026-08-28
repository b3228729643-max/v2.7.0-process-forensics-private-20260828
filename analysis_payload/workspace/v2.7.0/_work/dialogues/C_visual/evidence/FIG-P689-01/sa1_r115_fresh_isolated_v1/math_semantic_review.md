# Manual mathematical and semantic review

## Identity and nonnegativity

The left panel correctly displays

`log p(w) = L(q) + KL(q(h) || p(h|w))`.

This matches the exact current chapter theorem on lines 547-568 under its stated finite-evidence, absolute-continuity, measurability, and integrability conditions. The statement `KL>=0` correctly implies `L(q)<=log p(w)`. The bar segmentation is consistent with the equality: the ELBO segment plus the nonnegative KL gap equals the total evidence length. The note that a restricted variational family can retain a positive gap is consistent with chapter lines 587 and 746-747.

## Coordinate-update progression

The plotted values are `0.12, 0.34, 0.50, 0.64, 0.73, 0.79, 0.80`, hence every displayed step is nondecreasing. The caption uses the qualified wording that mean-field coordinate updates *can* make the ELBO nondecreasing. This is consistent with chapter lines 728-746: each E/M or coordinate block must not decrease the same ELBO on its feasible domain. The figure does not claim that an arbitrary approximate or numerically failed update is monotone.

## Finite-run and global-optimum limits

The endpoint annotation says `坐标稳定／局部驻点`, and the caption says a finite nonconvex run normally yields only a coordinate-stable point or local stationary point. It also explicitly states that multiple starts do not prove global optimality. These limitations agree with chapter lines 747 and 750-756. Neither numerical stabilization nor ELBO-value convergence is presented as parameter uniqueness or global optimality.

## Unknown-limit semantics

The orange horizontal line is labeled `未知全局上限`, not as an attained value and not as the observed log evidence. The y-axis has no numeric scale, so the line is conceptual. For fixed model parameters the finite `log p(w)` is an upper bound on the ELBO; the plot correctly leaves the global optimum/upper level unknown and keeps the finite-run endpoint below it. There is no claim that the shown endpoint reaches or estimates that limit.

## Caption and page consistency

The figure caption, preceding paragraph, source `alt` text, and chapter theorem use the same variables and relations. The caption's three qualifications—ELBO/KL identity, nondecreasing coordinate updates, and no global-optimum proof—are all visible in the two panels. No semantic or mathematical contradiction was found.

Manual verdict: `MATH_SEMANTICS_PASS=true`; `TEXT_CONSISTENCY_PASS=true`.
