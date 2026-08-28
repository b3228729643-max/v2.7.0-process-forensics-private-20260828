# Independent mathematics and semantic audit

The narrow chapter context states

`pi(alpha,theta,z | y) proportional to p(z,y | theta) p(theta | alpha) p(alpha)`.

When updating `theta`, condition on `alpha,z,y`. Any factor that is constant in `theta` is absorbed into the normalizing constant, so

`pi(theta | alpha,z,y) proportional to p(theta | alpha) p(z,y | theta)`.

Therefore the two factor neighbors of `theta` are exactly `p(theta | alpha)` and `p(z,y | theta)`. The variable Markov blanket shown for this update is `alpha,z,y`. The separate factor `p(alpha)` contains no `theta`, so its exclusion from the active conditional kernel is mathematically correct. The source topology, displayed formula, annotations, alt text, and caption all agree with this derivation. There is no missing conditioning variable, reversed dependency, or contradictory geometry. Manual semantic result: PASS.
